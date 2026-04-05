"""MCP Tools for drug intelligence — interactions, renal dosing, allergy cross-reactivity."""

from __future__ import annotations

import json
from datetime import date
from typing import Annotated

from src.mcp_server.app import mcp
from src.mcp_server.fhir_client import FHIRClient
from src.scoring.drug_intelligence import (
    check_drug_interactions,
    calculate_renal_adjustments,
    check_allergy_cross_reactivity,
)


def _get_age(patient: dict) -> int:
    bd = patient.get("birthDate", "")
    if not bd:
        return 0
    try:
        bd_date = date.fromisoformat(bd[:10])
    except ValueError:
        return 0
    today = date.today()
    return today.year - bd_date.year - ((today.month, today.day) < (bd_date.month, bd_date.day))


def _get_obs_value(observations: list[dict], loinc_code: str) -> float | None:
    for obs in observations:
        for coding in obs.get("code", {}).get("coding", []):
            if coding.get("code") == loinc_code:
                return obs.get("valueQuantity", {}).get("value")
    return None


@mcp.tool(
    name="check_drug_interactions",
    description=(
        "Check all active medications for drug-drug interactions. "
        "Identifies severe, moderate, and mild interactions with mechanisms, "
        "clinical effects, and recommendations. Includes perioperative-specific "
        "interactions (anticoagulant combos, serotonin syndrome, QT prolongation)."
    ),
)
async def check_drug_interactions_tool(
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if patient context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id

    if not patient_id:
        return "Error: No patient ID provided and no FHIR context available."

    medications = await client.get_medications(patient_id)
    if not medications:
        return json.dumps({"message": "No active medications found.", "interactions": []}, indent=2)

    result = check_drug_interactions(medications)
    return json.dumps(result, indent=2)


@mcp.tool(
    name="calculate_renal_dose_adjustments",
    description=(
        "Calculate renal dose adjustments for all active medications based on "
        "estimated GFR (CKD-EPI 2021). Checks metformin, anticoagulants, opioids, "
        "antibiotics, and other renally-cleared drugs. Provides specific dose "
        "modifications for the patient's kidney function."
    ),
)
async def calculate_renal_dose_adjustments_tool(
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if patient context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id

    if not patient_id:
        return "Error: No patient ID provided and no FHIR context available."

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    medications = await client.get_medications(patient_id)
    observations = await client.get_observations(patient_id, category="laboratory")

    creatinine = _get_obs_value(observations, "2160-0")
    if creatinine is None:
        return json.dumps({"error": "Creatinine not found in labs. Cannot calculate GFR."}, indent=2)

    age = _get_age(patient)
    gender = patient.get("gender", "unknown")

    result = calculate_renal_adjustments(medications, creatinine, age, gender)
    return json.dumps(result, indent=2)


@mcp.tool(
    name="check_allergy_cross_reactivity",
    description=(
        "Check patient allergies for cross-reactivity with current medications "
        "and potential perioperative drugs. Covers penicillin-cephalosporin "
        "cross-reactivity, sulfonamide cross-reactions, opioid alternatives, "
        "and latex allergy precautions. Provides surgical prophylaxis alternatives."
    ),
)
async def check_allergy_cross_reactivity_tool(
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if patient context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id

    if not patient_id:
        return "Error: No patient ID provided and no FHIR context available."

    allergies = await client.get_allergies(patient_id)
    medications = await client.get_medications(patient_id)

    if not allergies:
        return json.dumps({"message": "No allergies documented.", "results": []}, indent=2)

    result = check_allergy_cross_reactivity(allergies, medications)
    return json.dumps(result, indent=2)
