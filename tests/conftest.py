"""Shared test fixtures for PreOp Intelligence tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data" / "synthetic_patients"


@pytest.fixture
def patient_a_bundle() -> dict:
    with open(DATA_DIR / "patient_a_low_risk.json") as f:
        return json.load(f)


@pytest.fixture
def patient_b_bundle() -> dict:
    with open(DATA_DIR / "patient_b_medium_risk.json") as f:
        return json.load(f)


@pytest.fixture
def patient_c_bundle() -> dict:
    with open(DATA_DIR / "patient_c_high_risk.json") as f:
        return json.load(f)


@pytest.fixture
def patient_d_bundle() -> dict:
    with open(DATA_DIR / "patient_d_edge_case.json") as f:
        return json.load(f)


@pytest.fixture
def fhir_client_local_a():
    from src.mcp_server.fhir_client import FHIRClient
    return FHIRClient(local_bundle_path=str(DATA_DIR / "patient_a_low_risk.json"))


@pytest.fixture
def fhir_client_local_b():
    from src.mcp_server.fhir_client import FHIRClient
    return FHIRClient(local_bundle_path=str(DATA_DIR / "patient_b_medium_risk.json"))


@pytest.fixture
def fhir_client_local_c():
    from src.mcp_server.fhir_client import FHIRClient
    return FHIRClient(local_bundle_path=str(DATA_DIR / "patient_c_high_risk.json"))


@pytest.fixture
def fhir_client_local_d():
    from src.mcp_server.fhir_client import FHIRClient
    return FHIRClient(local_bundle_path=str(DATA_DIR / "patient_d_edge_case.json"))
