"""Tool 1: Extract comprehensive patient summary from FHIR data."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from src.mcp_server.fhir_client import FHIRClient
from src.mcp_server.models import (
    AllergyInfo,
    ConditionInfo,
    MedicationInfo,
    PatientSummary,
    ProcedureInfo,
    VitalSign,
)
from src.mcp_server.app import mcp


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


def _calculate_age(birth_date_str: str) -> int:
    bd = _parse_date(birth_date_str)
    if not bd:
        return 0
    today = date.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def _extract_name(patient: dict) -> str:
    names = patient.get("name", [])
    if not names:
        return "Unknown"
    name = names[0]
    given = " ".join(name.get("given", []))
    family = name.get("family", "")
    return f"{given} {family}".strip() or "Unknown"


def _extract_coding(resource: dict, field: str = "code") -> tuple[str, str, str]:
    concept = resource.get(field, {})
    codings = concept.get("coding", [])
    if codings:
        c = codings[0]
        return c.get("code", ""), c.get("display", concept.get("text", "")), c.get("system", "")
    return "", concept.get("text", ""), ""


def _extract_conditions(conditions: list[dict]) -> list[ConditionInfo]:
    result = []
    for cond in conditions:
        code, display, system = _extract_coding(cond)
        clinical_status = "active"
        cs = cond.get("clinicalStatus", {})
        cs_codings = cs.get("coding", [])
        if cs_codings:
            clinical_status = cs_codings[0].get("code", "active")
        onset = cond.get("onsetDateTime", None)
        result.append(ConditionInfo(
            code=code, display=display, system=system,
            clinical_status=clinical_status, onset_date=onset,
        ))
    return result


def _extract_medications(meds: list[dict]) -> list[MedicationInfo]:
    result = []
    for med in meds:
        concept = med.get("medicationCodeableConcept", {})
        codings = concept.get("coding", [])
        code = codings[0].get("code", "") if codings else ""
        display = codings[0].get("display", concept.get("text", "")) if codings else concept.get("text", "")
        system = codings[0].get("system", "") if codings else ""

        dosage_text = ""
        frequency = ""
        dosage_instructions = med.get("dosageInstruction", [])
        if dosage_instructions:
            dosage_text = dosage_instructions[0].get("text", "")
            timing = dosage_instructions[0].get("timing", {})
            repeat = timing.get("repeat", {})
            if repeat:
                freq = repeat.get("frequency", "")
                period = repeat.get("period", "")
                period_unit = repeat.get("periodUnit", "")
                if freq and period:
                    frequency = f"{freq}x per {period} {period_unit}"

        result.append(MedicationInfo(
            code=code, display=display, system=system,
            dosage=dosage_text or None, frequency=frequency or None,
            status=med.get("status", "active"),
        ))
    return result


def _extract_allergies(allergies: list[dict]) -> list[AllergyInfo]:
    result = []
    for allergy in allergies:
        code, display, _ = _extract_coding(allergy)
        substance = display or code

        reaction_text = None
        severity = None
        reactions = allergy.get("reaction", [])
        if reactions:
            manifestations = reactions[0].get("manifestation", [])
            if manifestations:
                _, reaction_text, _ = _extract_coding(manifestations[0], "")
                if not reaction_text:
                    man_codings = manifestations[0].get("coding", [])
                    if man_codings:
                        reaction_text = man_codings[0].get("display", "")
            severity = reactions[0].get("severity")

        result.append(AllergyInfo(
            substance=substance,
            reaction=reaction_text,
            severity=severity,
            criticality=allergy.get("criticality"),
        ))
    return result


def _extract_procedures(procedures: list[dict]) -> list[ProcedureInfo]:
    result = []
    for proc in procedures:
        code, display, _ = _extract_coding(proc)
        performed = proc.get("performedDateTime", proc.get("performedPeriod", {}).get("start"))
        result.append(ProcedureInfo(
            code=code, display=display,
            date=performed, status=proc.get("status", "completed"),
        ))
    return result


def _extract_vitals(observations: list[dict]) -> dict[str, VitalSign]:
    vitals: dict[str, VitalSign] = {}
    for obs in observations:
        code, display, _ = _extract_coding(obs)
        vq = obs.get("valueQuantity", {})
        value = vq.get("value")
        if value is None:
            components = obs.get("component", [])
            for comp in components:
                comp_code, comp_display, _ = _extract_coding(comp)
                comp_vq = comp.get("valueQuantity", {})
                comp_value = comp_vq.get("value")
                if comp_value is not None:
                    vitals[comp_code] = VitalSign(
                        code=comp_code, display=comp_display,
                        value=float(comp_value), unit=comp_vq.get("unit", ""),
                        date=obs.get("effectiveDateTime"),
                    )
            continue
        vitals[code] = VitalSign(
            code=code, display=display,
            value=float(value), unit=vq.get("unit", ""),
            date=obs.get("effectiveDateTime"),
        )
    return vitals


@mcp.tool(
    name="get_patient_summary",
    description=(
        "Extract comprehensive patient data from FHIR including demographics, "
        "conditions, medications, labs, allergies, procedures, and vital signs "
        "for perioperative assessment. Patient ID is optional if FHIR context is available."
    ),
)
async def get_patient_summary(
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if patient context exists."] = None,
) -> str:
    """Extract and structure patient data for pre-operative assessment."""
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id

    if not patient_id:
        return "Error: No patient ID provided and no FHIR context available."

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    vitals_obs = await client.get_observations(patient_id, category="vital-signs")
    allergies = await client.get_allergies(patient_id)
    procedures = await client.get_procedures(patient_id)

    vitals = _extract_vitals(vitals_obs)
    bmi = vitals.get("39156-5")

    summary = PatientSummary(
        patient_id=patient_id,
        name=_extract_name(patient),
        age=_calculate_age(patient.get("birthDate", "")),
        sex=patient.get("gender", "unknown"),
        bmi=bmi.value if bmi else None,
        conditions=_extract_conditions(conditions),
        active_medications=_extract_medications(medications),
        allergies=_extract_allergies(allergies),
        recent_procedures=_extract_procedures(procedures),
        vital_signs=vitals,
    )
    return summary.model_dump_json(indent=2)
