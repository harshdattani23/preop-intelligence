"""Pydantic models for PreOp Intelligence clinical data structures."""

from __future__ import annotations

from pydantic import BaseModel


class ConditionInfo(BaseModel):
    code: str
    display: str
    system: str = "http://snomed.info/sct"
    clinical_status: str = "active"
    onset_date: str | None = None


class MedicationInfo(BaseModel):
    code: str
    display: str
    system: str = "http://www.nlm.nih.gov/research/umls/rxnorm"
    dosage: str | None = None
    frequency: str | None = None
    status: str = "active"


class AllergyInfo(BaseModel):
    substance: str
    reaction: str | None = None
    severity: str | None = None  # "mild", "moderate", "severe"
    criticality: str | None = None  # "low", "high", "unable-to-assess"


class ProcedureInfo(BaseModel):
    code: str
    display: str
    date: str | None = None
    status: str = "completed"


class VitalSign(BaseModel):
    code: str
    display: str
    value: float
    unit: str
    date: str | None = None


class PatientSummary(BaseModel):
    patient_id: str
    name: str
    age: int
    sex: str
    bmi: float | None = None
    conditions: list[ConditionInfo] = []
    active_medications: list[MedicationInfo] = []
    allergies: list[AllergyInfo] = []
    recent_procedures: list[ProcedureInfo] = []
    vital_signs: dict[str, VitalSign] = {}


class RiskScoreResult(BaseModel):
    score_name: str
    score_value: int
    risk_level: str  # "low", "intermediate", "high", "very_high"
    risk_percentage: str | None = None
    contributing_factors: list[str] = []
    recommendations: list[str] = []
    citation: str = ""


class SurgicalRiskAssessment(BaseModel):
    asa_class: str
    asa_description: str
    asa_citation: str = ""
    rcri: RiskScoreResult
    caprini_vte: RiskScoreResult
    stop_bang: RiskScoreResult


class MedicationAction(BaseModel):
    medication_name: str
    action: str  # "hold", "continue", "adjust", "stop"
    timing: str  # e.g., "hold 5 days pre-op"
    details: str
    urgency: str  # "routine", "important", "critical"


class LabResult(BaseModel):
    test_name: str
    loinc_code: str
    value: float | None = None
    unit: str = ""
    reference_range: str = ""
    status: str = "normal"  # "normal", "abnormal_high", "abnormal_low", "critical"
    collection_date: str = ""
    is_expired: bool = False
    days_old: int = 0


class LabReadinessReport(BaseModel):
    labs_current: list[LabResult] = []
    labs_expired: list[LabResult] = []
    labs_missing: list[str] = []
    labs_abnormal: list[LabResult] = []
    overall_ready: bool = False


class AnesthesiaAssessment(BaseModel):
    airway_risk: str = "low"  # "low", "moderate", "high"
    airway_factors: list[str] = []
    bmi_category: str = "normal"
    npo_guidance: str = ""
    prior_anesthesia_complications: list[str] = []
    recommendations: list[str] = []


class PreOpReport(BaseModel):
    patient_summary: PatientSummary
    risk_assessment: SurgicalRiskAssessment
    medication_actions: list[MedicationAction] = []
    lab_readiness: LabReadinessReport
    anesthesia_assessment: AnesthesiaAssessment
    ai_synthesis: str = ""
    escalation_flags: list[str] = []
    generated_at: str = ""
