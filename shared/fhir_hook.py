"""
FHIR context hook — ADK before_model_callback.

When an A2A caller sends FHIR credentials in the message metadata, this hook
extracts them and stores them in session state so that tools can use them at
call time without the credentials ever appearing in the prompt text.

Metadata key convention (must match the AgentExtension URI in app.py):
    "http://<host>/schemas/a2a/v1/fhir-context": {
        "fhirUrl":   "https://fhir.example.org",
        "fhirToken": "<bearer-token>",
        "patientId": "patient-42"
    }

Two transport paths populate `fhir_data_var`:
  1. The ASGI middleware (FhirMetadataBridgeASGIApp) reads the JSON-RPC body,
     extracts FHIR context from params.metadata or params.message.metadata,
     and sets the contextvar BEFORE invoking the inner ADK app.
  2. As a fallback, this callback also walks callback_context / llm_request to
     find metadata if the contextvar isn't set (e.g., for callers that bypass
     the ASGI wrapper).

Set LOG_HOOK_RAW_OBJECTS=true in .env to dump the full llm_request and
callback_context objects to the log (useful when developing a new integration).
"""
import contextvars
import json
import logging
import os

from shared.logging_utils import safe_pretty_json, serialize_for_log, token_fingerprint

logger = logging.getLogger(__name__)

LOG_HOOK_RAW_OBJECTS = os.getenv("LOG_HOOK_RAW_OBJECTS", "false").lower() == "true"

# Must match the AgentExtension URI declared in each agent's app.py.
FHIR_CONTEXT_KEY = "fhir-context"

# Cross-async-boundary transport for FHIR data extracted by the ASGI middleware.
# The middleware writes to this contextvar before dispatching the inner app, and
# extract_fhir_context reads it at the start of every callback invocation.
# contextvars are scoped to the current async task / request, so concurrent
# requests get isolated values automatically.
fhir_data_var: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "fhir_data_var", default=None
)


# ── Private helpers ────────────────────────────────────────────────────────────

def _first_non_empty(*values):
    for v in values:
        if v not in (None, ""):
            return v
    return None


def _safe_correlation_ids(callback_context, llm_request) -> dict:
    return {
        "task_id":    _first_non_empty(getattr(llm_request, "task_id", None),    getattr(callback_context, "task_id", None)),
        "context_id": _first_non_empty(getattr(llm_request, "context_id", None),  getattr(callback_context, "context_id", None)),
        "message_id": _first_non_empty(getattr(llm_request, "message_id", None),  getattr(callback_context, "message_id", None)),
    }


