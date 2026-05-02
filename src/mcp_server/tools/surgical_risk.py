"""Tool 2: Compute validated perioperative risk scores (ASA, RCRI, Caprini, STOP-BANG)."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from src.mcp_server.fhir_client import FHIRClient
from src.mcp_server.models import RiskScoreResult, SurgicalRiskAssessment
from src.mcp_server.app import mcp
from src.scoring.citations import cite

# --- SNOMED code sets for condition matching ---

IHD_CODES = {"414545008", "22298006", "413844008", "59021001", "53741008"}
CHF_CODES = {"84114007", "42343007"}
CEREBROVASCULAR_CODES = {"230690007", "266257000"}
DM_CODES = {"44054006", "46635009", "73211009"}
HTN_CODES = {"59621000", "38341003"}
OSA_CODES = {"73430006"}
COPD_CODES = {"13645005"}
CKD_CODES = {"433144002", "46177005", "431855005", "431856006", "433146000"}
DVT_PE_CODES = {"128053003", "59282003", "706870000", "233935004"}
CANCER_CODES = {"363346000", "254637007", "93761005"}
VARICOSE_CODES = {"128060009"}
IBD_CODES = {"24526004", "34000006"}

HIGH_RISK_SURGERY_KEYWORDS = [
    "abdominal", "thoracic", "vascular", "aortic", "bowel", "colectomy",
    "gastrectomy", "hepatectomy", "pneumonectomy", "esophagectomy",
    "whipple", "aaa", "aneurysm", "intraperitoneal", "intrathoracic",
    "suprainguinal", "hernia repair",
]

INSULIN_NAMES = ["insulin glargine", "insulin lispro", "insulin aspart", "insulin detemir", "insulin"]


def _has_condition(conditions: list[dict], code_set: set[str]) -> bool:
    for cond in conditions:
        for coding in cond.get("code", {}).get("coding", []):
            if coding.get("code") in code_set:
                return True
    return False


def _has_medication_name(medications: list[dict], names: list[str]) -> bool:
    for med in medications:
        concept = med.get("medicationCodeableConcept", {})
        med_name = concept.get("text", "").lower()
        for coding in concept.get("coding", []):
            med_name += " " + coding.get("display", "").lower()
        for name in names:
            if name.lower() in med_name:
                return True
    return False


def _is_high_risk_surgery(surgery_type: str) -> bool:
    surgery_lower = surgery_type.lower()
    return any(kw in surgery_lower for kw in HIGH_RISK_SURGERY_KEYWORDS)


def _get_observation_value(observations: list[dict], loinc_code: str) -> float | None:
    for obs in observations:
        for coding in obs.get("code", {}).get("coding", []):
            if coding.get("code") == loinc_code:
                vq = obs.get("valueQuantity", {})
                return vq.get("value")
    return None


def _calculate_age(patient: dict) -> int:
    bd_str = patient.get("birthDate", "")
    if not bd_str:
        return 0
    try:
        bd = date.fromisoformat(bd_str[:10])
    except ValueError:
        return 0
    today = date.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def _get_bmi(observations: list[dict]) -> float | None:
    bmi = _get_observation_value(observations, "39156-5")
    if bmi:
        return bmi
    height_cm = _get_observation_value(observations, "8302-2")
    weight_kg = _get_observation_value(observations, "29463-7")
    if height_cm and weight_kg and height_cm > 0:
        return round(weight_kg / ((height_cm / 100) ** 2), 1)
    return None


def _classify_asa(conditions, medications, observations):
    has_chf = _has_condition(conditions, CHF_CODES)
    has_ihd = _has_condition(conditions, IHD_CODES)
    has_ckd = _has_condition(conditions, CKD_CODES)
    has_copd = _has_condition(conditions, COPD_CODES)
    bmi = _get_bmi(observations)
    creatinine = _get_observation_value(observations, "2160-0")

    severe_conditions = sum([
        has_chf, has_copd,
        bool(creatinine and creatinine > 2.0),
        bool(bmi and bmi >= 40),
    ])
    moderate_conditions = sum([
        _has_condition(conditions, DM_CODES),
        _has_condition(conditions, HTN_CODES),
        bool(bmi and 30 <= bmi < 40),
        has_ihd,
    ])

    if (has_chf and has_ihd) or severe_conditions >= 2:
        return "IV", "Severe systemic disease that is a constant threat to life"
    if severe_conditions >= 1 or (moderate_conditions >= 2 and (has_copd or has_ckd or has_chf)):
        return "III", "Severe systemic disease"
    if moderate_conditions >= 1:
        return "II", "Mild systemic disease"
    return "I", "Normal healthy patient"


def _calculate_rcri(conditions, medications, observations, surgery_type):
    score = 0
    factors = []

    if _is_high_risk_surgery(surgery_type):
        score += 1
        factors.append(f"High-risk surgery ({surgery_type})")
    if _has_condition(conditions, IHD_CODES):
        score += 1
        factors.append("History of ischemic heart disease")
    if _has_condition(conditions, CHF_CODES):
        score += 1
        factors.append("History of congestive heart failure")
    if _has_condition(conditions, CEREBROVASCULAR_CODES):
        score += 1
        factors.append("History of cerebrovascular disease")
    if _has_condition(conditions, DM_CODES) and _has_medication_name(medications, INSULIN_NAMES):
        score += 1
        factors.append("Insulin-dependent diabetes mellitus")

    creatinine = _get_observation_value(observations, "2160-0")
    if creatinine and creatinine > 2.0:
        score += 1
        factors.append(f"Serum creatinine >2.0 mg/dL (value: {creatinine})")

    risk_map = {0: ("low", "3.9%"), 1: ("low", "6.0%"), 2: ("intermediate", "10.1%")}
    risk_level, risk_pct = risk_map.get(score, ("high", ">15%"))

    recommendations = []
    if score >= 2:
        recommendations.append("Consider cardiology consultation for perioperative risk optimization")
    if score >= 3:
        recommendations.append("Consider non-invasive cardiac testing if it will change management")
        recommendations.append("Ensure beta-blocker therapy is optimized")

    return RiskScoreResult(
        score_name="Revised Cardiac Risk Index (RCRI / Lee Index)",
        score_value=score, risk_level=risk_level,
        risk_percentage=f"Estimated major cardiac event risk: {risk_pct}",
        contributing_factors=factors, recommendations=recommendations,
        citation=cite("RCRI"),
    )


def _calculate_caprini(patient, conditions, medications, observations, surgery_type):
    score = 0
    factors = []
    age = _calculate_age(patient)

    if 41 <= age <= 60:
        score += 1; factors.append(f"Age {age} (41-60: +1)")
    elif 61 <= age <= 74:
        score += 2; factors.append(f"Age {age} (61-74: +2)")
    elif age >= 75:
        score += 3; factors.append(f"Age {age} (>=75: +3)")

    surgery_lower = surgery_type.lower()
    if any(kw in surgery_lower for kw in ["arthroscopy", "minor", "laparoscopic"]):
        score += 1; factors.append("Minor surgery (+1)")
    elif any(kw in surgery_lower for kw in ["abdominal", "hernia", "cholecystectomy"]):
        score += 2; factors.append("Major surgery (>45 min) (+2)")
    elif any(kw in surgery_lower for kw in ["aortic", "aneurysm", "vascular", "hip", "knee replacement"]):
        score += 5; factors.append("Major vascular/orthopedic surgery (+5)")

    bmi = _get_bmi(observations)
    if bmi and bmi > 25:
        score += 1; factors.append(f"BMI {bmi} >25 (+1)")
    if _has_condition(conditions, CHF_CODES):
        score += 1; factors.append("Congestive heart failure (+1)")
    if _has_condition(conditions, COPD_CODES):
        score += 1; factors.append("COPD (+1)")
    if _has_condition(conditions, DVT_PE_CODES):
        score += 3; factors.append("History of DVT/PE (+3)")
    if _has_condition(conditions, CANCER_CODES):
        score += 2; factors.append("Active cancer (+2)")
    if _has_condition(conditions, VARICOSE_CODES):
        score += 1; factors.append("Varicose veins (+1)")
    if _has_condition(conditions, IBD_CODES):
        score += 1; factors.append("Inflammatory bowel disease (+1)")

    if score <= 1:
        risk_level, recs = "low", ["Early ambulation"]
    elif score == 2:
        risk_level, recs = "moderate", ["Consider intermittent pneumatic compression (IPC)"]
    elif score <= 4:
        risk_level, recs = "high", ["Pharmacologic prophylaxis (LMWH or UFH) + IPC recommended"]
    else:
        risk_level = "very_high"
        recs = ["Pharmacologic prophylaxis (LMWH or UFH) + IPC strongly recommended",
                "Consider extended prophylaxis (up to 30 days post-op)"]

    return RiskScoreResult(
        score_name="Caprini VTE Risk Score", score_value=score,
        risk_level=risk_level, contributing_factors=factors, recommendations=recs,
        citation=cite("Caprini"),
    )


def _calculate_stop_bang(patient, conditions, observations):
    score = 0
    factors = []
    age = _calculate_age(patient)
    gender = patient.get("gender", "").lower()
    bmi = _get_bmi(observations)

    has_osa = _has_condition(conditions, OSA_CODES)
    if has_osa:
        score += 1; factors.append("Snoring (OSA diagnosed)")
        score += 1; factors.append("Excessive daytime sleepiness (OSA diagnosed)")
        score += 1; factors.append("Observed apnea (OSA diagnosed)")
    if _has_condition(conditions, HTN_CODES):
        score += 1; factors.append("Treated hypertension")
    if bmi and bmi > 35:
        score += 1; factors.append(f"BMI {bmi} >35")
    if age > 50:
        score += 1; factors.append(f"Age {age} >50")
    neck = _get_observation_value(observations, "56072-2")
    if neck and neck > 40:
        score += 1; factors.append(f"Neck circumference {neck}cm >40cm")
    if gender == "male":
        score += 1; factors.append("Male gender")

    if score <= 2:
        risk_level, recs = "low", ["Low risk for OSA — no additional precautions needed"]
    elif score <= 4:
        risk_level = "intermediate"
        recs = ["Intermediate risk for OSA", "Consider formal sleep study if not previously evaluated",
                "Inform anesthesia team for airway planning"]
    else:
        risk_level = "high"
        recs = ["High risk for OSA — anticipate difficult airway management",
                "Ensure CPAP device is available post-operatively",
                "Consider monitored bed post-op (step-down unit)",
                "Minimize opioid use — consider multimodal analgesia"]

    return RiskScoreResult(
        score_name="STOP-BANG OSA Screening", score_value=score,
        risk_level=risk_level, contributing_factors=factors, recommendations=recs,
        citation=cite("STOP-BANG"),
    )


@mcp.tool(
    name="calculate_surgical_risk",
    description=(
        "Compute validated perioperative risk scores: ASA Physical Status Classification, "
        "RCRI (Revised Cardiac Risk Index / Lee Index), Caprini VTE Risk Score, and "
        "STOP-BANG OSA screening score. Patient ID is optional if FHIR context is available."
    ),
)
async def calculate_surgical_risk(
    surgery_type: Annotated[str, "Type of planned surgery, e.g. 'laparoscopic cholecystectomy', 'AAA repair'"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if patient context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id

    if not patient_id:
        return "Error: No patient ID provided and no FHIR context available."

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    observations = await client.get_observations(patient_id)

    asa_class, asa_desc = _classify_asa(conditions, medications, observations)
    rcri = _calculate_rcri(conditions, medications, observations, surgery_type)
    caprini = _calculate_caprini(patient, conditions, medications, observations, surgery_type)
    stop_bang = _calculate_stop_bang(patient, conditions, observations)

    assessment = SurgicalRiskAssessment(
        asa_class=asa_class, asa_description=asa_desc,
        asa_citation=cite("ASA"),
        rcri=rcri, caprini_vte=caprini, stop_bang=stop_bang,
    )
    return assessment.model_dump_json(indent=2)
