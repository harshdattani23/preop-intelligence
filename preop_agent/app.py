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
        "Perioperative risk assessment specialist. Generates comprehensive pre-operative "
        "clearance reports with ASA classification, RCRI cardiac risk, Caprini VTE score, "
        "STOP-BANG OSA screening, medication management, lab readiness, and anesthesia "
        "considerations — all from the patient's FHIR record."
    ),
    url=os.getenv("PREOP_AGENT_URL", os.getenv("BASE_URL", "http://localhost:8004")),
    port=8004,
    fhir_extension_uri=f"{os.getenv('PO_PLATFORM_BASE_URL', 'https://app.promptopinion.ai')}/schemas/a2a/v1/fhir-context",
    require_api_key=False,
    skills=[
        AgentSkill(
            id="preop-clearance-report",
            name="preop-clearance-report",
            description="Generate a comprehensive pre-operative clearance assessment with all risk scores, medication review, lab check, and anesthesia evaluation.",
            tags=["perioperative", "surgery", "risk-assessment", "fhir"],
        ),
        AgentSkill(
            id="surgical-risk-assessment",
            name="surgical-risk-assessment",
            description="Calculate ASA, RCRI, Caprini VTE, and STOP-BANG scores for a planned surgery.",
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
    ],
)
