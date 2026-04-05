"""Pre-operative imaging assessment A2A tool."""

import logging

import httpx
from google.adk.tools import ToolContext

from src.scoring.imaging_assessment import assess_preop_imaging

logger = logging.getLogger(__name__)
FHIR_TIMEOUT = 15


def _ctx(tc):
    u = tc.state.get("fhir_url", "").rstrip("/")
    t = tc.state.get("fhir_token", "")
    p = tc.state.get("patient_id", "")
    missing = [n for n, v in [("fhir_url", u), ("fhir_token", t), ("patient_id", p)] if not v]
    if missing:
        return {"status": "error", "error_message": f"FHIR context missing: {', '.join(missing)}"}
    return u, t, p


def _get(url, token, path):
    r = httpx.get(f"{url}/{path}", headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}, timeout=FHIR_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _search(url, token, rt, params):
    r = httpx.get(f"{url}/{rt}", params=params, headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}, timeout=FHIR_TIMEOUT)
    r.raise_for_status()
    return [e["resource"] for e in r.json().get("entry", []) if "resource" in e]


def assess_preop_imaging_a2a(surgery_type: str, surgery_date: str, tool_context: ToolContext) -> dict:
    """
    Assess pre-operative imaging requirements. Determines required imaging
    (CXR, ECG, echo, CT angiogram) based on surgery type and conditions.
    Checks availability, flags missing/expired studies, and parses report findings.

    Args:
        surgery_type: Type of planned surgery
        surgery_date: Surgery date YYYY-MM-DD
    """
    c = _ctx(tool_context)
    if isinstance(c, dict):
        return c
    u, t, pid = c
    logger.info("tool_assess_preop_imaging patient_id=%s surgery=%s", pid, surgery_type)

    try:
        patient = _get(u, t, f"Patient/{pid}")
        conditions = _search(u, t, "Condition", {"patient": pid, "_count": "50"})
        reports = _search(u, t, "DiagnosticReport", {"patient": pid, "_count": "50"})
        imaging = _search(u, t, "ImagingStudy", {"patient": pid, "_count": "20"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    result = assess_preop_imaging(surgery_type, surgery_date, patient, conditions, reports, imaging)
    result["status"] = "success"
    return result
