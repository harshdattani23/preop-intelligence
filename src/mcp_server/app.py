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
