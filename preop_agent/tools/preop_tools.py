"""
PreOp Intelligence A2A Tools — perioperative risk assessment tools for Google ADK.

Each tool reads FHIR credentials from tool_context.state (injected by fhir_hook)
and queries the patient's FHIR server to compute clinical assessments.
"""

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import httpx
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

FHIR_TIMEOUT = 15
KB_PATH = Path(__file__).resolve().parent.parent.parent / "src" / "data" / "medication_knowledge_base.json"

# --- SNOMED code sets ---
IHD_CODES = {"414545008", "22298006", "413844008", "59021001", "53741008"}
CHF_CODES = {"84114007", "42343007"}
CEREBROVASCULAR_CODES = {"230690007", "266257000"}
DM_CODES = {"44054006", "46635009", "73211009"}
HTN_CODES = {"59621000", "38341003"}
OSA_CODES = {"73430006"}
COPD_CODES = {"13645005"}
CKD_CODES = {"433144002", "46177005", "431855005", "431856006", "433146000"}
DVT_PE_CODES = {"128053003", "59282003", "706870000", "233935004"}

HIGH_RISK_SURGERY_KEYWORDS = [
    "abdominal", "thoracic", "vascular", "aortic", "bowel", "colectomy",
    "gastrectomy", "hepatectomy", "pneumonectomy", "aneurysm", "hernia repair",
]

REFERENCE_RANGES = {
    "6690-2": (4.5, 11.0), "718-7": (12.0, 17.5), "777-3": (150.0, 400.0),
    "2951-2": (136.0, 145.0), "2823-3": (3.5, 5.0), "2160-0": (0.7, 1.3),
    "3094-0": (7.0, 20.0), "2345-7": (70.0, 100.0), "34714-6": (0.9, 1.1),
    "4548-4": (None, 7.0), "42637-9": (None, 100.0),
}


# ── FHIR helpers ──────────────────────────────────────────────────────────────

def _get_fhir_context(tool_context: ToolContext):
    fhir_url = tool_context.state.get("fhir_url", "").rstrip("/")
    fhir_token = tool_context.state.get("fhir_token", "")
    patient_id = tool_context.state.get("patient_id", "")
    missing = [n for n, v in [("fhir_url", fhir_url), ("fhir_token", fhir_token), ("patient_id", patient_id)] if not v]
    if missing:
        return {"status": "error", "error_message": f"FHIR context missing: {', '.join(missing)}. Ensure FHIR context is enabled."}
    return fhir_url, fhir_token, patient_id


