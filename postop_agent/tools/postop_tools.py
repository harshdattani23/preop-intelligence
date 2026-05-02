"""
PostOp Monitor — post-operative complication surveillance and monitoring tools.
Reuses the FHIR helpers from preop_agent.tools.preop_tools.
"""
import logging

import httpx
from google.adk.tools import ToolContext

from preop_agent.tools.preop_tools import (
    _get_fhir_context,
    _fhir_get,
    _fhir_search,
    _get_age,
    _get_obs_value,
    _has_condition,
    CHF_CODES,
    IHD_CODES,
    CKD_CODES,
)

logger = logging.getLogger(__name__)

THORACIC_KEYWORDS = ["thoracic", "lobectomy", "pneumonectomy", "esophagectomy", "cabg", "valve"]
ABDOMINAL_KEYWORDS = ["abdominal", "colectomy", "gastrectomy", "hepatectomy", "whipple", "aaa", "aortic"]
VASCULAR_KEYWORDS = ["aaa", "aortic", "vascular", "endarterectomy", "bypass"]


def _classify_surgery(surgery_type: str) -> dict:
    s = (surgery_type or "").lower()
    return {
        "thoracic": any(k in s for k in THORACIC_KEYWORDS),
        "abdominal": any(k in s for k in ABDOMINAL_KEYWORDS),
        "vascular": any(k in s for k in VASCULAR_KEYWORDS),
    }


