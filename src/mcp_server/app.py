"""FastMCP application instance — separated to avoid circular imports."""

from fastmcp import FastMCP

mcp = FastMCP(
    name="PreOp Clinical Risk Toolkit",
    instructions=(
        "A suite of perioperative risk assessment tools for pre-operative evaluation. "
        "These tools extract patient data from FHIR, compute validated surgical risk scores, "
        "check medication safety, assess lab readiness, and evaluate anesthesia considerations. "
        "Use get_patient_summary first, then the other tools in parallel."
    ),
)

# Inject ai.promptopinion/fhir-context extension into capabilities
# so the Prompt Opinion platform knows this server supports SHARP-on-MCP.
_original_get_caps = mcp._mcp_server.get_capabilities.__func__


def _patched_get_capabilities(self, notification_options, experimental_capabilities):
    caps = _original_get_caps(self, notification_options, experimental_capabilities)
    if not hasattr(caps, "extensions") or not caps.extensions:
        caps.extensions = {}
    caps.extensions["ai.promptopinion/fhir-context"] = {}
    return caps


import types

mcp._mcp_server.get_capabilities = types.MethodType(_patched_get_capabilities, mcp._mcp_server)
