"""Test lab readiness assessment."""

import json

import pytest

from src.mcp_server.tools.lab_readiness import assess_lab_readiness


@pytest.mark.asyncio
async def test_patient_a_labs_ready():
    result = json.loads(await assess_lab_readiness(
        patient_id="patient-a",
        surgery_type="knee arthroscopy",
        surgery_date="2026-04-15",
    ))
    assert result["overall_ready"] is True
    assert len(result["labs_missing"]) == 0
    assert len(result["labs_expired"]) == 0


@pytest.mark.asyncio
async def test_patient_c_abnormal_labs():
    result = json.loads(await assess_lab_readiness(
        patient_id="patient-c",
        surgery_type="abdominal aortic aneurysm repair",
        surgery_date="2026-04-15",
    ))
    # Patient C has abnormal creatinine (2.3) and hemoglobin (10.2)
    assert len(result["labs_abnormal"]) >= 2
    abnormal_names = [lab["test_name"] for lab in result["labs_abnormal"]]
    assert "Creatinine" in abnormal_names or "Hemoglobin" in abnormal_names


@pytest.mark.asyncio
async def test_patient_d_expired_labs():
    result = json.loads(await assess_lab_readiness(
        patient_id="patient-d",
        surgery_type="laparoscopic cholecystectomy",
        surgery_date="2026-04-15",
    ))
    # Patient D labs drawn 95+ days ago — should be expired
    assert len(result["labs_expired"]) >= 1
    # Should be missing coag studies (on anticoagulant)
    assert len(result["labs_missing"]) >= 1
    assert result["overall_ready"] is False
