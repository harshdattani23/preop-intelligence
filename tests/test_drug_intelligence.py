"""Test drug intelligence tools."""

import json
import pytest

from src.mcp_server.tools.drug_intelligence import (
    check_drug_interactions_tool,
    calculate_renal_dose_adjustments_tool,
    check_allergy_cross_reactivity_tool,
)


@pytest.mark.asyncio
async def test_patient_c_drug_interactions():
    """Patient C has warfarin + aspirin + furosemide — should detect interactions."""
    result = json.loads(await check_drug_interactions_tool(patient_id="patient-c"))
    assert result["total_interactions"] >= 2
    # Warfarin + aspirin = moderate
    severities = [i["severity"] for i in result["interactions"]]
    assert "moderate" in severities


@pytest.mark.asyncio
async def test_patient_c_renal_dosing():
    """Patient C has creatinine 2.3 — should flag renal adjustments."""
    result = json.loads(await calculate_renal_dose_adjustments_tool(patient_id="patient-c"))
    assert result["estimated_gfr"] < 60  # CKD with creatinine 2.3
    assert result["adjustments_needed"] >= 1


@pytest.mark.asyncio
async def test_patient_c_allergy_cross_reactivity():
    """Patient C has penicillin allergy — should show cross-reactivity info."""
    result = json.loads(await check_allergy_cross_reactivity_tool(patient_id="patient-c"))
    assert result["allergies_checked"] >= 1
    assert result["results"][0]["allergy_class"] == "Beta-lactam antibiotics"
    assert len(result["results"][0]["safe_alternatives"]) >= 1


@pytest.mark.asyncio
async def test_patient_a_no_interactions():
    """Patient A has no meds — should return empty."""
    result = json.loads(await check_drug_interactions_tool(patient_id="patient-a"))
    assert result["message"] == "No active medications found."


@pytest.mark.asyncio
async def test_patient_a_no_allergies():
    """Patient A has no allergies."""
    result = json.loads(await check_allergy_cross_reactivity_tool(patient_id="patient-a"))
    assert result["message"] == "No allergies documented."
