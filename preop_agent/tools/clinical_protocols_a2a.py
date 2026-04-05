"""Clinical protocol A2A tools — antibiotic prophylaxis, blood products,
frailty, patient education, surgical checklist."""

import logging

import httpx
from google.adk.tools import ToolContext

from src.scoring.clinical_protocols import (
    select_antibiotic_prophylaxis,
    anticipate_blood_products,
    assess_frailty,
    generate_patient_education,
    generate_surgical_checklist,
)

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


def select_antibiotic_prophylaxis_a2a(surgery_type: str, tool_context: ToolContext) -> dict:
    """
    Select surgical antibiotic prophylaxis based on surgery type and patient allergies.
    Provides drug, dose, timing, redosing, and penicillin-allergy alternatives.

    Args:
        surgery_type: Type of planned surgery
    """
    c = _ctx(tool_context)
    if isinstance(c, dict): return c
    u, t, pid = c
    try:
        patient = _get(u, t, f"Patient/{pid}")
        allergies = _search(u, t, "AllergyIntolerance", {"patient": pid})
        obs = _search(u, t, "Observation", {"patient": pid, "category": "vital-signs", "_count": "20"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    result = select_antibiotic_prophylaxis(surgery_type, allergies, patient, obs)
    result["status"] = "success"
    return result


def anticipate_blood_products_a2a(surgery_type: str, tool_context: ToolContext) -> dict:
    """
    Predict blood product needs based on surgery type, hemoglobin, coagulation,
    and anticoagulation status. Recommends crossmatch units and transfusion plan.

    Args:
        surgery_type: Type of planned surgery
    """
    c = _ctx(tool_context)
    if isinstance(c, dict): return c
    u, t, pid = c
    try:
        patient = _get(u, t, f"Patient/{pid}")
        conditions = _search(u, t, "Condition", {"patient": pid, "_count": "50"})
        meds = _search(u, t, "MedicationRequest", {"patient": pid, "status": "active", "_count": "50"})
        obs = _search(u, t, "Observation", {"patient": pid, "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    result = anticipate_blood_products(surgery_type, patient, conditions, meds, obs)
    result["status"] = "success"
    return result


def assess_frailty_a2a(tool_context: ToolContext) -> dict:
    """
    Assess patient frailty using modified FRAIL scale. Evaluates fatigue,
    resistance, ambulation, illness burden, and weight loss.
    No arguments required.
    """
    c = _ctx(tool_context)
    if isinstance(c, dict): return c
    u, t, pid = c
    try:
        patient = _get(u, t, f"Patient/{pid}")
        conditions = _search(u, t, "Condition", {"patient": pid, "_count": "50"})
        meds = _search(u, t, "MedicationRequest", {"patient": pid, "status": "active", "_count": "50"})
        obs = _search(u, t, "Observation", {"patient": pid, "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    result = assess_frailty(patient, conditions, meds, obs)
    result["status"] = "success"
    return result


def generate_patient_education_a2a(surgery_type: str, surgery_date: str, tool_context: ToolContext) -> dict:
    """
    Generate plain-language pre-operative instructions for the patient.
    Includes fasting rules, medication changes, what to bring, and allergy reminders.

    Args:
        surgery_type: Type of planned surgery
        surgery_date: Surgery date YYYY-MM-DD
    """
    c = _ctx(tool_context)
    if isinstance(c, dict): return c
    u, t, pid = c
    try:
        patient = _get(u, t, f"Patient/{pid}")
        meds = _search(u, t, "MedicationRequest", {"patient": pid, "status": "active", "_count": "50"})
        allergies = _search(u, t, "AllergyIntolerance", {"patient": pid})
        obs = _search(u, t, "Observation", {"patient": pid, "category": "vital-signs", "_count": "20"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    result = generate_patient_education(surgery_type, surgery_date, patient, meds, allergies, obs)
    result["status"] = "success"
    return result


def generate_surgical_checklist_a2a(surgery_type: str, surgery_date: str, tool_context: ToolContext) -> dict:
    """
    Generate a WHO-style surgical safety checklist populated with patient data.
    Includes Sign In, Time Out, Sign Out phases with safety flags.

    Args:
        surgery_type: Type of planned surgery
        surgery_date: Surgery date YYYY-MM-DD
    """
    c = _ctx(tool_context)
    if isinstance(c, dict): return c
    u, t, pid = c
    try:
        patient = _get(u, t, f"Patient/{pid}")
        conditions = _search(u, t, "Condition", {"patient": pid, "_count": "50"})
        meds = _search(u, t, "MedicationRequest", {"patient": pid, "status": "active", "_count": "50"})
        allergies = _search(u, t, "AllergyIntolerance", {"patient": pid})
        obs = _search(u, t, "Observation", {"patient": pid, "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    result = generate_surgical_checklist(surgery_type, surgery_date, patient, conditions, meds, allergies, obs)
    result["status"] = "success"
    return result
