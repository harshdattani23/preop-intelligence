"""FastMCP application instance — separated to avoid circular imports."""

from fastmcp import FastMCP

mcp = FastMCP(
    name="PreOp Clinical Risk Toolkit",
    instructions=(
        "Perioperative risk assessment toolkit for pre-operative evaluation across all "
        "adult surgeries. Computes 11 validated clinical risk scores cited from primary "
        "literature — ASA, RCRI (Lee TH, Circulation 1999), Caprini VTE, STOP-BANG "
        "(Chung F, Anesthesiology 2008), CHA₂DS₂-VASc, MELD-Na, Wells, HEART, LEMON, GCS, "
        "P-POSSUM — plus medication management with hold-date calculation, drug-drug "
        "interactions, eGFR-based renal dose adjustment, allergy cross-reactivity with "
        "SCIP-aligned antibiotic prophylaxis, lab readiness, anesthesia considerations, "
        "imaging assessment, and multimodal prior-operative-note PDF parsing into 7 "
        "structured finding types. Pairs with the PreOp Intelligence and PostOp Monitor "
        "A2A agents on Prompt Opinion. Aligned with ACS NSQIP, SCIP, and CMS BPCI-Advanced. "
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
