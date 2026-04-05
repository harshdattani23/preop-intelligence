"""FastMCP application instance — separated to avoid circular imports."""

from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware


class FhirContextExtensionMiddleware(Middleware):
    """Inject ai.promptopinion/fhir-context extension into initialize response."""

    async def on_initialize(self, context, call_next):
        result = await call_next(context)
        if hasattr(result, "capabilities") and result.capabilities:
            if not hasattr(result.capabilities, "extensions") or not result.capabilities.extensions:
                result.capabilities.extensions = {}
            result.capabilities.extensions["ai.promptopinion/fhir-context"] = {}
        return result


mcp = FastMCP(
    name="PreOp Clinical Risk Toolkit",
    instructions=(
        "A suite of perioperative risk assessment tools for pre-operative evaluation. "
        "These tools extract patient data from FHIR, compute validated surgical risk scores, "
        "check medication safety, assess lab readiness, and evaluate anesthesia considerations. "
        "Use get_patient_summary first, then the other tools in parallel."
    ),
    middleware=[FhirContextExtensionMiddleware()],
)