def _fhir_get(fhir_url, token, path, params=None):
    response = httpx.get(
        f"{fhir_url}/{path}", params=params,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"},
        timeout=FHIR_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _fhir_search(fhir_url, token, resource_type, params):
    bundle = _fhir_get(fhir_url, token, resource_type, params)
    return [e["resource"] for e in bundle.get("entry", []) if "resource" in e]


def _has_condition(conditions, code_set):
    return any(c.get("code") in code_set for cond in conditions for c in cond.get("code", {}).get("coding", []))


def _get_obs_value(observations, loinc_code):
    for obs in observations:
        for c in obs.get("code", {}).get("coding", []):
            if c.get("code") == loinc_code:
                return obs.get("valueQuantity", {}).get("value")
    return None


def _get_age(patient):
    bd = patient.get("birthDate", "")
    if not bd:
        return 0
    try:
        bd = date.fromisoformat(bd[:10])
    except ValueError:
        return 0
    today = date.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def _get_name(patient):
    names = patient.get("name", [])
    if not names:
        return "Unknown"
    n = names[0]
    return f"{' '.join(n.get('given', []))} {n.get('family', '')}".strip()


def _coding_display(codings):
    for c in codings:
        if c.get("display"):
            return c["display"]
    return "Unknown"


# ── Tool 1: Patient Summary ──────────────────────────────────────────────────

def get_patient_preop_summary(tool_context: ToolContext) -> dict:
    """
    Get comprehensive patient summary for pre-operative assessment.
    Retrieves demographics, active conditions, medications, allergies,
    recent labs, vitals, and surgical history from the FHIR server.
    No arguments required — patient identity comes from session context.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_get_patient_preop_summary patient_id=%s", patient_id)

    try:
        patient = _fhir_get(fhir_url, token, f"Patient/{patient_id}")
        conditions = _fhir_search(fhir_url, token, "Condition", {"patient": patient_id, "_count": "50"})
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
        allergies = _fhir_search(fhir_url, token, "AllergyIntolerance", {"patient": patient_id, "_count": "20"})
        vitals = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "category": "vital-signs", "_sort": "-date", "_count": "20"})
        labs = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "category": "laboratory", "_sort": "-date", "_count": "30"})
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error_message": f"FHIR server error: HTTP {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Could not reach FHIR server: {e}"}

    return {
        "status": "success",
        "patient_id": patient_id,
        "name": _get_name(patient),
        "age": _get_age(patient),
        "gender": patient.get("gender"),
        "birth_date": patient.get("birthDate"),
        "conditions_count": len(conditions),
        "conditions": [c.get("code", {}).get("text") or _coding_display(c.get("code", {}).get("coding", [])) for c in conditions],
        "medications_count": len(meds),
        "medications": [m.get("medicationCodeableConcept", {}).get("text") or _coding_display(m.get("medicationCodeableConcept", {}).get("coding", [])) for m in meds],
        "allergies": [a.get("code", {}).get("text") or _coding_display(a.get("code", {}).get("coding", [])) for a in allergies],
        "recent_vitals": [{
            "name": o.get("code", {}).get("text") or _coding_display(o.get("code", {}).get("coding", [])),
            "value": o.get("valueQuantity", {}).get("value"),
            "unit": o.get("valueQuantity", {}).get("unit"),
            "date": o.get("effectiveDateTime", "")[:10],
        } for o in vitals[:10]],
        "recent_labs": [{
            "name": o.get("code", {}).get("text") or _coding_display(o.get("code", {}).get("coding", [])),
            "value": o.get("valueQuantity", {}).get("value"),
            "unit": o.get("valueQuantity", {}).get("unit"),
            "date": o.get("effectiveDateTime", "")[:10],
        } for o in labs[:15]],
    }


# ── Tool 2: Surgical Risk ────────────────────────────────────────────────────

def calculate_surgical_risk(surgery_type: str, tool_context: ToolContext) -> dict:
    """
    Calculate validated perioperative risk scores for a planned surgery.
    Computes ASA Physical Status, RCRI (cardiac risk), Caprini VTE score,
    and STOP-BANG OSA screening.

    Args:
        surgery_type: Type of planned surgery (e.g. 'knee arthroscopy', 'AAA repair', 'hernia repair')
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_calculate_surgical_risk patient_id=%s surgery=%s", patient_id, surgery_type)

    try:
        patient = _fhir_get(fhir_url, token, f"Patient/{patient_id}")
        conditions = _fhir_search(fhir_url, token, "Condition", {"patient": patient_id, "_count": "50"})
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
        observations = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    age = _get_age(patient)
    gender = patient.get("gender", "").lower()
    bmi = _get_obs_value(observations, "39156-5")
    creatinine = _get_obs_value(observations, "2160-0")
    surgery_lower = surgery_type.lower()
    is_high_risk = any(kw in surgery_lower for kw in HIGH_RISK_SURGERY_KEYWORDS)

    # ASA
    has_chf = _has_condition(conditions, CHF_CODES)
    has_ihd = _has_condition(conditions, IHD_CODES)
    severe = sum([has_chf, _has_condition(conditions, COPD_CODES), bool(creatinine and creatinine > 2.0), bool(bmi and bmi >= 40)])
    moderate = sum([_has_condition(conditions, DM_CODES), _has_condition(conditions, HTN_CODES), bool(bmi and 30 <= (bmi or 0) < 40), has_ihd])
    if (has_chf and has_ihd) or severe >= 2:
        asa = "IV"
    elif severe >= 1 or (moderate >= 2 and (has_chf or _has_condition(conditions, COPD_CODES))):
        asa = "III"
    elif moderate >= 1:
        asa = "II"
    else:
        asa = "I"

    # RCRI
    rcri = 0
    rcri_factors = []
    if is_high_risk:
        rcri += 1; rcri_factors.append(f"High-risk surgery ({surgery_type})")
    if has_ihd:
        rcri += 1; rcri_factors.append("Ischemic heart disease")
    if has_chf:
        rcri += 1; rcri_factors.append("Heart failure")
    if _has_condition(conditions, CEREBROVASCULAR_CODES):
        rcri += 1; rcri_factors.append("Cerebrovascular disease")
    if _has_condition(conditions, DM_CODES) and any("insulin" in (m.get("medicationCodeableConcept", {}).get("text", "") or "").lower() for m in meds):
        rcri += 1; rcri_factors.append("Insulin-dependent diabetes")
    if creatinine and creatinine > 2.0:
        rcri += 1; rcri_factors.append(f"Creatinine {creatinine} >2.0")
    rcri_risk = {0: "3.9%", 1: "6.0%", 2: "10.1%"}.get(rcri, ">15%")

    # STOP-BANG
    sb = 0
    has_osa = _has_condition(conditions, OSA_CODES)
    if has_osa: sb += 3
    if _has_condition(conditions, HTN_CODES): sb += 1
    if bmi and bmi > 35: sb += 1
    if age > 50: sb += 1
    neck = _get_obs_value(observations, "56072-2")
    if neck and neck > 40: sb += 1
    if gender == "male": sb += 1

    # Caprini
    cap = 0
    if 41 <= age <= 60: cap += 1
    elif 61 <= age <= 74: cap += 2
    elif age >= 75: cap += 3
    if any(kw in surgery_lower for kw in ["arthroscopy", "minor", "laparoscopic"]): cap += 1
    elif any(kw in surgery_lower for kw in ["abdominal", "hernia"]): cap += 2
    elif any(kw in surgery_lower for kw in ["aortic", "aneurysm", "vascular"]): cap += 5
    if bmi and bmi > 25: cap += 1
    if has_chf: cap += 1
    if _has_condition(conditions, DVT_PE_CODES): cap += 3

    return {
        "status": "success",
        "asa_class": asa,
        "rcri_score": rcri, "rcri_risk": rcri_risk, "rcri_factors": rcri_factors,
        "stop_bang_score": sb, "stop_bang_risk": "low" if sb <= 2 else ("intermediate" if sb <= 4 else "high"),
        "caprini_score": cap, "caprini_risk": "low" if cap <= 1 else ("moderate" if cap == 2 else ("high" if cap <= 4 else "very high")),
        "escalation_flags": [f for f in [
            "HIGH CARDIAC RISK — cardiology consult recommended" if rcri >= 3 else None,
            f"ASA {asa} — high perioperative mortality risk" if asa in ("IV", "V") else None,
            "HIGH OSA RISK — CPAP post-op, monitored bed" if sb >= 5 else None,
            "VERY HIGH VTE RISK — pharmacologic prophylaxis required" if cap >= 5 else None,
        ] if f],
    }


# ── Tool 3: Medication Check ─────────────────────────────────────────────────

def check_periop_medications(surgery_date: str, tool_context: ToolContext) -> dict:
    """
    Review active medications for perioperative management.
    Flags medications that need to be held, adjusted, or stopped before surgery,
    including anticoagulants, diabetes meds, ACE inhibitors, and herbal supplements.

    Args:
        surgery_date: Planned surgery date in YYYY-MM-DD format
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_check_periop_medications patient_id=%s date=%s", patient_id, surgery_date)

    try:
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    if not meds:
        return {"status": "success", "message": "No active medications found.", "actions": []}

    try:
        with open(KB_PATH) as f:
            kb = json.load(f)
    except FileNotFoundError:
        return {"status": "error", "error_message": "Medication knowledge base not found."}

    try:
        surgery_dt = date.fromisoformat(surgery_date[:10])
    except ValueError:
        surgery_dt = date.today()

    actions = []
    for med in meds:
        concept = med.get("medicationCodeableConcept", {})
        med_name = concept.get("text") or _coding_display(concept.get("coding", []))

        matched = None
        for category, drugs in kb.items():
            for drug_key, drug_info in drugs.items():
                for name in drug_info.get("names", []):
                    if name.lower() in med_name.lower():
                        matched = drug_info
                        break
                if matched:
                    break
            if matched:
                break

        if matched:
            hold_days = matched.get("hold_days", 0)
            action = matched.get("action", "continue")
            if action in ("hold", "stop") and hold_days > 0:
                hold_date = surgery_dt - timedelta(days=hold_days)
                timing = f"Last dose: {hold_date.isoformat()} ({hold_days} days before surgery)"
            else:
                timing = "Continue perioperatively"
            actions.append({
                "medication": med_name,
                "action": action,
                "timing": timing,
                "details": matched.get("details", ""),
                "urgency": matched.get("urgency", "routine"),
            })
        else:
            actions.append({
                "medication": med_name,
                "action": "continue",
                "timing": "No specific perioperative guidance — continue unless directed otherwise",
                "details": "",
                "urgency": "routine",
            })

    actions.sort(key=lambda a: {"critical": 0, "important": 1, "routine": 2}.get(a["urgency"], 3))
    return {"status": "success", "patient_id": patient_id, "surgery_date": surgery_date, "actions": actions}


# ── Tool 4: Lab Readiness ────────────────────────────────────────────────────

def assess_lab_readiness(surgery_type: str, surgery_date: str, tool_context: ToolContext) -> dict:
    """
    Check if pre-operative labs are current, within normal range, and identify
    any missing required labs based on the patient's conditions and surgery type.

    Args:
        surgery_type: Planned surgery type (e.g. 'hernia repair', 'AAA repair')
        surgery_date: Planned surgery date in YYYY-MM-DD format
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_assess_lab_readiness patient_id=%s surgery=%s", patient_id, surgery_type)

    try:
        patient = _fhir_get(fhir_url, token, f"Patient/{patient_id}")
        conditions = _fhir_search(fhir_url, token, "Condition", {"patient": patient_id, "_count": "50"})
        meds = _fhir_search(fhir_url, token, "MedicationRequest", {"patient": patient_id, "status": "active", "_count": "50"})
        labs = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "category": "laboratory", "_sort": "-date", "_count": "50"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    try:
        ref_date = date.fromisoformat(surgery_date[:10])
    except ValueError:
        ref_date = date.today()

    # Determine required labs
    required = [("6690-2", "WBC"), ("718-7", "Hemoglobin"), ("777-3", "Platelets")]
    age = _get_age(patient)
    if age > 50 or _has_condition(conditions, CHF_CODES | IHD_CODES):
        required += [("2951-2", "Sodium"), ("2823-3", "Potassium"), ("2160-0", "Creatinine"), ("2345-7", "Glucose")]
    if any("warfarin" in (m.get("medicationCodeableConcept", {}).get("text", "") or "").lower() or "apixaban" in (m.get("medicationCodeableConcept", {}).get("text", "") or "").lower() for m in meds):
        required += [("34714-6", "INR")]
    if _has_condition(conditions, DM_CODES):
        required += [("4548-4", "HbA1c")]
    if _has_condition(conditions, CHF_CODES):
        required += [("42637-9", "BNP")]

    current, expired, missing, abnormal = [], [], [], []
    for loinc, name in required:
        matches = [o for o in labs for c in o.get("code", {}).get("coding", []) if c.get("code") == loinc]
        if not matches:
            missing.append(name)
            continue
        latest = max(matches, key=lambda o: o.get("effectiveDateTime", ""))
        val = latest.get("valueQuantity", {}).get("value")
        dt = latest.get("effectiveDateTime", "")[:10]
        try:
            days_old = (ref_date - date.fromisoformat(dt)).days
        except ValueError:
            days_old = 999

        ref = REFERENCE_RANGES.get(loinc, (None, None))
        is_abnormal = False
        if val is not None:
            if ref[0] is not None and val < ref[0]:
                is_abnormal = True
            if ref[1] is not None and val > ref[1]:
                is_abnormal = True

        entry = {"test": name, "value": val, "unit": latest.get("valueQuantity", {}).get("unit", ""), "date": dt, "days_old": days_old}
        if days_old > 30:
            expired.append(entry)
        else:
            current.append(entry)
        if is_abnormal:
            abnormal.append(entry)

    return {
        "status": "success",
        "overall_ready": len(missing) == 0 and len(expired) == 0,
        "current_labs": current, "expired_labs": expired,
        "missing_labs": missing, "abnormal_labs": abnormal,
    }


# ── Tool 5: Anesthesia Considerations ────────────────────────────────────────

def get_anesthesia_considerations(tool_context: ToolContext) -> dict:
    """
    Assess anesthesia risk factors including airway difficulty (BMI, neck circumference,
    OSA), NPO fasting guidance, drug allergies, and prior anesthesia complications.
    No arguments required — patient identity comes from session context.
    """
    ctx = _get_fhir_context(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, token, patient_id = ctx
    logger.info("tool_get_anesthesia_considerations patient_id=%s", patient_id)

    try:
        conditions = _fhir_search(fhir_url, token, "Condition", {"patient": patient_id, "_count": "50"})
        observations = _fhir_search(fhir_url, token, "Observation", {"patient": patient_id, "_count": "50"})
        allergies = _fhir_search(fhir_url, token, "AllergyIntolerance", {"patient": patient_id, "_count": "20"})
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

    bmi = _get_obs_value(observations, "39156-5")
    neck = _get_obs_value(observations, "56072-2")
    has_osa = _has_condition(conditions, OSA_CODES)

    airway_factors = []
    if bmi and bmi >= 40: airway_factors.append(f"Morbid obesity (BMI {bmi})")
    elif bmi and bmi >= 35: airway_factors.append(f"Severe obesity (BMI {bmi})")
    if neck and neck > 40: airway_factors.append(f"Large neck circumference ({neck}cm)")
    if has_osa: airway_factors.append("Obstructive sleep apnea")
    if _has_condition(conditions, COPD_CODES): airway_factors.append("COPD — bronchospasm risk")

    airway_risk = "high" if len(airway_factors) >= 2 or any("morbid" in f.lower() for f in airway_factors) else ("moderate" if airway_factors else "low")

    allergy_list = [a.get("code", {}).get("text") or _coding_display(a.get("code", {}).get("coding", [])) for a in allergies]

    recommendations = []
    if airway_risk == "high":
        recommendations.append("Have difficult airway equipment ready (video laryngoscope)")
    if has_osa:
        recommendations.append("Ensure CPAP available post-op, consider monitored bed")
        recommendations.append("Minimize opioids — use multimodal analgesia")
    if _has_condition(conditions, CHF_CODES):
        recommendations.append("Monitor fluid balance, consider arterial line")
    if any("penicillin" in a.lower() for a in allergy_list):
        recommendations.append("Penicillin allergy — use clindamycin or vancomycin for prophylaxis")

    return {
        "status": "success",
        "airway_risk": airway_risk,
        "airway_factors": airway_factors,
        "bmi": bmi,
        "allergies": allergy_list,
        "npo_guidance": "Clear liquids 2h, light meal 6h, full meal 8h before surgery",
        "recommendations": recommendations or ["No specific anesthesia concerns — standard monitoring appropriate"],
    }


# ── Tool 6: Full Pre-Op Clearance Report ─────────────────────────────────────

def generate_preop_clearance_report(surgery_type: str, surgery_date: str, tool_context: ToolContext) -> dict:
    """
    Generate a comprehensive pre-operative clearance report by running ALL assessments:
    patient summary, surgical risk scores, medication review, lab readiness,
    and anesthesia considerations. This is the primary tool — use it to produce
    a complete pre-op evaluation in one call.

    Args:
        surgery_type: Type of planned surgery (e.g. 'AAA repair', 'knee arthroscopy')
        surgery_date: Planned surgery date in YYYY-MM-DD format
    """
    logger.info("tool_generate_preop_clearance_report surgery=%s date=%s", surgery_type, surgery_date)

    summary = get_patient_preop_summary(tool_context)
    if summary.get("status") == "error":
        return summary

    risk = calculate_surgical_risk(surgery_type, tool_context)
    meds = check_periop_medications(surgery_date, tool_context)
    labs = assess_lab_readiness(surgery_type, surgery_date, tool_context)
    anesthesia = get_anesthesia_considerations(tool_context)

    # Collect all escalation flags
    flags = risk.get("escalation_flags", [])
    if labs.get("missing_labs"):
        flags.append(f"MISSING LABS: {', '.join(labs['missing_labs'])}")
    if labs.get("expired_labs"):
        flags.append(f"EXPIRED LABS: {', '.join(e['test'] for e in labs['expired_labs'])}")
    if any(a.get("urgency") == "critical" for a in meds.get("actions", [])):
        critical = [a["medication"] for a in meds["actions"] if a["urgency"] == "critical"]
        flags.append(f"CRITICAL MEDICATION MANAGEMENT: {', '.join(critical)}")
    if anesthesia.get("airway_risk") == "high":
        flags.append("DIFFICULT AIRWAY ANTICIPATED")

    return {
        "status": "success",
        "report_type": "Pre-Operative Clearance Assessment",
        "patient": summary,
        "surgical_risk": risk,
        "medication_review": meds,
        "lab_readiness": labs,
        "anesthesia": anesthesia,
        "escalation_flags": flags,
        "disclaimer": "This is AI-generated decision support. All findings require clinician review and approval before clinical action.",
    }
