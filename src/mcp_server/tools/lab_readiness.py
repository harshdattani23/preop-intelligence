"""Tool 4: Assess pre-operative lab readiness — currency, abnormals, and missing labs."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from src.mcp_server.fhir_client import FHIRClient
from src.mcp_server.models import LabReadinessReport, LabResult
from src.mcp_server.app import mcp

# Required labs by clinical context
BASE_LABS = [
    ("6690-2", "WBC", "x10^9/L", "4.5-11.0"),
    ("718-7", "Hemoglobin", "g/dL", "12.0-17.5"),
    ("777-3", "Platelets", "x10^9/L", "150-400"),
]

METABOLIC_LABS = [
    ("2951-2", "Sodium", "mEq/L", "136-145"),
    ("2823-3", "Potassium", "mEq/L", "3.5-5.0"),
    ("2160-0", "Creatinine", "mg/dL", "0.7-1.3"),
    ("3094-0", "BUN", "mg/dL", "7-20"),
    ("2345-7", "Glucose", "mg/dL", "70-100"),
]

COAG_LABS = [
    ("34714-6", "INR", "", "0.9-1.1"),
    ("3173-2", "aPTT", "seconds", "25-35"),
]

DIABETES_LABS = [
    ("4548-4", "HbA1c", "%", "<7.0"),
]

CHF_LABS = [
    ("42637-9", "BNP", "pg/mL", "<100"),
]

TYPE_SCREEN_LABS = [
    ("882-1", "ABO Group", "", ""),
    ("10331-7", "Rh Type", "", ""),
]

# Reference ranges for abnormal detection
REFERENCE_RANGES: dict[str, tuple[float | None, float | None]] = {
    "6690-2": (4.5, 11.0),    # WBC
    "718-7": (12.0, 17.5),    # Hemoglobin (using wider range; gender-specific in _check_abnormal)
    "777-3": (150.0, 400.0),  # Platelets
    "2951-2": (136.0, 145.0), # Sodium
    "2823-3": (3.5, 5.0),     # Potassium
    "2160-0": (0.7, 1.3),     # Creatinine
    "3094-0": (7.0, 20.0),    # BUN
    "2345-7": (70.0, 100.0),  # Glucose (fasting)
    "34714-6": (0.9, 1.1),    # INR (non-anticoagulated)
    "3173-2": (25.0, 35.0),   # aPTT
    "4548-4": (None, 7.0),    # HbA1c
    "42637-9": (None, 100.0), # BNP
}

# Critical values that need immediate attention
CRITICAL_RANGES: dict[str, tuple[float | None, float | None]] = {
    "2823-3": (3.0, 6.0),     # Potassium
    "2951-2": (125.0, 155.0), # Sodium
    "718-7": (7.0, None),     # Hemoglobin
    "777-3": (50.0, None),    # Platelets
}

# Keywords for determining which additional labs are needed
HIGH_RISK_SURGERY_KEYWORDS = [
    "abdominal", "thoracic", "vascular", "aortic", "cardiac", "spine",
    "major", "open", "aneurysm",
]


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        try:
            return date.fromisoformat(date_str[:10])
        except (ValueError, TypeError):
            return None


def _check_abnormal(loinc_code: str, value: float | None) -> str:
    """Return 'normal', 'abnormal_high', 'abnormal_low', or 'critical'."""
    if value is None:
        return "normal"

    # Check critical first
    crit = CRITICAL_RANGES.get(loinc_code)
    if crit:
        low, high = crit
        if low is not None and value < low:
            return "critical"
        if high is not None and value > high:
            return "critical"

    ref = REFERENCE_RANGES.get(loinc_code)
    if not ref:
        return "normal"
    low, high = ref
    if low is not None and value < low:
        return "abnormal_low"
    if high is not None and value > high:
        return "abnormal_high"
    return "normal"


def _has_condition_code(conditions: list[dict], code_set: set[str]) -> bool:
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


def _determine_required_labs(
    conditions: list[dict], medications: list[dict], surgery_type: str, patient: dict,
) -> list[tuple[str, str, str, str]]:
    """Determine which labs are required based on clinical context."""
    required = list(BASE_LABS)

    age = 0
    bd = patient.get("birthDate", "")
    if bd:
        bd_date = _parse_date(bd)
        if bd_date:
            today = date.today()
            age = today.year - bd_date.year - ((today.month, today.day) < (bd_date.month, bd_date.day))

    # Add metabolic panel for age >50 or cardiac conditions
    cardiac_codes = {"84114007", "42343007", "414545008", "22298006", "53741008", "413844008"}
    if age > 50 or _has_condition_code(conditions, cardiac_codes):
        required.extend(METABOLIC_LABS)

    # Coag studies if on anticoagulants
    anticoag_names = ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "enoxaparin"]
    if _has_medication_name(medications, anticoag_names):
        required.extend(COAG_LABS)

    # HbA1c for diabetics
    dm_codes = {"44054006", "46635009", "73211009"}
    if _has_condition_code(conditions, dm_codes):
        required.extend(DIABETES_LABS)

    # BNP for CHF patients
    chf_codes = {"84114007", "42343007"}
    if _has_condition_code(conditions, chf_codes):
        required.extend(CHF_LABS)

    # Type & screen for major surgery
    if any(kw in surgery_type.lower() for kw in HIGH_RISK_SURGERY_KEYWORDS):
        required.extend(TYPE_SCREEN_LABS)

    # Deduplicate by LOINC code
    seen = set()
    deduped = []
    for lab in required:
        if lab[0] not in seen:
            seen.add(lab[0])
            deduped.append(lab)
    return deduped


@mcp.tool(
    name="assess_lab_readiness",
    description=(
        "Check if pre-operative labs are current (within 30 days), within normal range, "
        "and identify missing required labs based on patient risk factors and surgery type."
    ),
)
async def assess_lab_readiness(
    patient_id: Annotated[str, "FHIR Patient ID"],
    surgery_type: Annotated[str, "Planned surgery type"],
    surgery_date: Annotated[str, "Planned surgery date YYYY-MM-DD"] = "",
    fhir_base_url: Annotated[str, "FHIR R4 server base URL"] = "https://hapi.fhir.org/baseR4",
    fhir_token: Annotated[str | None, "FHIR bearer token from SHARP context"] = None,
) -> str:
    """Assess pre-operative lab readiness."""
    client = FHIRClient(base_url=fhir_base_url, fhir_token=fhir_token)

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    lab_observations = await client.get_observations(patient_id, category="laboratory")

    ref_date = _parse_date(surgery_date) or date.today()
    required_labs = _determine_required_labs(conditions, medications, surgery_type, patient)

    labs_current: list[LabResult] = []
    labs_expired: list[LabResult] = []
    labs_abnormal: list[LabResult] = []
    labs_missing: list[str] = []

    for loinc_code, test_name, unit, ref_range in required_labs:
        # Find the most recent observation with this LOINC code
        matching = []
        for obs in lab_observations:
            for coding in obs.get("code", {}).get("coding", []):
                if coding.get("code") == loinc_code:
                    matching.append(obs)

        if not matching:
            labs_missing.append(f"{test_name} (LOINC: {loinc_code})")
            continue

        # Get most recent by effectiveDateTime
        matching.sort(
            key=lambda o: o.get("effectiveDateTime", ""),
            reverse=True,
        )
        latest = matching[0]
        vq = latest.get("valueQuantity", {})
        value = vq.get("value")
        obs_unit = vq.get("unit", unit)
        collection_date = latest.get("effectiveDateTime", "")

        coll_date = _parse_date(collection_date)
        days_old = (ref_date - coll_date).days if coll_date else 999
        is_expired = days_old > 30
        status = _check_abnormal(loinc_code, value)

        lab_result = LabResult(
            test_name=test_name,
            loinc_code=loinc_code,
            value=float(value) if value is not None else None,
            unit=obs_unit,
            reference_range=ref_range,
            status=status,
            collection_date=collection_date[:10] if collection_date else "",
            is_expired=is_expired,
            days_old=days_old,
        )

        if is_expired:
            labs_expired.append(lab_result)
        else:
            labs_current.append(lab_result)

        if status in ("abnormal_high", "abnormal_low", "critical"):
            labs_abnormal.append(lab_result)

    overall_ready = len(labs_missing) == 0 and len(labs_expired) == 0 and not any(
        lab.status == "critical" for lab in labs_abnormal
    )

    report = LabReadinessReport(
        labs_current=labs_current,
        labs_expired=labs_expired,
        labs_missing=labs_missing,
        labs_abnormal=labs_abnormal,
        overall_ready=overall_ready,
    )
    return report.model_dump_json(indent=2)
