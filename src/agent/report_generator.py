"""Report generator using Gemini 3.1 for clinical synthesis."""

from __future__ import annotations

import json
import os
from datetime import datetime

from google import genai

from src.agent.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.mcp_server.models import (
    AnesthesiaAssessment,
    LabReadinessReport,
    MedicationAction,
    PatientSummary,
    PreOpReport,
    SurgicalRiskAssessment,
)


class ReportGenerator:
    """Generate pre-operative reports using Gemini 3.1 for clinical synthesis."""

    def __init__(self, api_key: str | None = None):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    async def generate_report(
        self,
        patient_summary: PatientSummary,
        risk_assessment: SurgicalRiskAssessment,
        medication_actions: list[MedicationAction],
        lab_readiness: LabReadinessReport,
        anesthesia: AnesthesiaAssessment,
        surgery_type: str,
    ) -> PreOpReport:
        """Generate a complete pre-operative report with AI synthesis."""
        # Build the prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            patient_name=patient_summary.name,
            patient_id=patient_summary.patient_id,
            age=patient_summary.age,
            sex=patient_summary.sex,
            surgery_type=surgery_type,
            patient_summary_json=patient_summary.model_dump_json(indent=2),
            risk_assessment_json=risk_assessment.model_dump_json(indent=2),
            medication_actions_json=json.dumps([m.model_dump() for m in medication_actions], indent=2),
            lab_readiness_json=lab_readiness.model_dump_json(indent=2),
            anesthesia_json=anesthesia.model_dump_json(indent=2),
        )

        # Call Gemini 3.1
        response = await self.client.aio.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=2000,
            ),
        )

        ai_synthesis = response.text

        # Determine escalation flags (rule-based, not AI-dependent)
        escalation_flags = self._compute_escalation_flags(
            risk_assessment, medication_actions, lab_readiness, anesthesia,
        )

        return PreOpReport(
            patient_summary=patient_summary,
            risk_assessment=risk_assessment,
            medication_actions=medication_actions,
            lab_readiness=lab_readiness,
            anesthesia_assessment=anesthesia,
            ai_synthesis=ai_synthesis,
            escalation_flags=escalation_flags,
            generated_at=datetime.now().isoformat(),
        )

    def _compute_escalation_flags(
        self,
        risk: SurgicalRiskAssessment,
        meds: list[MedicationAction],
        labs: LabReadinessReport,
        anesthesia: AnesthesiaAssessment,
    ) -> list[str]:
        flags = []

        if risk.rcri.score_value >= 3:
            flags.append("HIGH CARDIAC RISK — RCRI score >= 3, consider cardiology consultation")

        if risk.asa_class in ("IV", "V"):
            flags.append(f"ASA Class {risk.asa_class} — high perioperative mortality risk")

        critical_meds = [m for m in meds if m.urgency == "critical"]
        if critical_meds:
            med_names = ", ".join(m.medication_name for m in critical_meds)
            flags.append(f"ANTICOAGULATION MANAGEMENT REQUIRED — {med_names}")

        critical_labs = [l for l in labs.labs_abnormal if l.status == "critical"]
        if critical_labs:
            lab_names = ", ".join(f"{l.test_name}: {l.value} {l.unit}" for l in critical_labs)
            flags.append(f"CRITICAL LAB VALUES — {lab_names}")

        if labs.labs_missing:
            flags.append(f"MISSING REQUIRED LABS — {', '.join(labs.labs_missing)}")

        if labs.labs_expired:
            expired_names = ", ".join(l.test_name for l in labs.labs_expired)
            flags.append(f"EXPIRED LABS — must repeat: {expired_names}")

        if anesthesia.airway_risk == "high":
            flags.append("DIFFICULT AIRWAY ANTICIPATED — ensure difficult airway equipment available")

        if risk.caprini_vte.risk_level == "very_high":
            flags.append("VERY HIGH VTE RISK — ensure prophylaxis plan in place")

        if risk.stop_bang.risk_level == "high":
            flags.append("HIGH OSA RISK — CPAP post-op, monitored bed recommended")

        return flags
