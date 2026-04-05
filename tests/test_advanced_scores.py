"""Test advanced clinical scoring systems."""

import json

import pytest

from src.mcp_server.tools.advanced_scores import calculate_advanced_risk_scores


@pytest.mark.asyncio
async def test_patient_c_all_scores():
    """Patient C (high risk) should trigger significant scores."""
    result = json.loads(await calculate_advanced_risk_scores(
        surgery_type="abdominal aortic aneurysm repair",
        patient_id="patient-c",
    ))

    # CHA2DS2-VASc: AFib + CHF + HTN + age 72 + vascular + TIA = high
    assert result["cha2ds2vasc"]["score"] >= 4
    assert result["cha2ds2vasc"]["risk_level"] == "high"

    # MELD: creatinine 2.3 + INR 2.8 → elevated
    if result["meld"]["score"] is not None:
        assert result["meld"]["score"] >= 10

    # Wells DVT: previous DVT not in patient C, but surgery planned
    assert result["wells_dvt"]["score"] >= 1

    # LEMON: BMI 38 + neck 44cm + OSA = high
    assert result["lemon_airway"]["risk_level"] in ("moderate", "high")

    # P-POSSUM: AAA repair = major+ operative severity
    assert result["p_possum"]["operative_severity_score"] >= 3
    assert result["p_possum"]["predicted_mortality_pct"] > 0


@pytest.mark.asyncio
async def test_patient_a_low_scores():
    """Patient A (healthy) should have minimal scores."""
    result = json.loads(await calculate_advanced_risk_scores(
        surgery_type="knee arthroscopy",
        patient_id="patient-a",
    ))

    assert result["cha2ds2vasc"]["score"] <= 1  # female gets +1
    assert result["lemon_airway"]["risk_level"] == "low"
    assert result["p_possum"]["risk_level"] == "low"


@pytest.mark.asyncio
async def test_selective_scores():
    """Test requesting specific scores only."""
    result = json.loads(await calculate_advanced_risk_scores(
        surgery_type="hernia repair",
        patient_id="patient-b",
        scores="cha2ds2vasc,possum",
    ))

    assert "cha2ds2vasc" in result
    assert "p_possum" in result
    assert "wells_dvt" not in result
    assert "lemon_airway" not in result
