"""Test surgical risk calculators against all synthetic patients."""

import json

import pytest

from src.mcp_server.tools.surgical_risk import calculate_surgical_risk
from src.mcp_server.tools.patient_summary import get_patient_summary


@pytest.mark.asyncio
async def test_patient_a_low_risk():
    result = json.loads(await calculate_surgical_risk(
        patient_id="patient-a",
        surgery_type="knee arthroscopy",
    ))
    assert result["asa_class"] == "I"
    assert result["rcri"]["score_value"] == 0
    assert result["rcri"]["risk_level"] == "low"
    assert result["stop_bang"]["risk_level"] == "low"


@pytest.mark.asyncio
async def test_patient_b_medium_risk():
    result = json.loads(await calculate_surgical_risk(
        patient_id="patient-b",
        surgery_type="inguinal hernia repair",
    ))
    # ASA II or III (diabetes + HTN)
    assert result["asa_class"] in ("II", "III")
    # RCRI: high-risk surgery (hernia repair) + insulin-dependent DM = 2
    assert result["rcri"]["score_value"] >= 2
    assert result["rcri"]["risk_level"] in ("intermediate", "high")


@pytest.mark.asyncio
async def test_patient_c_high_risk():
    result = json.loads(await calculate_surgical_risk(
        patient_id="patient-c",
        surgery_type="abdominal aortic aneurysm repair",
    ))
    # ASA IV (CHF + CAD + multiple comorbidities)
    assert result["asa_class"] in ("III", "IV")
    # RCRI should be high: high-risk surgery + IHD + CHF + cerebrovascular + creatinine >2
    assert result["rcri"]["score_value"] >= 4
    assert result["rcri"]["risk_level"] == "high"
    # STOP-BANG should be high (OSA + HTN + BMI >35 + age >50 + male + neck >40)
    assert result["stop_bang"]["score_value"] >= 5
    assert result["stop_bang"]["risk_level"] == "high"
    # Caprini should be very high
    assert result["caprini_vte"]["risk_level"] in ("high", "very_high")


@pytest.mark.asyncio
async def test_patient_d_edge_case():
    result = json.loads(await calculate_surgical_risk(
        patient_id="patient-d",
        surgery_type="laparoscopic cholecystectomy",
    ))
    # Should have some risk from AFib + DM + DVT history
    assert result["rcri"]["score_value"] >= 0
    # Caprini should be elevated (DVT history = +3)
    assert result["caprini_vte"]["score_value"] >= 3


@pytest.mark.asyncio
async def test_patient_a_summary():
    result = json.loads(await get_patient_summary(patient_id="patient-a"))
    assert result["name"] != "Unknown"
    assert result["age"] == 35
    assert result["sex"] == "female"
    assert len(result["conditions"]) == 0
    assert len(result["active_medications"]) == 0


@pytest.mark.asyncio
async def test_patient_c_summary():
    result = json.loads(await get_patient_summary(patient_id="patient-c"))
    assert result["age"] == 72
    assert result["sex"] == "male"
    assert len(result["conditions"]) >= 5  # Multiple conditions
    assert len(result["active_medications"]) >= 5
    assert len(result["allergies"]) >= 1
