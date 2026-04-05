"""MCP Tool for pre-operative imaging assessment."""

from __future__ import annotations

import json
from typing import Annotated

from src.mcp_server.app import mcp
from src.mcp_server.fhir_client import FHIRClient
from src.scoring.imaging_assessment import assess_preop_imaging


@mcp.tool(
    name="assess_preop_imaging",
    description=(
        "Assess pre-operative imaging requirements and parse available reports. "
        "Determines required imaging based on surgery type and conditions "
        "(chest X-ray, ECG, echocardiogram, CT angiogram, PFTs). "
        "Checks what's available, flags missing/expired studies, and parses "
        "findings from diagnostic reports (cardiomegaly, arrhythmias, EF%, etc.)."
    ),
)
async def assess_preop_imaging_tool(
    surgery_type: Annotated[str, "Type of planned surgery"],
    surgery_date: Annotated[str, "Surgery date YYYY-MM-DD"],
    patient_id: Annotated[str | None, "FHIR Patient ID. Optional if context exists."] = None,
) -> str:
    client, header_patient_id = FHIRClient.from_headers()
    patient_id = patient_id or header_patient_id
    if not patient_id:
        return "Error: No patient ID."

    patient = await client.get_patient(patient_id)
    if not patient:
        return f"Error: Patient {patient_id} not found."

    conditions = await client.get_conditions(patient_id)

    # Fetch diagnostic reports and imaging studies
    diagnostic_reports = []
    imaging_studies = []

    if client.base_url:
        diagnostic_reports = await client._search("DiagnosticReport", {"patient": patient_id, "_count": "50"})
        imaging_studies = await client._search("ImagingStudy", {"patient": patient_id, "_count": "20"})
    elif client._local_bundle:
        diagnostic_reports = client._get_resources_by_type("DiagnosticReport")
        imaging_studies = client._get_resources_by_type("ImagingStudy")

    result = assess_preop_imaging(
        surgery_type, surgery_date, patient, conditions,
        diagnostic_reports, imaging_studies,
    )
    return json.dumps(result, indent=2)
