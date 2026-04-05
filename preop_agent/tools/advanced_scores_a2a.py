"""Advanced clinical scoring systems as A2A tools (Google ADK)."""

import logging

import httpx
from google.adk.tools import ToolContext

from src.scoring.calculators import (
    _calc_cha2ds2vasc,
    _calc_meld,
    _calc_wells_dvt,
    _calc_heart,
    _calc_lemon_airway,
    _calc_gcs,
    _calc_p_possum,
)

logger = logging.getLogger(__name__)

FHIR_TIMEOUT = 15


def _get_fhir_context(tool_context: ToolContext):
    fhir_url = tool_context.state.get("fhir_url", "").rstrip("/")
    fhir_token = tool_context.state.get("fhir_token", "")
    patient_id = tool_context.state.get("patient_id", "")
    missing = [n for n, v in [("fhir_url", fhir_url), ("fhir_token", fhir_token), ("patient_id", patient_id)] if not v]
    if missing:
        return {"status": "error", "error_message": f"FHIR context missing: {', '.join(missing)}"}
    return fhir_url, fhir_token, patient_id


def _fhir_search(fhir_url, token, resource_type, params):
    response = httpx.get(
        f"{fhir_url}/{resource_type}", params=params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"},
        timeout=FHIR_TIMEOUT,
    )
    response.raise_for_status()
    return [e["resource"] for e in response.json().get("entry", []) if "resource" in e]


def _fhir_get(fhir_url, token, path):
    response = httpx.get(
        f"{fhir_url}/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"},
        timeout=FHIR_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def calculate_advanced_risk_scores(
    surgery_type: str,
    scores: str = "cha2ds2vasc,meld,wells,heart,lemon,gcs,possum",
    tool_context: ToolContext = None,
) -> dict:
    """
    Calculate advanced perioperative risk scores beyond ASA/RCRI.
    Available scores: CHA₂DS₂-VASc (stroke risk), MELD-Na (liver),
    Wells (DVT), HEART (chest pain), LEMON (airway), GCS (neuro),
    P-POSSUM (surgical mortality).

    Args:
        surgery_type: Type of planned surgery
        scores: Comma-separated list of scores. Options: cha2ds2vasc, meld, wells, heart, lemon, gcs, possum. Default: all.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_calculate_advanced_risk_scores patient_id=%s surgery=%s", patient_id, surgery_type)

    try:
        patient = _fhir_get(fhir_url, token, f"Patient/{patient_id}")
        conditions = _fhir_search(fhir_url, token, "Condition", {"patient": patient_id, "_count": "50"})
        observations = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    requested = set(scores.lower().replace(" ", "").split(","))

    results = {"status": "success"}
    if "cha2ds2vasc" in requested:
        results["cha2ds2vasc"] = _calc_cha2ds2vasc(patient, conditions, observations)
    if "meld" in requested:
        results["meld"] = _calc_meld(observations)
    if "wells" in requested:
        results["wells_dvt"] = _calc_wells_dvt(patient, conditions, observations)
    if "heart" in requested:
        results["heart"] = _calc_heart(patient, conditions, observations)
    if "lemon" in requested:
        results["lemon_airway"] = _calc_lemon_airway(patient, conditions, observations)
    if "gcs" in requested:
        results["gcs"] = _calc_gcs(observations)
    if "possum" in requested:
        results["p_possum"] = _calc_p_possum(patient, conditions, observations, surgery_type)

    return results
