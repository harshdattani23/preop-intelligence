"""
PostOp Monitor Agent — A2A application entry point.

Start with:
    uvicorn postop_agent.app:a2a_app --host 0.0.0.0 --port 8005
"""
import os

from a2a.types import AgentSkill
from shared.app_factory import create_a2a_app

from .agent import root_agent

a2a_app = create_a2a_app(
    agent=root_agent,
    name="postop_monitor",
    description=(
        "Post-operative surveillance across all adult surgeries — the downstream half "
        "of a two-agent A2A perioperative system (PreOp Intelligence → PostOp Monitor). "
        "Receives the patient from PreOp Intelligence after surgery and continues the "
        "same FHIR-grounded conversation with the surgery type, ASA class, RCRI score, "
        "intra-op events, and anticoagulation context already in memory — so post-op "
        "monitoring is anchored to the pre-op risk profile rather than starting from "
        "zero. Screens for the four complications driving most post-op morbidity (KDIGO "
        "AKI, new-onset atrial fibrillation, delirium, pulmonary complications) plus "
        "the SSI surveillance window; generates surgery- and ASA-driven monitoring "
        "plans with vitals frequency, lab cadence, telemetry, mobilization milestones, "
        "and explicit red-flag thresholds; re-computes P-POSSUM mortality + Wells DVT "
        "+ GCS for ongoing risk stratification; re-doses every active medication for "
        "the patient's current eGFR (critical after intra-op AKI or contrast exposure); "
        "parses the operative note (PDF or text) for intra-op events that drive post-op "
        "monitoring. Every output ships with an independent verification pass — "
        "per-section confidence (high/medium/low), unverified-area list, source FHIR "
        "resource IDs as provenance. Physician-review drafts only. Aligned with SCIP "
        "perioperative quality measures and CMS BPCI-Advanced surgical episode-based "
        "payment programs."
    ),
    url=os.getenv("POSTOP_AGENT_URL", os.getenv("BASE_URL", "http://localhost:8005")),
    port=8005,
    fhir_extension_uri=f"{os.getenv('PO_PLATFORM_BASE_URL', 'https://app.promptopinion.ai')}/schemas/a2a/v1/fhir-context",
    require_api_key=False,
    skills=[
        AgentSkill(
            id="postop-complication-screen",
            name="postop-complication-screen",
            description="Screen for AKI, new-onset AFib, delirium, pulmonary complications, and SSI window. Each finding mapped to a concrete monitoring action.",
            tags=["postoperative", "complications", "aki", "afib", "delirium", "fhir"],
        ),
        AgentSkill(
            id="postop-monitoring-plan",
            name="postop-monitoring-plan",
            description="Generate a surgery- and ASA-driven monitoring schedule: vitals frequency, lab cadence, telemetry, mobilization, discharge plan, red-flag thresholds.",
            tags=["postoperative", "monitoring", "vitals", "labs"],
        ),
        AgentSkill(
            id="postop-renal-redose",
            name="postop-renal-redose",
            description="Re-dose every active medication based on the patient's current eGFR — critical after intra-op AKI or contrast exposure.",
            tags=["renal", "dosing", "aki", "postoperative"],
        ),
        AgentSkill(
            id="postop-mortality-prediction",
            name="postop-mortality-prediction",
            description="Calculate P-POSSUM (predicted post-op mortality) plus Wells (DVT) and GCS (neuro) for ongoing risk stratification.",
            tags=["risk-scores", "possum", "mortality", "postoperative"],
        ),
        AgentSkill(
            id="postop-medication-safety",
            name="postop-medication-safety",
            description="Drug-drug interaction check and allergy cross-reactivity check on the current post-op medication list.",
            tags=["medications", "interactions", "allergy", "safety"],
        ),
        AgentSkill(
            id="postop-operative-note-parsing",
            name="postop-operative-note-parsing",
            description="Parse the operative note (PDF or text) to surface intra-op events that drive post-op monitoring: CPB time, peak Cr, transfusions, complications.",
            tags=["multimodal", "pdf", "operative-note", "postoperative"],
        ),
        AgentSkill(
            id="postop-output-verification",
            name="postop-output-verification",
            description="Independent verification + confidence pass on the post-op monitoring plan. Re-fetches FHIR resources, returns per-section confidence (high/medium/low) tied to data completeness, lists unverified areas, and provides source FHIR resource IDs as provenance. All outputs are physician-review drafts requiring bedside verification.",
            tags=["verification", "safety", "confidence-scoring", "provenance", "physician-review", "postoperative"],
        ),
        AgentSkill(
            id="perioperative-handoff-from-preop",
            name="perioperative-handoff-from-preop",
            description="Receive the patient from PreOp Intelligence after surgery. Continues the same FHIR-grounded conversation with the surgery type, surgery date, ASA class, RCRI score, intra-op events, and anticoagulation context already in memory — so post-op monitoring is anchored to the pre-op risk profile rather than starting from zero. Closes the pre-op → post-op handoff loop, the highest-risk transition in surgical care.",
            tags=["handoff", "perioperative", "preop-to-postop", "transitions-of-care", "multi-agent", "continuity"],
        ),
    ],
)