def _coerce_fhir_data(value):
    """Accept either a dict or a JSON string; return a dict or None."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _extract_metadata_sources(callback_context, llm_request) -> list:
    """
    Return candidate metadata dicts in priority order.

    ADK can surface the A2A metadata in several places depending on how the
    request flows through the framework; we check all known locations.
    """
    callback_metadata = getattr(callback_context, "metadata", None)

    run_config      = getattr(callback_context, "run_config", None)
    custom_metadata = getattr(run_config, "custom_metadata", None) if run_config else None
    a2a_metadata    = custom_metadata.get("a2a_metadata") if isinstance(custom_metadata, dict) else None

    llm_payload      = serialize_for_log(llm_request)
    contents         = llm_payload.get("contents", []) if isinstance(llm_payload, dict) else []
    content_metadata = None
    if contents and isinstance(contents, list):
        last = contents[-1]
        if isinstance(last, dict):
            content_metadata = last.get("metadata")

    return [
        ("callback_context.metadata",                                  callback_metadata),
        ("callback_context.run_config.custom_metadata.a2a_metadata",   a2a_metadata),
        ("llm_request.contents[-1].metadata",                          content_metadata),
    ]


# ── Public helper (also used by middleware) ────────────────────────────────────

def extract_fhir_from_payload(payload: dict):
    """
    Extract FHIR context from a raw JSON-RPC payload dict.

    Checks params.metadata first, then params.message.metadata as a fallback.
    Returns (key, fhir_data_dict) or (None, None).
    """
    if not isinstance(payload, dict):
        return None, None
    params = payload.get("params")
    if not isinstance(params, dict):
        return None, None

    for metadata in (params.get("metadata"), (params.get("message") or {}).get("metadata")):
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if FHIR_CONTEXT_KEY in str(key):
                    return key, _coerce_fhir_data(value)

    return None, None


# ── ADK callback ───────────────────────────────────────────────────────────────

def extract_fhir_context(callback_context, llm_request):
    """
    ADK before_model_callback.

    Reads FHIR credentials from the A2A message metadata and writes them into
    callback_context.state so that tools can call the FHIR server.
    Returns None (does not modify the LLM request).
    """
    correlation      = _safe_correlation_ids(callback_context, llm_request)

    # Primary path: the ASGI middleware put the FHIR data into a contextvar
    # before dispatching the inner ADK app. This is the reliable path because
    # ADK does not consistently surface A2A request metadata through
    # callback_context — different ADK versions / request shapes put it in
    # different places, and we cannot rely on any of them.
    ctx_fhir = fhir_data_var.get()
    if isinstance(ctx_fhir, dict) and ctx_fhir:
        callback_context.state["fhir_url"]   = ctx_fhir.get("fhirUrl",   "") or ""
        callback_context.state["fhir_token"] = ctx_fhir.get("fhirToken", "") or ""
        callback_context.state["patient_id"] = ctx_fhir.get("patientId", "") or ""
        print(
            f"[fhir_hook_contextvar] patient_id={callback_context.state['patient_id']} "
            f"fhir_url={callback_context.state['fhir_url']}",
            flush=True,
        )
        return None

    # Fallback path: walk the callback_context / llm_request structures in case
    # the agent is hit by something that bypasses the ASGI wrapper. Kept for
    # backwards compatibility and defense in depth.
    metadata_sources = _extract_metadata_sources(callback_context, llm_request)

    # Walk candidate sources in priority order; use the first non-empty one.
    selected_source = "none"
    metadata        = {}
    for source_name, candidate in metadata_sources:
        if isinstance(candidate, dict) and candidate:
            metadata        = candidate
            selected_source = source_name
            break

    metadata_keys = list(metadata.keys())
    print(
        f"[fhir_hook_fallback] contextvar empty; metadata_source={selected_source} "
        f"metadata_keys={metadata_keys}",
        flush=True,
    )

    if LOG_HOOK_RAW_OBJECTS:
        logger.info("hook_raw_llm_request=\n%s", safe_pretty_json(serialize_for_log(llm_request)))
        logger.info(
            "hook_raw_callback_context=\n%s",
            safe_pretty_json({
                "task_id":    getattr(callback_context, "task_id", None),
                "context_id": getattr(callback_context, "context_id", None),
                "message_id": getattr(callback_context, "message_id", None),
                "metadata":   serialize_for_log(getattr(callback_context, "metadata", None)),
                "state":      serialize_for_log(getattr(callback_context, "state", None)),
            }),
        )

    logger.info(
        "hook_called_enter task_id=%s context_id=%s message_id=%s metadata_source=%s metadata_keys=%s",
        correlation["task_id"], correlation["context_id"], correlation["message_id"],
        selected_source, metadata_keys,
    )

    if not metadata:
        logger.info(
            "hook_called_no_metadata task_id=%s context_id=%s message_id=%s",
            correlation["task_id"], correlation["context_id"], correlation["message_id"],
        )
        return None

    if not isinstance(metadata, dict):
        logger.warning(
            "hook_called_metadata_invalid_shape task_id=%s context_id=%s message_id=%s metadata_type=%s",
            correlation["task_id"], correlation["context_id"], correlation["message_id"],
            type(metadata).__name__,
        )
        return None

    # Find the FHIR entry inside the metadata dict.
    fhir_data = None
    for key, value in metadata.items():
        if FHIR_CONTEXT_KEY in str(key):
            fhir_data = _coerce_fhir_data(value)
            if fhir_data is None:
                logger.warning(
                    "hook_called_fhir_malformed task_id=%s context_id=%s message_id=%s "
                    "metadata_key=%s value_type=%s",
                    correlation["task_id"], correlation["context_id"], correlation["message_id"],
                    key, type(value).__name__,
                )
            break

    if fhir_data:
        callback_context.state["fhir_url"]   = fhir_data.get("fhirUrl",   "")
        callback_context.state["fhir_token"] = fhir_data.get("fhirToken", "")
        callback_context.state["patient_id"] = fhir_data.get("patientId", "")
        logger.info("FHIR_URL_FOUND value=%s",         callback_context.state["fhir_url"]   or "[EMPTY]")
        logger.info("FHIR_TOKEN_FOUND fingerprint=%s", token_fingerprint(callback_context.state["fhir_token"]))
        logger.info("FHIR_PATIENT_FOUND value=%s",     callback_context.state["patient_id"] or "[EMPTY]")
        logger.info(
            "hook_called_fhir_found task_id=%s context_id=%s message_id=%s "
            "patient_id=%s fhir_url_set=%s fhir_token=%s",
            correlation["task_id"], correlation["context_id"], correlation["message_id"],
            callback_context.state["patient_id"],
            bool(callback_context.state["fhir_url"]),
            token_fingerprint(callback_context.state["fhir_token"]),
        )
    else:
        logger.info(
            "hook_called_fhir_not_found task_id=%s context_id=%s message_id=%s metadata_keys=%s",
            correlation["task_id"], correlation["context_id"], correlation["message_id"],
            metadata_keys,
        )

    logger.info(
        "hook_called_exit task_id=%s context_id=%s message_id=%s patient_id=%s",
        correlation["task_id"], correlation["context_id"], correlation["message_id"],
        callback_context.state.get("patient_id", ""),
    )
    return None
