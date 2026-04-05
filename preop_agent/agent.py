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
        "You are a perioperative medicine specialist AI assistant with secure, read-only access "
        "to a patient's FHIR health record.\n\n"
        "Your primary function is to generate pre-operative clearance assessments for patients "
        "scheduled for surgery. When asked to assess a patient:\n\n"
        "1. Use generate_preop_clearance_report as your primary tool — it runs ALL assessments "
        "   (risk scores, medication review, lab check, anesthesia evaluation) in one call.\n"
        "2. For specific questions, use individual tools:\n"
        "   - get_patient_preop_summary for demographics and clinical overview\n"
        "   - calculate_surgical_risk for ASA/RCRI/Caprini/STOP-BANG scores\n"
        "   - check_periop_medications for medication hold/adjust/stop guidance\n"
        "   - assess_lab_readiness for lab currency and abnormal values\n"
        "   - get_anesthesia_considerations for airway risk and NPO guidance\n\n"
        "When presenting results:\n"
        "- Lead with ESCALATION FLAGS if any exist — these are critical safety concerns\n"
        "- Present risk scores with their clinical interpretation\n"
        "- List medication actions in priority order (critical > important > routine)\n"
        "- Flag missing or expired labs clearly\n"
        "- Include airway risk assessment and recommendations\n"
        "- Always note this is decision support requiring clinician review\n\n"
        "Never fabricate clinical data. If a tool returns an error, explain what happened. "
        "If FHIR context is not available, inform the caller."
    ),
    tools=[
        generate_preop_clearance_report,
        get_patient_preop_summary,
        calculate_surgical_risk,
        check_periop_medications,
        assess_lab_readiness,
        get_anesthesia_considerations,
    ],
    before_model_callback=extract_fhir_context,
)
