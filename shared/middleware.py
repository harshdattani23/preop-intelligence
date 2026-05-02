"""
Middleware — FHIR metadata bridging + (optional) API key authentication.

Two responsibilities, split into two middleware classes so they can be attached
independently:

  - FhirMetadataBridgeMiddleware: always attached. Logs the incoming request
    (headers redacted) and bridges FHIR metadata from params.message.metadata
    up to params.metadata so the ADK before_model_callback can find it
    regardless of where the caller placed it. This is required for every
    A2A caller — Prompt Opinion, raw JSON-RPC clients, and any other A2A
    consumer.

  - ApiKeyMiddleware: only attached when require_api_key=True. Enforces
    X-API-Key header on all non-agent-card requests. The agent-card endpoint
    is intentionally public so callers can discover that auth is required.

In production, load API keys from environment variables or a secrets manager
(e.g. Azure Key Vault, AWS Secrets Manager) rather than hardcoding them here.
"""
import json
import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request  # kept for type hints in dispatch signature
from starlette.responses import JSONResponse

from shared.fhir_hook import extract_fhir_from_payload
from shared.logging_utils import redact_headers, safe_pretty_json, token_fingerprint

logger = logging.getLogger(__name__)

LOG_FULL_PAYLOAD = os.getenv("LOG_FULL_PAYLOAD", "true").lower() == "true"

# Replace / extend with keys loaded from your environment or secrets store.
VALID_API_KEYS: set = {
    "my-secret-key-123",    # your application's key
    "another-valid-key",    # any other trusted callers
}


class FhirMetadataBridgeASGIApp:
    """
    Pure ASGI middleware that bridges FHIR metadata before the request reaches
    the ADK A2A handler. We use raw ASGI rather than Starlette's BaseHTTPMiddleware
    because google.adk.a2a.utils.agent_to_a2a builds its middleware stack at app
    construction time — calling app.add_middleware() afterwards is a silent no-op.
    Wrapping at the ASGI layer guarantees we run before any Starlette plumbing.

    Two responsibilities:
      1. Bridge FHIR metadata from params.message.metadata to params.metadata,
         where the ADK request_converter will surface it on the LLM request.
      2. Log the incoming payload (headers redacted) for debugging.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Drain the request body once so we can inspect (and possibly rewrite) it.
        chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.request":
                chunks.append(message.get("body", b""))
                more_body = message.get("more_body", False)
            else:
                more_body = False
        body_bytes = b"".join(chunks)

        new_body = body_bytes
        if body_bytes:
            try:
                parsed = json.loads(body_bytes.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                parsed = None

            path = scope.get("path", "")
            method = scope.get("method", "")

            if LOG_FULL_PAYLOAD and parsed is not None:
                # Headers come as a list of (bytes, bytes) tuples in scope.
                hdrs = {
                    k.decode("latin-1"): v.decode("latin-1")
                    for k, v in scope.get("headers", [])
                }
                logger.info(
                    "incoming_http_request path=%s method=%s headers=%s\npayload=\n%s",
                    path, method,
                    safe_pretty_json(redact_headers(hdrs)),
                    safe_pretty_json(parsed),
                )

            if isinstance(parsed, dict):
                fhir_key, fhir_data = extract_fhir_from_payload(parsed)
                params = parsed.get("params")
                if isinstance(params, dict):
                    if fhir_key and fhir_data and not params.get("metadata"):
                        params["metadata"] = {fhir_key: fhir_data}
                        new_body = json.dumps(parsed, ensure_ascii=False).encode("utf-8")
                        logger.info(
                            "FHIR_METADATA_BRIDGED source=message.metadata target=params.metadata key=%s",
                            fhir_key,
                        )
                    if fhir_data:
                        logger.info("FHIR_URL_FOUND value=%s",         fhir_data.get("fhirUrl", "[EMPTY]"))
                        logger.info("FHIR_TOKEN_FOUND fingerprint=%s", token_fingerprint(fhir_data.get("fhirToken", "")))
                        logger.info("FHIR_PATIENT_FOUND value=%s",     fhir_data.get("patientId", "[EMPTY]"))
                    else:
                        logger.info("FHIR_NOT_FOUND_IN_PAYLOAD keys_checked=params.metadata,message.metadata")

        # Update Content-Length if we rewrote the body.
        if new_body is not body_bytes:
            new_headers = []
            for k, v in scope.get("headers", []):
                if k.lower() == b"content-length":
                    continue
                new_headers.append((k, v))
            new_headers.append((b"content-length", str(len(new_body)).encode("latin-1")))
            scope = dict(scope)
            scope["headers"] = new_headers

        # Replay the (possibly rewritten) body downstream.
        sent = False

        async def replay_receive():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": new_body, "more_body": False}

        await self.app(scope, replay_receive, send)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Enforce X-API-Key authentication on all non-agent-card requests.
    Only attached when require_api_key=True in app_factory.
    """

    async def dispatch(self, request: Request, call_next):
        # Agent-card endpoint is intentionally public — it tells callers that
        # an API key IS required before they start authenticating.
        if request.url.path == "/.well-known/agent-card.json":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(
                "security_rejected_missing_api_key path=%s method=%s",
                request.url.path, request.method,
            )
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "X-API-Key header is required"},
            )

        if api_key not in VALID_API_KEYS:
            logger.warning(
                "security_rejected_invalid_api_key path=%s method=%s key_prefix=%s",
                request.url.path, request.method, api_key[:6],
            )
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "detail": "Invalid API key"},
            )

        logger.info(
            "security_authorized path=%s method=%s key_prefix=%s",
            request.url.path, request.method, api_key[:6],
        )
        return await call_next(request)
