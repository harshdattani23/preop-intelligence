"""
PostOp Monitor tools — reuses preop_agent tools where the underlying logic is
identical (FHIR fetchers, scoring, drug-intelligence). Adds two thin wrappers
specific to post-operative monitoring.
"""
from preop_agent.tools.preop_tools import get_patient_preop_summary
from preop_agent.tools.advanced_scores_a2a import calculate_advanced_risk_scores
from preop_agent.tools.drug_intelligence_a2a import (
    check_drug_interactions_a2a,
    calculate_renal_dose_adjustments_a2a,
    check_allergy_cross_reactivity_a2a,
)
from preop_agent.tools.surgical_history_a2a import parse_prior_operative_note_a2a
from preop_agent.tools.verification_a2a import verify_clinical_output_a2a

from .postop_tools import (
    assess_postop_complications,
    recommend_postop_monitoring,
)

__all__ = [
    "get_patient_preop_summary",
    "calculate_advanced_risk_scores",
    "check_drug_interactions_a2a",
    "calculate_renal_dose_adjustments_a2a",
    "check_allergy_cross_reactivity_a2a",
    "parse_prior_operative_note_a2a",
    "assess_postop_complications",
    "recommend_postop_monitoring",
    "verify_clinical_output_a2a",
]
