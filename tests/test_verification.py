"""Tests for the clinical-output verification tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from preop_agent.tools.verification_a2a import (
    _confidence,
    _resource_id,
    verify_clinical_output_a2a,
)


def test_confidence_high():
    assert _confidence(10, 10) == "high"
    assert _confidence(9, 10) == "high"
    assert _confidence(85, 100) == "high"


def test_confidence_medium():
    assert _confidence(5, 10) == "medium"
    assert _confidence(7, 10) == "medium"


def test_confidence_low():
    assert _confidence(2, 10) == "low"
    assert _confidence(0, 10) == "low"


def test_confidence_zero_expected_is_high():
    assert _confidence(0, 0) == "high"


def test_resource_id_formats_correctly():
    assert _resource_id({"resourceType": "Patient", "id": "abc-123"}) == "Patient/abc-123"
    assert _resource_id({"resourceType": "Observation", "id": "lab-1"}) == "Observation/lab-1"


def test_resource_id_handles_missing_fields():
    assert _resource_id({}) == "?/?"
    assert _resource_id({"resourceType": "Patient"}) == "Patient/?"


def test_verification_returns_error_without_fhir_context():
    tool_context = MagicMock()
    tool_context.state.get.return_value = ""
    result = verify_clinical_output_a2a(
        surgery_type="hernia repair",
        surgery_date="2026-06-01",
        tool_context=tool_context,
    )
    assert result["status"] == "error"
    assert "FHIR context missing" in result["error_message"]


def test_verification_full_pass_with_complete_data():
    """When all FHIR resources are present, verification should pass with high confidence."""
    tool_context = MagicMock()
    tool_context.state.get.side_effect = lambda k, default="": {
        "fhir_url": "https://fhir.example.org",
        "fhir_token": "token-123",
        "patient_id": "patient-1",
    }.get(k, default)

    patient = {
        "resourceType": "Patient",
        "id": "patient-1",
        "birthDate": "1960-01-01",
        "gender": "male",
        "name": [{"given": ["John"], "family": "Doe"}],
    }
    conditions = [
        {"resourceType": "Condition", "id": "c1", "code": {"coding": [{"code": "59621000"}]}},  # HTN
    ]
    meds = [
        {"resourceType": "MedicationRequest", "id": "m1",
         "medicationCodeableConcept": {"text": "metoprolol 50mg"}},
    ]
    observations = [
        {"resourceType": "Observation", "id": "o1", "code": {"coding": [{"code": "39156-5"}]},
         "valueQuantity": {"value": 28.0}, "effectiveDateTime": "2026-05-15"},  # BMI
        {"resourceType": "Observation", "id": "o2", "code": {"coding": [{"code": "2160-0"}]},
         "valueQuantity": {"value": 1.0}, "effectiveDateTime": "2026-05-15"},  # Creatinine
        {"resourceType": "Observation", "id": "o3", "code": {"coding": [{"code": "6690-2"}]},
         "valueQuantity": {"value": 7.0}, "effectiveDateTime": "2026-05-15"},  # WBC
        {"resourceType": "Observation", "id": "o4", "code": {"coding": [{"code": "718-7"}]},
         "valueQuantity": {"value": 14.0}, "effectiveDateTime": "2026-05-15"},  # Hb
        {"resourceType": "Observation", "id": "o5", "code": {"coding": [{"code": "777-3"}]},
         "valueQuantity": {"value": 250.0}, "effectiveDateTime": "2026-05-15"},  # Platelets
        {"resourceType": "Observation", "id": "o6", "code": {"coding": [{"code": "2951-2"}]},
         "valueQuantity": {"value": 140.0}, "effectiveDateTime": "2026-05-15"},  # Sodium
        {"resourceType": "Observation", "id": "o7", "code": {"coding": [{"code": "2823-3"}]},
         "valueQuantity": {"value": 4.0}, "effectiveDateTime": "2026-05-15"},  # Potassium
        {"resourceType": "Observation", "id": "o8", "code": {"coding": [{"code": "2345-7"}]},
         "valueQuantity": {"value": 90.0}, "effectiveDateTime": "2026-05-15"},  # Glucose
    ]
    allergies = [
        {"resourceType": "AllergyIntolerance", "id": "a1", "code": {"text": "penicillin"}},
    ]

    with patch("preop_agent.tools.verification_a2a._fhir_get", return_value=patient), \
         patch("preop_agent.tools.verification_a2a._fhir_search", side_effect=[conditions, meds, observations, allergies]):
        result = verify_clinical_output_a2a(
            surgery_type="hernia repair",
            surgery_date="2026-06-01",
            tool_context=tool_context,
        )

    assert result["status"] == "success"
    assert result["physician_review_required"] is True
    assert result["overall_confidence"] in ("high", "medium")
    assert "verification_method" in result
    assert "regulatory_alignment" in result
    assert "ACS NSQIP" in result["regulatory_alignment"]
    assert "SCIP" in result["regulatory_alignment"]
    assert "PHYSICIAN-REVIEW DRAFT" in result["disclaimer"]
    # Sections must be present
    for section in ("patient_summary", "surgical_risk", "medication_review",
                    "lab_readiness", "anesthesia"):
        assert section in result["sections"]
        assert result["sections"][section]["confidence"] in ("high", "medium", "low")
        assert isinstance(result["sections"][section]["source_resources"], list)


def test_verification_flags_missing_data():
    """When labs are missing, verification should flag the lab_readiness section as low."""
    tool_context = MagicMock()
    tool_context.state.get.side_effect = lambda k, default="": {
        "fhir_url": "https://fhir.example.org",
        "fhir_token": "token-123",
        "patient_id": "patient-1",
    }.get(k, default)

    patient = {
        "resourceType": "Patient",
        "id": "patient-1",
        "birthDate": "1955-01-01",  # age >= 70 → triggers extended labs
        "gender": "female",
        "name": [{"given": ["Jane"], "family": "Doe"}],
    }
    conditions = []
    meds = []
    observations = []  # no labs at all
    allergies = []

    with patch("preop_agent.tools.verification_a2a._fhir_get", return_value=patient), \
         patch("preop_agent.tools.verification_a2a._fhir_search", side_effect=[conditions, meds, observations, allergies]):
        result = verify_clinical_output_a2a(
            surgery_type="hernia repair",
            surgery_date="2026-06-01",
            tool_context=tool_context,
        )

    assert result["status"] == "success"
    assert result["overall_confidence"] == "low"
    assert result["verification_pass"] is False
    assert result["sections"]["lab_readiness"]["confidence"] == "low"
    assert any("Lab readiness" in u for u in result["unverified_areas"])
