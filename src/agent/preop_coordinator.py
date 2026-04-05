"""PreOp Coordinator — orchestrates all MCP tools and generates the final report."""

from __future__ import annotations

import asyncio
import json
import os

from dotenv import load_dotenv

from src.agent.report_generator import ReportGenerator
from src.mcp_server.models import (
    AnesthesiaAssessment,
    LabReadinessReport,
    MedicationAction,
    PatientSummary,
    PreOpReport,
    SurgicalRiskAssessment,
)
from src.mcp_server.tools.anesthesia import get_anesthesia_considerations
from src.mcp_server.tools.lab_readiness import assess_lab_readiness
from src.mcp_server.tools.patient_summary import get_patient_summary
from src.mcp_server.tools.periop_medications import check_periop_medications
from src.mcp_server.tools.surgical_risk import calculate_surgical_risk

load_dotenv()


class PreOpCoordinator:
    """Orchestrate pre-operative assessment using MCP tools + Claude synthesis."""

    def __init__(self, api_key: str | None = None):
        self.report_generator = ReportGenerator(
            api_key=api_key or os.getenv("GEMINI_API_KEY")
        )

    async def run_assessment(
        self,
        patient_id: str,
        surgery_type: str,
        surgery_date: str,
        fhir_base_url: str = "https://hapi.fhir.org/baseR4",
        fhir_token: str | None = None,
        anesthesia_type: str = "general",
    ) -> PreOpReport:
        """Run complete pre-operative assessment pipeline.

        1. Get patient summary
        2. Run risk calculators, medication check, lab check, anesthesia assessment in parallel
        3. Synthesize with Claude API
        4. Return structured PreOpReport
        """
        # Step 1: Get patient summary first (other tools need patient context)
        summary_json = await get_patient_summary(
            patient_id=patient_id,
            fhir_base_url=fhir_base_url,
            fhir_token=fhir_token,
        )
        patient_summary = PatientSummary.model_validate_json(summary_json)

        # Step 2: Run remaining tools in parallel
        risk_json, meds_json, labs_json, anesthesia_json = await asyncio.gather(
            calculate_surgical_risk(
                patient_id=patient_id,
                surgery_type=surgery_type,
                fhir_base_url=fhir_base_url,
                fhir_token=fhir_token,
            ),
            check_periop_medications(
                patient_id=patient_id,
                surgery_date=surgery_date,
                fhir_base_url=fhir_base_url,
                fhir_token=fhir_token,
            ),
            assess_lab_readiness(
                patient_id=patient_id,
                surgery_type=surgery_type,
                surgery_date=surgery_date,
                fhir_base_url=fhir_base_url,
                fhir_token=fhir_token,
            ),
            get_anesthesia_considerations(
                patient_id=patient_id,
                surgery_date=surgery_date,
                anesthesia_type=anesthesia_type,
                fhir_base_url=fhir_base_url,
                fhir_token=fhir_token,
            ),
        )

        # Parse results
        risk_assessment = SurgicalRiskAssessment.model_validate_json(risk_json)

        meds_data = json.loads(meds_json)
        if isinstance(meds_data, dict):
            medication_actions = []
        else:
            medication_actions = [MedicationAction.model_validate(m) for m in meds_data]

        lab_readiness = LabReadinessReport.model_validate_json(labs_json)
        anesthesia = AnesthesiaAssessment.model_validate_json(anesthesia_json)

        # Step 3: Generate report with Claude synthesis
        report = await self.report_generator.generate_report(
            patient_summary=patient_summary,
            risk_assessment=risk_assessment,
            medication_actions=medication_actions,
            lab_readiness=lab_readiness,
            anesthesia=anesthesia,
            surgery_type=surgery_type,
        )

        return report


async def main():
    """Demo: Run assessment for all synthetic patients."""
    coordinator = PreOpCoordinator()

    demo_cases = [
        ("patient-a", "knee arthroscopy", "2026-05-01", "general"),
        ("patient-b", "inguinal hernia repair", "2026-05-01", "general"),
        ("patient-c", "abdominal aortic aneurysm repair", "2026-05-01", "general"),
        ("patient-d", "laparoscopic cholecystectomy", "2026-05-01", "general"),
    ]

    for patient_id, surgery, surgery_date, anesthesia in demo_cases:
        print(f"\n{'='*80}")
        print(f"ASSESSMENT: {patient_id} — {surgery}")
        print(f"{'='*80}")

        report = await coordinator.run_assessment(
            patient_id=patient_id,
            surgery_type=surgery,
            surgery_date=surgery_date,
            anesthesia_type=anesthesia,
        )

        print(f"\nPatient: {report.patient_summary.name}")
        print(f"ASA: {report.risk_assessment.asa_class} — {report.risk_assessment.asa_description}")
        print(f"RCRI: {report.risk_assessment.rcri.score_value} ({report.risk_assessment.rcri.risk_level})")
        print(f"Caprini VTE: {report.risk_assessment.caprini_vte.score_value} ({report.risk_assessment.caprini_vte.risk_level})")
        print(f"STOP-BANG: {report.risk_assessment.stop_bang.score_value} ({report.risk_assessment.stop_bang.risk_level})")

        if report.escalation_flags:
            print("\nESCALATION FLAGS:")
            for flag in report.escalation_flags:
                print(f"  ⚠ {flag}")

        print(f"\nAI SYNTHESIS:\n{report.ai_synthesis}")
        print(f"\nFull report saved: {report.generated_at}")


if __name__ == "__main__":
    asyncio.run(main())
