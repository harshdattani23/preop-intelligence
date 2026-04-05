"""Drug intelligence A2A tools — interactions, renal dosing, allergy cross-reactivity."""

import logging
from datetime import date

import httpx
from google.adk.tools import ToolContext

from src.scoring.drug_intelligence import (
    check_drug_interactions,
    calculate_renal_adjustments,
    check_allergy_cross_reactivity,
)

logger = logging.getLogger(__name__)

FHIR_TIMEOUT = 15


def _get_fhir_context(tool_context):
    fhir_url = tool_context.state.get("fhir_url", "").rstrip("/")
    fhir_token = tool_context.state.get("fhir_token", "")
    patient_id = tool_context.state.get("patient_id", "")
    missing = [n for n, v in [("fhir_url", fhir_url), ("fhir_token", fhir_token), ("patient_id", patient_id)] if not v]
    if missing:
        return {"status": "error", "error_message": f"FHIR context missing: {', '.join(missing)}"}
    return fhir_url, fhir_token, patient_id


def _fhir_get(fhir_url, token, path):
    r = httpx.get(f"{fhir_url}/{path}", headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}, timeout=FHIR_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _fhir_search(fhir_url, token, resource_type, params):
    r = httpx.get(f"{fhir_url}/{resource_type}", params=params, headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}, timeout=FHIR_TIMEOUT)
    r.raise_for_status()
    return [e["resource"] for e in r.json().get("entry", []) if "resource" in e]


def _get_obs_value(observations, loinc_code):
    for obs in observations:
        for c in obs.get("code", {}).get("coding", []):
            if c.get("code") == loinc_code:
                return obs.get("valueQuantity", {}).get("value")
    return None


def _get_age(patient):
    bd = patient.get("birthDate", "")
    if not bd: return 0
    try: bd_date = date.fromisoformat(bd[:10])
    except ValueError: return 0
    today = date.today()
    return today.year - bd_date.year - ((today.month, today.day) < (bd_date.month, bd_date.day))


def check_drug_interactions_a2a(tool_context: ToolContext) -> dict:
    """
    Check all active medications for drug-drug interactions.
    Identifies severe, moderate, and mild interactions with clinical effects
    and recommendations. Covers anticoagulant combos, serotonin syndrome,
    QT prolongation, and perioperative-specific interactions.
    No arguments required.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict): return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_check_drug_interactions patient_id=%s", patient_id)

    try:
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    if not meds:
        return {"status": "success", "message": "No active medications found.", "interactions": []}

    result = check_drug_interactions(meds)
    result["status"] = "success"
    return result


def calculate_renal_dose_adjustments_a2a(tool_context: ToolContext) -> dict:
    """
    Calculate renal dose adjustments for all active medications based on
    estimated GFR (CKD-EPI 2021). Checks metformin, anticoagulants, opioids,
    antibiotics, and other renally-cleared drugs.
    No arguments required.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict): return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_calculate_renal_dose patient_id=%s", patient_id)

    try:
        patient = _fhir_get(fhir_url, token, f"Patient/{patient_id}")
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
        labs = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "category": "laboratory", "_count": "30"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    creatinine = _get_obs_value(labs, "2160-0")
    if creatinine is None:
        return {"status": "error", "error_message": "Creatinine not found. Cannot calculate GFR."}

    result = calculate_renal_adjustments(meds, creatinine, _get_age(patient), patient.get("gender", "unknown"))
    result["status"] = "success"
    return result


def check_allergy_cross_reactivity_a2a(tool_context: ToolContext) -> dict:
    """
    Check patient allergies for cross-reactivity with current medications
    and potential perioperative drugs. Covers penicillin-cephalosporin,
    sulfonamide, opioid, and latex cross-reactivity.
    Provides surgical prophylaxis alternatives.
    No arguments required.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict): return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_check_allergy_cross_reactivity patient_id=%s", patient_id)

    try:
        allergies = _fhir_search(fhir_url, token, "AllergyIntolerance", {"patient": patient_id, "_count": "20"})
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    if not allergies:
        return {"status": "success", "message": "No allergies documented.", "results": []}

    result = check_allergy_cross_reactivity(allergies, meds)
    result["status"] = "success"
    return result
