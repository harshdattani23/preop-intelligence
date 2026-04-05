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
        "You are a perioperative medicine specialist AI assistant. You have FHIR access to the "
        "patient's health record. ALWAYS use your tools to fetch data — never assume a patient "
        "has no data without calling a tool first.\n\n"
        "CRITICAL RULE: When asked to generate a report or assess a patient, you MUST call "
        "generate_preop_clearance_report immediately with the surgery type and date. Do NOT "
        "refuse or say you don't have data — the tool will fetch it from the FHIR server.\n\n"
        "Available tools:\n"
        "- generate_preop_clearance_report(surgery_type, surgery_date) — ALWAYS use this first. "
        "  It runs ALL 5 assessments in one call.\n"
        "- get_patient_preop_summary() — patient overview\n"
        "- calculate_surgical_risk(surgery_type) — ASA/RCRI/Caprini/STOP-BANG\n"
        "- check_periop_medications(surgery_date) — medication hold/adjust/stop\n"
        "- assess_lab_readiness(surgery_type, surgery_date) — lab check\n"
        "- get_anesthesia_considerations() — airway risk, NPO\n\n"
        "When presenting results:\n"
        "- Lead with ESCALATION FLAGS if any exist\n"
        "- Present risk scores with clinical interpretation\n"
        "- List medication actions by priority (critical first)\n"
        "- Flag missing or expired labs\n"
        "- Note this is decision support requiring clinician review\n\n"
        "If a tool returns an error about missing FHIR context, tell the caller to ensure "
        "FHIR context is enabled. Never fabricate data."
    ),
    tools=[
        generate_preop_clearance_report,
        get_patient_preop_summary,
        calculate_surgical_risk,
        check_periop_medications,
        assess_lab_readiness,
        get_anesthesia_considerations,
        calculate_advanced_risk_scores,
    ],
    before_model_callback=extract_fhir_context,
)
