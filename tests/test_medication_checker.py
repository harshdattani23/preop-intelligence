"""Test perioperative medication checker."""

import json

import pytest

from src.mcp_server.tools.periop_medications import check_periop_medications


@pytest.mark.asyncio
async def test_patient_a_no_meds():
    result = json.loads(await check_periop_medications(
        patient_id="patient-a",
        surgery_date="2026-05-01",
    ))
    # Patient A has no medications
    assert isinstance(result, dict)
    assert result["message"] == "No active medications found."


@pytest.mark.asyncio
async def test_patient_b_diabetes_meds():
    result = json.loads(await check_periop_medications(
        patient_id="patient-b",
        surgery_date="2026-05-01",
    ))
    assert isinstance(result, list)
    assert len(result) >= 5
    med_names = [r["medication_name"].lower() for r in result]
    # Should include metformin, insulin, lisinopril, aspirin
    assert any("metformin" in n for n in med_names)
    assert any("insulin" in n for n in med_names)


@pytest.mark.asyncio
async def test_patient_c_warfarin():
    result = json.loads(await check_periop_medications(
        patient_id="patient-c",
        surgery_date="2026-05-01",
    ))
    assert isinstance(result, list)
    # Find warfarin entry
    warfarin = [r for r in result if "warfarin" in r["medication_name"].lower()]
    assert len(warfarin) >= 1
    assert warfarin[0]["action"] == "hold"
    assert warfarin[0]["urgency"] == "critical"


@pytest.mark.asyncio
async def test_patient_d_herbal_supplements():
    result = json.loads(await check_periop_medications(
        patient_id="patient-d",
        surgery_date="2026-05-01",
    ))
    assert isinstance(result, list)
    # Should flag apixaban and herbal supplements
    actions = {r["medication_name"].lower(): r["action"] for r in result}
    # Apixaban should be held
    apixaban_entries = [r for r in result if "apixaban" in r["medication_name"].lower()]
    assert len(apixaban_entries) >= 1
    assert apixaban_entries[0]["action"] == "hold"
