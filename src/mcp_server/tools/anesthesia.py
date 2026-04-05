"""Tool 5: Assess anesthesia considerations — airway risk, NPO guidance, prior complications."""

from __future__ import annotations

from typing import Annotated

from src.mcp_server.fhir_client import FHIRClient
from src.mcp_server.models import AnesthesiaAssessment
from src.mcp_server.app import mcp

OSA_CODES = {"73430006"}
MALIGNANT_HYPERTHERMIA_CODES = {"405501007"}
COPD_CODES = {"13645005"}
CHF_CODES = {"84114007", "42343007"}
OBESITY_CODES = {"414916001", "238136002"}  # Obesity, morbid obesity

# Medications that affect anesthesia
GLP1_NAMES = ["semaglutide", "liraglutide", "dulaglutide", "tirzepatide", "exenatide"]
ANTICOAG_NAMES = ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "enoxaparin"]


def _has_condition(conditions: list[dict], code_set: set[str]) -> bool:
    for cond in conditions:
        for coding in cond.get("code", {}).get("coding", []):
            if coding.get("code") in code_set:
                return True
    return False


def _has_medication(medications: list[dict], names: list[str]) -> bool:
    for med in medications:
        concept = med.get("medicationCodeableConcept", {})
        med_name = concept.get("text", "").lower()
        for coding in concept.get("coding", []):
            med_name += " " + coding.get("display", "").lower()
        for name in names:
            if name.lower() in med_name:
                return True
    return False


def _get_obs_value(observations: list[dict], loinc_code: str) -> float | None:
    for obs in observations:
        for coding in obs.get("code", {}).get("coding", []):
            if coding.get("code") == loinc_code:
                return obs.get("valueQuantity", {}).get("value")
    return None


def _get_allergy_substances(allergies: list[dict]) -> list[str]:
    substances = []
    for allergy in allergies:
        codings = allergy.get("code", {}).get("coding", [])
        if codings:
            substances.append(codings[0].get("display", "Unknown"))
        elif allergy.get("code", {}).get("text"):
            substances.append(allergy["code"]["text"])
    return substances


