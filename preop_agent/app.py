"""
PreOp Intelligence Agent — A2A application entry point.

Start with:
    uvicorn preop_agent.app:a2a_app --host 0.0.0.0 --port 8004
"""
import os

from a2a.types import AgentSkill
from shared.app_factory import create_a2a_app

from .agent import root_agent

a2a_app = create_a2a_app(
    agent=root_agent,
    name="preop_intelligence",
    description=(
        "Pre-operative + post-operative risk assessment across all adult surgeries — "
        "the upstream half of a two-agent A2A perioperative system (PreOp Intelligence "
        "→ PostOp Monitor). Computes 11 validated clinical risk scores from primary "
        "literature: ASA, RCRI (Lee TH, Circulation 1999), Caprini VTE, STOP-BANG "
        "(Chung F, Anesthesiology 2008), CHA₂DS₂-VASc, MELD-Na, Wells, HEART, LEMON, "
        "GCS, P-POSSUM. Multimodal: parses prior operative-note PDFs into 7 structured "
        "finding types (difficult airway, allergy severity, intra-op hemodynamics, "
        "transfusion history, post-op complications). Medication management with "
        "hold-date calculation from surgery date, drug-drug interactions, eGFR-based "
        "renal dose adjustment, allergy cross-reactivity, and SCIP-aligned antibiotic "
        "prophylaxis. Every output ships with an independent verification pass — "
        "per-section confidence (high/medium/low), unverified-area list, source FHIR "
        "resource IDs as provenance — and the literature citation for every score. "
        "Physician-review drafts only. Aligned with ACS NSQIP risk-adjusted reporting, "
        "SCIP perioperative quality measures, and CMS BPCI-Advanced surgical "
        "episode-based payment programs."
    ),
    url=os.getenv("PREOP_AGENT_URL", os.getenv("BASE_URL", "http://localhost:8004")),
    port=8004,
    fhir_extension_uri=f"{os.getenv('PO_PLATFORM_BASE_URL', 'https://app.promptopinion.ai')}/schemas/a2a/v1/fhir-context",
    require_api_key=False,
    skills=[
        AgentSkill(
            id="preop-clearance-report",
            name="preop-clearance-report",
            description="Generate a comprehensive pre-operative clearance assessment: all 11 validated risk scores with primary-literature citations, medication review with hold-date calculation against the surgery date, lab readiness check, anesthesia evaluation, and the independent verification pass with per-section confidence and FHIR resource provenance.",
            tags=["perioperative", "surgery", "risk-assessment", "fhir"],
        ),
        AgentSkill(
            id="surgical-risk-assessment",
            name="surgical-risk-assessment",
            description="Calculate the 4 core perioperative scores — ASA, RCRI (Lee TH, Circulation 1999), Caprini VTE, STOP-BANG (Chung F, Anesthesiology 2008) — for a planned surgery. Use alongside advanced-risk-scores for the full set of 11 validated scores.",
            tags=["risk-scores", "cardiac", "vte", "osa"],
        ),
        AgentSkill(
            id="periop-medication-review",
            name="periop-medication-review",
            description="Review medications for perioperative management — hold timing for anticoagulants, diabetes adjustments, herbal supplement cessation.",
            tags=["medications", "anticoagulation", "safety"],
        ),
        AgentSkill(
            id="lab-readiness-check",
            name="lab-readiness-check",
            description="Check if pre-op labs are current, within range, and identify missing required labs.",
            tags=["labs", "screening"],
        ),
        AgentSkill(
            id="anesthesia-evaluation",
            name="anesthesia-evaluation",
            description="Assess airway risk, NPO guidance, allergies, and anesthesia-specific recommendations.",
            tags=["anesthesia", "airway", "safety"],
        ),
        AgentSkill(
            id="advanced-risk-scores",
            name="advanced-risk-scores",
            description="Calculate advanced scores: CHA₂DS₂-VASc (stroke), MELD-Na (liver), Wells (DVT), HEART (chest pain), LEMON (airway), GCS (neuro), P-POSSUM (surgical mortality).",
            tags=["risk-scores", "cha2ds2vasc", "meld", "wells", "heart", "lemon", "possum"],
        ),
        AgentSkill(
            id="drug-interactions",
            name="drug-interactions",
            description="Check all active medications for drug-drug interactions with severity, mechanisms, and perioperative recommendations.",
            tags=["medications", "interactions", "safety"],
        ),
        AgentSkill(
            id="renal-dose-adjustment",
            name="renal-dose-adjustment",
            description="Calculate renal dose adjustments based on eGFR for all active medications.",
            tags=["renal", "dosing", "gfr", "ckd"],
        ),
        AgentSkill(
            id="allergy-cross-reactivity",
            name="allergy-cross-reactivity",
            description="Check allergy cross-reactivity with current meds and perioperative drugs. Includes surgical prophylaxis alternatives.",
            tags=["allergy", "cross-reactivity", "safety"],
        ),
        AgentSkill(
            id="antibiotic-prophylaxis",
            name="antibiotic-prophylaxis",
            description="Select surgical antibiotic prophylaxis with dose, timing, and allergy-based alternatives.",
            tags=["antibiotics", "prophylaxis", "surgery"],
        ),
        AgentSkill(
            id="blood-product-anticipation",
            name="blood-product-anticipation",
            description="Predict blood product needs — crossmatch units, transfusion thresholds, cell saver recommendation.",
            tags=["blood", "transfusion", "anemia"],
        ),
        AgentSkill(
            id="frailty-assessment",
            name="frailty-assessment",
            description="Assess patient frailty using FRAIL scale with prehabilitation recommendations.",
            tags=["frailty", "geriatric", "prehabilitation"],
        ),
        AgentSkill(
            id="patient-education",
            name="patient-education",
            description="Generate plain-language pre-op instructions for the patient — fasting, meds, what to bring.",
            tags=["education", "patient", "instructions"],
        ),
        AgentSkill(
            id="surgical-safety-checklist",
            name="surgical-safety-checklist",
            description="Generate WHO-style surgical safety checklist with patient-specific safety flags.",
            tags=["checklist", "safety", "WHO"],
        ),
        AgentSkill(
            id="preop-imaging-assessment",
            name="preop-imaging-assessment",
            description="Assess required pre-op imaging (CXR, ECG, echo, CT), check availability, flag missing/expired, parse report findings.",
            tags=["imaging", "radiology", "ecg", "xray", "echo"],
        ),
        AgentSkill(
            id="prior-operative-note-parsing",
            name="prior-operative-note-parsing",
            description="Parse a prior operative/surgical report (PDF or text). Extracts difficult-airway history, drug allergies with severity, intra-op hemodynamics (CPB time, LVEF, peak creatinine), transfusion history, and post-op complications (AFib, AKI, pneumonia). Each finding is mapped to a concrete pre-op implication.",
            tags=["multimodal", "pdf", "operative-note", "airway", "allergy", "history"],
        ),
        AgentSkill(
            id="clinical-output-verification",
            name="clinical-output-verification",
            description="Independent verification + confidence pass on the generated assessment. Re-fetches FHIR resources, returns per-section confidence (high/medium/low) tied to data completeness, lists unverified areas, and provides source FHIR resource IDs as provenance for every claim category. Aligned with ACS NSQIP risk-adjusted reporting and SCIP perioperative quality measures. All outputs are physician-review drafts.",
            tags=["verification", "safety", "confidence-scoring", "provenance", "physician-review", "ACS-NSQIP", "SCIP"],
        ),
        AgentSkill(
            id="perioperative-handoff-to-postop",
            name="perioperative-handoff-to-postop",
            description="Hand the patient off to the PostOp Monitor agent for surgery-day and post-op surveillance. Carries forward the surgery type, surgery date, ASA class, RCRI score, anticipated airway difficulty, anticoagulation hold plan, and intra-op risk flags so post-op monitoring is anchored to the same FHIR context and risk profile. Pre-op → post-op is the highest-risk clinical handoff in surgical care; this agent pair is engineered to make it auditable.",
            tags=["handoff", "perioperative", "preop-to-postop", "transitions-of-care", "multi-agent", "continuity"],
        ),
    ],
)
