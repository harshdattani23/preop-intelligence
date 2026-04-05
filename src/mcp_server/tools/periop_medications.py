"""Tool 3: Check perioperative medication management — holds, adjustments, and safety flags."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Annotated

from src.mcp_server.fhir_client import FHIRClient
from src.mcp_server.models import MedicationAction
from src.mcp_server.app import mcp

KB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "medication_knowledge_base.json"


def _load_knowledge_base() -> dict:
    with open(KB_PATH) as f:
        return json.load(f)


def _parse_date(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return date.today()


def _match_medication(med_name: str, kb: dict) -> tuple[str, dict] | None:
    """Match a medication display name against the knowledge base."""
    med_lower = med_name.lower()
    for category, drugs in kb.items():
        for drug_key, drug_info in drugs.items():
            for name in drug_info.get("names", []):
                if name.lower() in med_lower:
                    return drug_key, drug_info
    return None


def _extract_med_name(med_resource: dict) -> str:
    concept = med_resource.get("medicationCodeableConcept", {})
    codings = concept.get("coding", [])
    if codings:
        return codings[0].get("display", concept.get("text", "Unknown"))
    return concept.get("text", "Unknown")


def _extract_med_code(med_resource: dict) -> str:
    concept = med_resource.get("medicationCodeableConcept", {})
    codings = concept.get("coding", [])
    if codings:
        return codings[0].get("code", "")
    return ""


def _match_by_code(rxnorm_code: str, kb: dict) -> tuple[str, dict] | None:
    """Match by RxNorm code."""
    if not rxnorm_code:
        return None
    for category, drugs in kb.items():
        for drug_key, drug_info in drugs.items():
            if rxnorm_code in drug_info.get("rxnorm_codes", []):
                return drug_key, drug_info
    return None


@mcp.tool(
    name="check_periop_medications",
    description=(
        "Review active medications and flag those requiring perioperative management: "
        "anticoagulant/antiplatelet hold timing, diabetes medication adjustments, "
        "ACE-I/ARB decisions, herbal supplement cessation, and drug safety alerts."
    ),
)
async def check_periop_medications(
    patient_id: Annotated[str, "FHIR Patient ID"],
    surgery_date: Annotated[str, "Planned surgery date in YYYY-MM-DD format"],
    surgery_risk_level: Annotated[str, "Surgery bleeding risk: 'low', 'moderate', 'high'"] = "moderate",
    fhir_base_url: Annotated[str, "FHIR R4 server base URL"] = "https://hapi.fhir.org/baseR4",
    fhir_token: Annotated[str | None, "FHIR bearer token from SHARP context"] = None,
) -> str:
    """Check medications for perioperative management requirements."""
    client = FHIRClient(base_url=fhir_base_url, fhir_token=fhir_token)
    medications = await client.get_medications(patient_id)

    if not medications:
        return json.dumps({"message": "No active medications found.", "actions": []}, indent=2)

    kb = _load_knowledge_base()
    surgery_dt = _parse_date(surgery_date)
    actions: list[MedicationAction] = []

    for med in medications:
        med_name = _extract_med_name(med)
        med_code = _extract_med_code(med)

        # Try matching by code first, then by name
        match = _match_by_code(med_code, kb) or _match_medication(med_name, kb)

        if match:
            drug_key, drug_info = match
            hold_days = drug_info.get("hold_days", 0)
            action = drug_info.get("action", "continue")

            # Calculate hold date if applicable
            timing = drug_info.get("details", "")
            if action == "hold" and hold_days > 0:
                hold_date = surgery_dt - timedelta(days=hold_days)
                timing = f"Last dose: {hold_date.isoformat()} (hold {hold_days} days before surgery on {surgery_date}). {drug_info.get('details', '')}"
            elif action == "adjust":
                timing = drug_info.get("details", "")
            elif action == "stop":
                hold_date = surgery_dt - timedelta(days=hold_days)
                timing = f"Stop by {hold_date.isoformat()} ({hold_days} days before surgery). {drug_info.get('details', '')}"
            else:
                timing = f"Continue perioperatively. {drug_info.get('details', '')}"

            actions.append(MedicationAction(
                medication_name=med_name,
                action=action,
                timing=timing.strip(),
                details=drug_info.get("resume", ""),
                urgency=drug_info.get("urgency", "routine"),
            ))
        else:
            # Unknown medication — flag for manual review
            actions.append(MedicationAction(
                medication_name=med_name,
                action="continue",
                timing="No specific perioperative guidance found — continue unless otherwise directed.",
                details="Review with pharmacist or anesthesiologist if unsure.",
                urgency="routine",
            ))

    # Sort by urgency: critical > important > routine
    urgency_order = {"critical": 0, "important": 1, "routine": 2}
    actions.sort(key=lambda a: urgency_order.get(a.urgency, 3))

    return json.dumps([a.model_dump() for a in actions], indent=2)