@mcp.tool(
    name="get_anesthesia_considerations",
    description=(
        "Assess airway risk factors (BMI, neck circumference, OSA), "
        "provide NPO (fasting) guidance, review prior anesthesia complications, "
        "and generate anesthesia-specific recommendations."
    ),
)
async def get_anesthesia_considerations(
    patient_id: Annotated[str, "FHIR Patient ID"],
    surgery_date: Annotated[str, "Planned surgery date YYYY-MM-DD"] = "",
    anesthesia_type: Annotated[str, "Planned anesthesia: 'general', 'regional', 'MAC'"] = "general",
    fhir_base_url: Annotated[str, "FHIR R4 server base URL"] = "https://hapi.fhir.org/baseR4",
    fhir_token: Annotated[str | None, "FHIR bearer token from SHARP context"] = None,
) -> str:
    """Assess anesthesia considerations for pre-operative planning."""
    client = FHIRClient(base_url=fhir_base_url, fhir_token=fhir_token)

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    observations = await client.get_observations(patient_id)
    allergies = await client.get_allergies(patient_id)
    procedures = await client.get_procedures(patient_id)

    # --- Airway Risk Assessment ---
    airway_factors = []
    bmi = _get_obs_value(observations, "39156-5")
    if bmi is None:
        height = _get_obs_value(observations, "8302-2")
        weight = _get_obs_value(observations, "29463-7")
        if height and weight and height > 0:
            bmi = round(weight / ((height / 100) ** 2), 1)

    if bmi:
        if bmi >= 40:
            airway_factors.append(f"Morbid obesity (BMI {bmi}) — anticipate difficult mask ventilation and intubation")
        elif bmi >= 35:
            airway_factors.append(f"Severe obesity (BMI {bmi}) — increased airway difficulty")
        elif bmi >= 30:
            airway_factors.append(f"Obesity (BMI {bmi}) — moderate airway risk")

    neck_circ = _get_obs_value(observations, "56072-2")
    if neck_circ and neck_circ > 40:
        airway_factors.append(f"Large neck circumference ({neck_circ}cm >40cm) — difficult intubation risk")

    has_osa = _has_condition(conditions, OSA_CODES)
    if has_osa:
        airway_factors.append("Obstructive sleep apnea — anticipate difficult airway, ensure CPAP available post-op")

    has_copd = _has_condition(conditions, COPD_CODES)
    if has_copd:
        airway_factors.append("COPD — risk of bronchospasm, consider bronchodilator pre-treatment")

    # Mallampati note
    airway_factors.append("Mallampati score: requires bedside assessment (not available in EHR data)")

    # Determine overall airway risk
    if any("morbid" in f.lower() or ("neck" in f.lower() and "large" in f.lower()) for f in airway_factors):
        airway_risk = "high"
    elif any("obesity" in f.lower() or "sleep apnea" in f.lower() for f in airway_factors):
        airway_risk = "moderate"
    else:
        airway_risk = "low"

    # --- BMI Category ---
    if bmi:
        if bmi >= 40:
            bmi_category = f"morbid_obesity (BMI {bmi})"
        elif bmi >= 35:
            bmi_category = f"severe_obesity (BMI {bmi})"
        elif bmi >= 30:
            bmi_category = f"obese (BMI {bmi})"
        elif bmi >= 25:
            bmi_category = f"overweight (BMI {bmi})"
        else:
            bmi_category = f"normal (BMI {bmi})"
    else:
        bmi_category = "unknown"

    # --- NPO Guidance ---
    on_glp1 = _has_medication(medications, GLP1_NAMES)
    npo_lines = [
        "Clear liquids: stop 2 hours before surgery",
        "Light meal / non-human milk: stop 6 hours before surgery",
        "Full meal / fatty foods: stop 8 hours before surgery",
    ]
    if on_glp1:
        npo_lines.append(
            "ALERT: Patient on GLP-1 agonist — increased aspiration risk. "
            "Consider holding weekly GLP-1 for 1 week pre-op. "
            "Consider point-of-care gastric ultrasound to assess residual volume."
        )
    npo_guidance = "\n".join(npo_lines)

    # --- Prior Anesthesia Complications ---
    prior_complications = []
    if _has_condition(conditions, MALIGNANT_HYPERTHERMIA_CODES):
        prior_complications.append("HISTORY OF MALIGNANT HYPERTHERMIA — avoid succinylcholine and volatile agents")

    # Check for prior anesthesia-related procedures
    for proc in procedures:
        for coding in proc.get("code", {}).get("coding", []):
            display = coding.get("display", "").lower()
            if "difficult intubation" in display or "failed intubation" in display:
                prior_complications.append(f"Prior difficult/failed intubation ({proc.get('performedDateTime', 'date unknown')})")

    # --- Allergy Considerations ---
    allergy_substances = _get_allergy_substances(allergies)

    # --- Recommendations ---
    recommendations = []

    if airway_risk == "high":
        recommendations.append("Have difficult airway equipment readily available (video laryngoscope, fiberoptic scope)")
        recommendations.append("Consider awake fiberoptic intubation if multiple high-risk airway factors present")

    if has_osa:
        recommendations.append("Ensure CPAP device is available for post-operative recovery")
        recommendations.append("Consider monitored bed (step-down unit) post-operatively")
        recommendations.append("Minimize opioid use — prefer multimodal analgesia (regional blocks, acetaminophen, NSAIDs)")

    if has_copd:
        recommendations.append("Optimize bronchodilator therapy pre-operatively")
        recommendations.append("Consider regional anesthesia if feasible to avoid intubation")

    if _has_condition(conditions, CHF_CODES):
        recommendations.append("Monitor fluid balance carefully — avoid fluid overload")
        recommendations.append("Consider arterial line for hemodynamic monitoring")

    if _has_medication(medications, ANTICOAG_NAMES) and anesthesia_type == "regional":
        recommendations.append("ALERT: Patient on anticoagulation — verify adequate hold time before neuraxial anesthesia")
        recommendations.append("Follow ASRA guidelines for neuraxial anticoagulation timing")

    if allergy_substances:
        recommendations.append(f"Drug allergies documented: {', '.join(allergy_substances)}")
        if any("penicillin" in s.lower() for s in allergy_substances):
            recommendations.append("Penicillin allergy — use alternative antibiotic prophylaxis (e.g., clindamycin or vancomycin)")

    if on_glp1:
        recommendations.append("GLP-1 agonist — elevated aspiration risk, may need rapid sequence induction")

    if not recommendations:
        recommendations.append("No specific anesthesia concerns identified — standard monitoring appropriate")

    assessment = AnesthesiaAssessment(
        airway_risk=airway_risk,
        airway_factors=airway_factors,
        bmi_category=bmi_category,
        npo_guidance=npo_guidance,
        prior_anesthesia_complications=prior_complications,
        recommendations=recommendations,
    )
    return assessment.model_dump_json(indent=2)
