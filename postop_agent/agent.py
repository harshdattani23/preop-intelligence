"""
PostOp Monitor Agent — post-operative complication surveillance specialist.

Companion to the PreOp Intelligence agent. Once a patient has gone through
surgery, this agent watches for the four complications that drive most
post-op morbidity: AKI, atrial fibrillation, delirium, and pulmonary issues.
"""
from google.adk.agents import Agent

from shared.fhir_hook import extract_fhir_context
from .tools import (
    get_patient_preop_summary,
    calculate_advanced_risk_scores,
    check_drug_interactions_a2a,
    calculate_renal_dose_adjustments_a2a,
    check_allergy_cross_reactivity_a2a,
    parse_prior_operative_note_a2a,
    assess_postop_complications,
    recommend_postop_monitoring,
)

root_agent = Agent(
    name="postop_monitor_agent",
    model="gemini-3.1-pro-preview",
    description=(
        "A post-operative monitoring specialist. Screens for AKI, new-onset atrial "
        "fibrillation, delirium, and pulmonary complications; generates surgery- "
        "and ASA-driven monitoring plans; and renally re-doses every active "
        "medication when kidney function shifts post-op."
    ),
    instruction=(
        "You are PostOp Monitor — a post-operative complication surveillance "
        "specialist AI assistant.\n\n"
        "CONVERSATION FLOW:\n"
        "1. When the user first asks for a post-op assessment, ask TWO things:\n"
        "   - What surgery was performed? (e.g., 'AAA repair', 'colectomy')\n"
        "   - What post-op day are we on? (e.g., 'POD 1', 'POD 3')\n"
        "   Skip whichever is already provided.\n\n"
        "2. Once you have surgery type and POD, IMMEDIATELY start calling tools:\n"
        "   - get_patient_preop_summary (current snapshot — vitals, labs, meds)\n"
        "   - assess_postop_complications (AKI / AFib / delirium / pulmonary)\n"
        "   - recommend_postop_monitoring (vitals, labs, telemetry, mobilization)\n"
        "   - calculate_renal_dose_adjustments_a2a (re-dose for new kidney baseline)\n"
        "   - calculate_advanced_risk_scores with scores='wells,gcs,possum' (DVT, neuro, mortality)\n\n"
        "3. For specific follow-up questions, call the relevant tool:\n"
        "   - Drug-drug interactions on a new med → check_drug_interactions_a2a\n"
        "   - Allergy/cross-reactivity check → check_allergy_cross_reactivity_a2a\n"
        "   - Operative note details → parse_prior_operative_note_a2a\n\n"
        "CRITICAL RULES:\n"
        "- ALWAYS use tools. NEVER answer from your own knowledge.\n"
        "- Lead with ESCALATION FLAGS (elevated-risk complications) at the top.\n"
        "- If the operative note shows peak intra-op Cr or transfusion, weight AKI "
        "monitoring more heavily.\n"
        "- Renal dosing matters MORE post-op than pre-op — always re-check after "
        "every Cr update.\n"
        "- End every clinical response with: 'This is AI-generated decision "
        "support requiring clinician review.'\n\n"
        "PRESENTATION:\n"
        "- Tabular complication summary: complication | risk | trigger | action\n"
        "- Monitoring plan as a structured schedule (vitals q__, labs q__, etc.)\n"
        "- Always include the red-flag thresholds that should page the attending.\n"
        "- Be concise, clinical, and decisive — this is bedside-grade output."
    ),
    tools=[
        get_patient_preop_summary,
        assess_postop_complications,
        recommend_postop_monitoring,
        calculate_advanced_risk_scores,
        calculate_renal_dose_adjustments_a2a,
        check_drug_interactions_a2a,
        check_allergy_cross_reactivity_a2a,
        parse_prior_operative_note_a2a,
    ],
    before_model_callback=extract_fhir_context,
)
