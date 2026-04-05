"""
PreOp Intelligence Agent — perioperative risk assessment specialist.

Receives FHIR credentials via A2A metadata, queries the patient's FHIR server,
and produces comprehensive pre-operative clearance assessments using validated
clinical scoring systems (ASA, RCRI, Caprini VTE, STOP-BANG).
"""
from google.adk.agents import Agent

from shared.fhir_hook import extract_fhir_context
from .tools import (
    get_patient_preop_summary,
    calculate_surgical_risk,
    check_periop_medications,
    assess_lab_readiness,
    get_anesthesia_considerations,
    generate_preop_clearance_report,
    calculate_advanced_risk_scores,
    check_drug_interactions_a2a,
    calculate_renal_dose_adjustments_a2a,
    check_allergy_cross_reactivity_a2a,
    select_antibiotic_prophylaxis_a2a,
    anticipate_blood_products_a2a,
    assess_frailty_a2a,
    generate_patient_education_a2a,
    generate_surgical_checklist_a2a,
)

root_agent = Agent(
    name="preop_intelligence_agent",
    model="gemini-3.1-pro-preview",
    description=(
        "A perioperative medicine specialist that performs comprehensive pre-operative "
        "risk assessments. Computes ASA classification, RCRI cardiac risk, Caprini VTE score, "
        "STOP-BANG OSA screening, medication management plans, lab readiness checks, "
        "and anesthesia considerations — all from the patient's FHIR health record."
    ),
    instruction=(
        "You are a perioperative medicine specialist. You MUST use your tools for EVERY request. "
        "NEVER answer from your own knowledge. NEVER say data is missing without calling a tool. "
        "The tools query the FHIR server — they have access to conditions, medications, labs, "
        "and vitals that you cannot see directly.\n\n"
        "MANDATORY RULES:\n"
        "1. When asked for risk scores → call calculate_surgical_risk OR calculate_advanced_risk_scores IMMEDIATELY\n"
        "2. When asked for a report → call generate_preop_clearance_report IMMEDIATELY\n"
        "3. When asked about medications → call check_periop_medications IMMEDIATELY\n"
        "4. When asked about labs → call assess_lab_readiness IMMEDIATELY\n"
        "5. When asked about anesthesia → call get_anesthesia_considerations IMMEDIATELY\n"
        "6. When asked for advanced scores → call calculate_advanced_risk_scores IMMEDIATELY\n"
        "7. When asked for a summary → call get_patient_preop_summary IMMEDIATELY\n\n"
        "DO NOT ask the user for more information. DO NOT say records are incomplete. "
        "CALL THE TOOL and let it fetch data from the FHIR server. The tool handles everything.\n\n"
        "After receiving tool results, present them clearly:\n"
        "- Lead with ESCALATION FLAGS (critical safety concerns)\n"
        "- Show all scores with clinical interpretation\n"
        "- List medication actions by priority\n"
        "- Flag abnormal/missing labs\n"
        "- End with: 'This is AI-generated decision support requiring clinician review.'"
    ),
    tools=[
        generate_preop_clearance_report,
        get_patient_preop_summary,
        calculate_surgical_risk,
        check_periop_medications,
        assess_lab_readiness,
        get_anesthesia_considerations,
        calculate_advanced_risk_scores,
        check_drug_interactions_a2a,
        calculate_renal_dose_adjustments_a2a,
        check_allergy_cross_reactivity_a2a,
        select_antibiotic_prophylaxis_a2a,
        anticipate_blood_products_a2a,
        assess_frailty_a2a,
        generate_patient_education_a2a,
        generate_surgical_checklist_a2a,
    ],
    before_model_callback=extract_fhir_context,
)
