"""MCP Tools for clinical protocols — antibiotic prophylaxis, blood products,
frailty, patient education, surgical checklist."""

from __future__ import annotations

import json
from typing import Annotated

from src.mcp_server.app import mcp
from src.mcp_server.fhir_client import FHIRClient
from src.scoring.clinical_protocols import (
    select_antibiotic_prophylaxis,
    anticipate_blood_products,
    assess_frailty,
    generate_patient_education,
    generate_surgical_checklist,
)


@mcp.tool(
    name="select_antibiotic_prophylaxis",
    description=(
        "Select appropriate surgical antibiotic prophylaxis based on surgery type "
        "and patient allergies. Provides drug, dose, timing, redosing schedule, "
        "and weight-based adjustments. Handles penicillin allergy alternatives."
    ),
)
async def select_antibiotic_prophylaxis_tool(
    surgery_type: Annotated[str, "Type of planned surgery"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id
    if not patient_id:
        return "Error: No patient ID."

    patient = await client.get_patient(patient_id)
    allergies = await client.get_allergies(patient_id)
    observations = await client.get_observations(patient_id, category="vital-signs")
    return json.dumps(select_antibiotic_prophylaxis(surgery_type, allergies, patient, observations), indent=2)


@mcp.tool(
    name="anticipate_blood_products",
    description=(
        "Predict blood product needs based on surgery type, hemoglobin level, "
        "coagulation status, and anticoagulation. Recommends type & screen, "
        "crossmatch units, and transfusion thresholds."
    ),
)
async def anticipate_blood_products_tool(
    surgery_type: Annotated[str, "Type of planned surgery"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id
    if not patient_id:
        return "Error: No patient ID."

    patient = await client.get_patient(patient_id)
    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    observations = await client.get_observations(patient_id)
    return json.dumps(anticipate_blood_products(surgery_type, patient, conditions, medications, observations), indent=2)


@mcp.tool(
    name="assess_frailty",
    description=(
        "Assess patient frailty using modified FRAIL scale. Evaluates fatigue, "
        "resistance, ambulation, illness burden, and weight loss. Provides "
        "frailty level and prehabilitation recommendations."
    ),
)
async def assess_frailty_tool(
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id
    if not patient_id:
        return "Error: No patient ID."

    patient = await client.get_patient(patient_id)
    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    observations = await client.get_observations(patient_id)
    return json.dumps(assess_frailty(patient, conditions, medications, observations), indent=2)


@mcp.tool(
    name="generate_patient_education",
    description=(
        "Generate plain-language pre-operative instructions for the patient. "
        "Includes fasting rules, medications to stop/continue, what to bring, "
        "allergy reminders, and day-of-surgery instructions."
    ),
)
async def generate_patient_education_tool(
    surgery_type: Annotated[str, "Type of planned surgery"],
    surgery_date: Annotated[str, "Surgery date YYYY-MM-DD"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id
    if not patient_id:
        return "Error: No patient ID."

    patient = await client.get_patient(patient_id)
    medications = await client.get_medications(patient_id)
    allergies = await client.get_allergies(patient_id)
    observations = await client.get_observations(patient_id, category="vital-signs")
    return json.dumps(generate_patient_education(surgery_type, surgery_date, patient, medications, allergies, observations), indent=2)


@mcp.tool(
    name="generate_surgical_checklist",
    description=(
        "Generate a WHO-style surgical safety checklist populated with patient data. "
        "Includes Sign In, Time Out, and Sign Out phases with safety flags for "
        "allergies, difficult airway, anemia, coagulopathy, and comorbidities."
    ),
)
async def generate_surgical_checklist_tool(
    surgery_type: Annotated[str, "Type of planned surgery"],
    surgery_date: Annotated[str, "Surgery date YYYY-MM-DD"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id
    if not patient_id:
        return "Error: No patient ID."

    patient = await client.get_patient(patient_id)
    conditions = await client.get_conditions(patient_id)
    medications = await client.get_medications(patient_id)
    allergies = await client.get_allergies(patient_id)
    observations = await client.get_observations(patient_id)
    return json.dumps(generate_surgical_checklist(surgery_type, surgery_date, patient, conditions, medications, allergies, observations), indent=2)
