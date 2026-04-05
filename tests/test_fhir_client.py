"""Test FHIR client with local synthetic bundles."""

import pytest

from src.mcp_server.fhir_client import FHIRClient, DATA_DIR


@pytest.mark.asyncio
async def test_load_patient_a():
    client = FHIRClient(local_bundle_path=str(DATA_DIR / "patient_a_low_risk.json"))
    patient = await client.get_patient("patient-a")
    assert patient is not None
    assert patient["resourceType"] == "Patient"
    assert patient["gender"] == "female"


@pytest.mark.asyncio
async def test_load_patient_a_by_id():
    """Test auto-loading by patient ID without explicit bundle path."""
    client = FHIRClient()
    patient = await client.get_patient("patient-a")
    assert patient is not None
    assert patient["gender"] == "female"


@pytest.mark.asyncio
async def test_patient_b_conditions():
    client = FHIRClient(local_bundle_path=str(DATA_DIR / "patient_b_medium_risk.json"))
    conditions = await client.get_conditions("patient-b")
    assert len(conditions) >= 3  # DM2, HTN, hyperlipidemia
    resource_types = [c["resourceType"] for c in conditions]
    assert all(rt == "Condition" for rt in resource_types)


@pytest.mark.asyncio
async def test_patient_b_medications():
    client = FHIRClient(local_bundle_path=str(DATA_DIR / "patient_b_medium_risk.json"))
    meds = await client.get_medications("patient-b")
    assert len(meds) >= 5  # metformin, insulin, lisinopril, atorvastatin, aspirin


@pytest.mark.asyncio
async def test_patient_c_allergies():
    client = FHIRClient(local_bundle_path=str(DATA_DIR / "patient_c_high_risk.json"))
    allergies = await client.get_allergies("patient-c")
    assert len(allergies) >= 1  # Penicillin


@pytest.mark.asyncio
async def test_patient_c_observations():
    client = FHIRClient(local_bundle_path=str(DATA_DIR / "patient_c_high_risk.json"))
    labs = await client.get_observations("patient-c", category="laboratory")
    assert len(labs) >= 5  # Multiple lab values


@pytest.mark.asyncio
async def test_patient_d_medications():
    client = FHIRClient(local_bundle_path=str(DATA_DIR / "patient_d_edge_case.json"))
    meds = await client.get_medications("patient-d")
    assert len(meds) >= 3  # apixaban, metformin, supplements
