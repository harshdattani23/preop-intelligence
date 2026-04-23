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
    assess_preop_imaging_a2a,
    parse_prior_operative_note_a2a,
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
        "You are PreOp Intelligence — a perioperative medicine specialist AI assistant.\n\n"
        "CONVERSATION FLOW:\n"
        "1. When the user first asks for a pre-op assessment, ask TWO things:\n"
        "   - What surgery is planned? (e.g., 'AAA repair', 'knee replacement')\n"
        "   - When is the surgery scheduled? (e.g., 'May 15, 2026')\n"
        "   Ask naturally in one message. If the user already provided these, skip asking.\n\n"
        "2. Once you have surgery type and date, IMMEDIATELY start calling tools.\n"
        "   Begin with get_patient_preop_summary to get the clinical picture, then run:\n"
        "   - calculate_surgical_risk (ASA, RCRI, Caprini, STOP-BANG)\n"
        "   - calculate_advanced_risk_scores (CHA2DS2-VASc, MELD, Wells, HEART, LEMON, GCS, P-POSSUM)\n"
        "   - check_periop_medications (hold dates calculated from surgery date)\n"
        "   - assess_lab_readiness (lab currency check against surgery date)\n"
        "   - get_anesthesia_considerations (airway, NPO, allergies)\n"
        "   - check_drug_interactions (medication safety)\n"
        "   - calculate_renal_dose_adjustments (kidney-based dosing)\n"
        "   - check_allergy_cross_reactivity (allergy safety)\n"
        "   - assess_preop_imaging (required imaging check)\n\n"
        "3. For specific follow-up questions, call the relevant tool:\n"
        "   - Antibiotic selection → select_antibiotic_prophylaxis\n"
        "   - Blood needs → anticipate_blood_products\n"
        "   - Frailty → assess_frailty\n"
        "   - Patient instructions → generate_patient_education\n"
        "   - Surgical checklist → generate_surgical_checklist\n\n"
        "CRITICAL RULES:\n"
        "- ALWAYS use tools to fetch data. NEVER answer from your own knowledge.\n"
        "- NEVER say records are incomplete without calling a tool first.\n"
        "- If a user uploads a document (PDF, JSON), read it AND ALSO call parse_prior_operative_note "
"with the extracted text so findings are structured and auditable. Combine those findings with tool results.\n"
        "- Remember the surgery type and date throughout the conversation — don't ask again.\n\n"
        "PRESENTATION:\n"
        "- Lead with ESCALATION FLAGS (critical safety concerns) if any\n"
        "- Present risk scores with clinical interpretation\n"
        "- List medication actions by priority (critical → important → routine)\n"
        "- Flag abnormal/missing/expired labs\n"
        "- Include airway risk and anesthesia recommendations\n"
        "- End every clinical response with: 'This is AI-generated decision support requiring clinician review.'\n\n"
        "PERSONALITY:\n"
        "- Be concise, professional, and clinically precise\n"
        "- Use tables and structured formatting for readability\n"
        "- Proactively suggest next steps (e.g., 'Would you like the antibiotic prophylaxis recommendation?')\n"
        "- After presenting results, offer to generate: surgical safety checklist, patient education sheet, or full clearance report"
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
        assess_preop_imaging_a2a,
        parse_prior_operative_note_a2a,
    ],
    before_model_callback=extract_fhir_context,
)
