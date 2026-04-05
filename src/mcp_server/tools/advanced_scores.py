"""MCP Tool wrapper for advanced clinical scoring systems."""

from __future__ import annotations

import json
from typing import Annotated

from src.mcp_server.app import mcp
from src.mcp_server.fhir_client import FHIRClient
from src.scoring.calculators import (
    _calc_cha2ds2vasc,
    _calc_meld,
    _calc_wells_dvt,
    _calc_heart,
    _calc_lemon_airway,
    _calc_gcs,
    _calc_p_possum,
)


@mcp.tool(
    name="calculate_advanced_risk_scores",
    description=(
        "Calculate advanced perioperative risk scores beyond standard ASA/RCRI: "
        "CHA₂DS₂-VASc (stroke risk in AFib), MELD-Na (liver disease), "
        "Wells DVT criteria, HEART score (chest pain), LEMON airway assessment, "
        "Glasgow Coma Scale, and P-POSSUM (surgical mortality prediction). "
        "Patient ID is optional if FHIR context is available."
    ),
)
async def calculate_advanced_risk_scores(
    surgery_type: Annotated[str, "Type of planned surgery"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if patient context exists."] = None,
    scores: Annotated[str | None, "Comma-separated list of scores to calculate. Options: cha2ds2vasc, meld, wells, heart, lemon, gcs, possum. Default: all."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id

    if not patient_id:
        return "Error: No patient ID provided and no FHIR context available."

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    conditions = await client.get_conditions(patient_id)
    observations = await client.get_observations(patient_id)

    requested = set((scores or "cha2ds2vasc,meld,wells,heart,lemon,gcs,possum").lower().replace(" ", "").split(","))

    results = {}
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

    return json.dumps(results, indent=2)