def assess_postop_complications(
    surgery_type: str,
    post_op_day: int = 1,
    tool_context: ToolContext = None,
) -> dict:
    """
    Screen for the four most common post-operative complications: AKI,
    new-onset atrial fibrillation, delirium, and pulmonary complications.
    Each finding is mapped to a concrete monitoring or intervention action.

    Args:
        surgery_type: Type of surgery performed (e.g., 'AAA repair', 'colectomy').
        post_op_day: Days since surgery. Default 1.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_assess_postop_complications patient_id=%s pod=%d", patient_id, post_op_day)

    try:
        patient = _fhir_get(fhir_url, token, f"Patient/{patient_id}")
        conditions = _fhir_search(fhir_url, token, "Condition", {"patient": patient_id, "_count": "50"})
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
        observations = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "_sort": "-date", "_count": "50"})
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error_message": f"FHIR server error: HTTP {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Could not reach FHIR server: {e}"}

    age = _get_age(patient)
    surgery_class = _classify_surgery(surgery_type)
    findings = []

    creatinine = _get_obs_value(observations, "2160-0")
    egfr = _get_obs_value(observations, "33914-3") or _get_obs_value(observations, "98979-8")
    aki_flag = creatinine is not None and creatinine >= 1.5
    if aki_flag:
        findings.append({
            "complication": "Acute Kidney Injury",
            "risk": "elevated",
            "trigger": f"Cr {creatinine} mg/dL",
            "action": "Trend BUN/Cr q12h; hold nephrotoxins (NSAIDs, ACEi); review contrast exposure; renally dose all meds.",
            "stage_kdigo": "1+" if creatinine < 2.0 else "2+",
        })
    elif _has_condition(conditions, CKD_CODES) or (egfr and egfr < 60):
        findings.append({
            "complication": "AKI surveillance (CKD baseline)",
            "risk": "moderate",
            "trigger": f"baseline CKD; eGFR {egfr}" if egfr else "CKD diagnosis",
            "action": "Daily Cr; strict I/O; avoid nephrotoxins.",
        })

    afib_substrate = age >= 65 or _has_condition(conditions, CHF_CODES) or _has_condition(conditions, IHD_CODES)
    afib_high_risk_surgery = surgery_class["thoracic"] or surgery_class["abdominal"]
    if afib_substrate and afib_high_risk_surgery:
        findings.append({
            "complication": "New-onset Atrial Fibrillation",
            "risk": "elevated",
            "trigger": f"age {age}, cardiac/thoracic substrate, high-risk surgery",
            "action": "Continuous telemetry POD 0-3; correct K/Mg; hold rate-control if hypotensive; CHA₂DS₂-VASc on first AF episode for anticoagulation decision.",
            "incidence_pct": 30 if surgery_class["thoracic"] else 12,
        })

    sedating_meds = [
        m.get("medicationCodeableConcept", {}).get("text", "")
        for m in meds
    ]
    on_opioids = any("opioid" in (t or "").lower() or "morphine" in (t or "").lower() or "fentanyl" in (t or "").lower() or "oxycodone" in (t or "").lower() for t in sedating_meds)
    if age >= 70:
        findings.append({
            "complication": "Post-operative Delirium",
            "risk": "elevated" if on_opioids else "moderate",
            "trigger": f"age {age}" + (", on opioids" if on_opioids else ""),
            "action": "CAM-ICU q-shift; reorient frequently; sleep-wake cycle protection; minimize benzodiazepines; multimodal non-opioid analgesia.",
        })

    if surgery_class["thoracic"] or surgery_class["abdominal"]:
        findings.append({
            "complication": "Pulmonary (atelectasis / pneumonia / VTE)",
            "risk": "elevated",
            "trigger": f"{'thoracic' if surgery_class['thoracic'] else 'upper-abdominal'} incision",
            "action": "Incentive spirometry q1h while awake; early ambulation POD 1; chemical VTE prophylaxis (LMWH); SCDs continuous; daily SpO2 trend.",
        })

    if surgery_class["vascular"]:
        findings.append({
            "complication": "Limb ischemia / graft patency",
            "risk": "monitor",
            "trigger": "vascular surgery",
            "action": "Pulse checks q1h x 24h then q4h; ABI on POD 1; report any pain disproportionate to exam.",
        })

    fever_window = post_op_day in range(3, 8)
    if fever_window:
        findings.append({
            "complication": "Surgical Site Infection window",
            "risk": "monitor",
            "trigger": f"POD {post_op_day} (typical SSI window)",
            "action": "Daily wound exam; if T≥38.0°C send blood + wound + urine cultures; CBC, lactate, procalcitonin.",
        })

    escalations = [f for f in findings if f["risk"] == "elevated"]

    return {
        "status": "success",
        "patient_id": patient_id,
        "post_op_day": post_op_day,
        "surgery_type": surgery_type,
        "surgery_classification": surgery_class,
        "complications_screened": len(findings),
        "elevated_risk_count": len(escalations),
        "findings": findings,
        "disclaimer": "AI-generated decision support requiring clinician review.",
    }


MONITORING_TEMPLATES = {
    "high": {
        "vitals": "q1h x 4h, then q2h x 8h, then q4h",
        "labs": "CBC + BMP q12h x 48h; lactate q6h x 24h",
        "telemetry": "continuous x 72h",
        "mobilization": "OOB to chair POD 0 evening; ambulate POD 1 with PT",
        "discharge_floor": "step-down or ICU x 24-48h before floor transfer",
    },
    "moderate": {
        "vitals": "q4h x 24h, then q8h",
        "labs": "CBC + BMP daily x 3d",
        "telemetry": "continuous x 24-48h if cardiac substrate",
        "mobilization": "OOB POD 1 AM; ambulate POD 1",
        "discharge_floor": "surgical floor",
    },
    "low": {
        "vitals": "q4h x 24h, then q-shift",
        "labs": "BMP POD 1 if comorbid; otherwise as indicated",
        "telemetry": "not required",
        "mobilization": "OOB POD 0; ambulate POD 1",
        "discharge_floor": "surgical floor or short-stay",
    },
}


def recommend_postop_monitoring(
    surgery_type: str,
    asa_class: int = 3,
    tool_context: ToolContext = None,
) -> dict:
    """
    Generate a post-operative monitoring schedule (vitals frequency, lab cadence,
    telemetry, mobilization, discharge plan) based on surgery class and ASA score.

    Args:
        surgery_type: Type of surgery performed.
        asa_class: Patient's ASA classification (1-5). Default 3.
    """
    surgery_class = _classify_surgery(surgery_type)
    high_acuity_surgery = surgery_class["thoracic"] or surgery_class["vascular"] or (surgery_class["abdominal"] and "aaa" in (surgery_type or "").lower())

    if high_acuity_surgery or asa_class >= 4:
        tier = "high"
    elif surgery_class["abdominal"] or asa_class == 3:
        tier = "moderate"
    else:
        tier = "low"

    plan = dict(MONITORING_TEMPLATES[tier])

    red_flags = [
        "MAP < 65 mmHg sustained > 5 min",
        "HR > 120 or new arrhythmia",
        "SpO2 < 92% on supplemental O2",
        "UOP < 0.5 mL/kg/hr x 2h",
        "Lactate > 2.0 or rising",
        "T ≥ 38.5°C or hypothermia",
    ]
    if surgery_class["vascular"]:
        red_flags.append("loss of distal pulse or new limb pain")
    if surgery_class["thoracic"]:
        red_flags.append("chest tube output > 200 mL/hr x 2h")

    return {
        "status": "success",
        "surgery_type": surgery_type,
        "asa_class": asa_class,
        "acuity_tier": tier,
        "monitoring_plan": plan,
        "red_flags_to_call_attending": red_flags,
        "disclaimer": "AI-generated decision support requiring clinician review.",
    }
