"""Clinical protocol engines — antibiotic prophylaxis, surgical checklist,
blood product anticipation, frailty assessment, patient education.

All functions are pure logic operating on FHIR resource dicts.
No framework dependencies.
"""

from __future__ import annotations

from datetime import date, timedelta


# ══════════════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _has_condition(conditions, code_set):
    for cond in conditions:
        for c in cond.get("code", {}).get("coding", []):
            if c.get("code") in code_set:
                return True
    return False


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
        bd_date = date.fromisoformat(bd[:10])
    except ValueError:
        return 0
    today = date.today()
    return today.year - bd_date.year - ((today.month, today.day) < (bd_date.month, bd_date.day))


def _get_allergy_names(allergies):
    names = []
    for a in allergies:
        code = a.get("code", {})
        name = code.get("text", "")
        if not name:
            codings = code.get("coding", [])
            name = codings[0].get("display", "") if codings else ""
        names.append(name.lower())
    return names


def _get_med_names(medications):
    names = []
    for m in medications:
        concept = m.get("medicationCodeableConcept", {})
        name = concept.get("text", "")
        if not name:
            codings = concept.get("coding", [])
            name = codings[0].get("display", "") if codings else ""
        names.append(name.lower())
    return names


CHF_CODES = {"84114007", "42343007"}
DM_CODES = {"44054006", "46635009", "73211009"}
CKD_CODES = {"433144002", "46177005", "431855005"}
COPD_CODES = {"13645005"}
OSA_CODES = {"73430006"}
IHD_CODES = {"414545008", "22298006", "413844008", "53741008"}
HTN_CODES = {"59621000", "38341003"}
AFIB_CODES = {"49436004"}
STROKE_TIA_CODES = {"230690007", "266257000"}
CANCER_CODES = {"363346000", "254637007"}


# ══════════════════════════════════════════════════════════════════════════════
# 1. ANTIBIOTIC PROPHYLAXIS SELECTOR
# ══════════════════════════════════════════════════════════════════════════════

ANTIBIOTIC_PROTOCOLS = {
    "cardiac": {
        "standard": {"drug": "Cefazolin", "dose": "2g IV (3g if >120kg)", "timing": "Within 60 min before incision", "redose": "Every 4 hours intraoperatively"},
        "penicillin_allergy": {"drug": "Vancomycin", "dose": "15mg/kg IV", "timing": "Begin 60-120 min before incision (infuse over 1-2h)", "redose": "No intraop redose needed"},
        "mrsa_risk": {"drug": "Vancomycin + Cefazolin", "dose": "Vancomycin 15mg/kg + Cefazolin 2g", "timing": "Vancomycin 120min, Cefazolin 60min before incision", "redose": "Cefazolin every 4h"},
    },
    "vascular": {
        "standard": {"drug": "Cefazolin", "dose": "2g IV (3g if >120kg)", "timing": "Within 60 min before incision", "redose": "Every 4 hours"},
        "penicillin_allergy": {"drug": "Clindamycin 900mg IV + Gentamicin 5mg/kg IV", "dose": "As stated", "timing": "Within 60 min before incision", "redose": "Clindamycin every 6h"},
    },
    "abdominal": {
        "standard": {"drug": "Cefazolin + Metronidazole", "dose": "Cefazolin 2g + Metronidazole 500mg IV", "timing": "Within 60 min before incision", "redose": "Cefazolin every 4h, Metronidazole every 8h"},
        "penicillin_allergy": {"drug": "Clindamycin 900mg IV + Gentamicin 5mg/kg IV", "dose": "As stated", "timing": "Within 60 min before incision", "redose": "Clindamycin every 6h"},
    },
    "orthopedic": {
        "standard": {"drug": "Cefazolin", "dose": "2g IV (3g if >120kg)", "timing": "Within 60 min before incision", "redose": "Every 4 hours"},
        "penicillin_allergy": {"drug": "Vancomycin", "dose": "15mg/kg IV", "timing": "Begin 60-120 min before incision", "redose": "No intraop redose needed"},
    },
    "general": {
        "standard": {"drug": "Cefazolin", "dose": "2g IV (3g if >120kg)", "timing": "Within 60 min before incision", "redose": "Every 4 hours"},
        "penicillin_allergy": {"drug": "Clindamycin 900mg IV", "dose": "As stated", "timing": "Within 60 min before incision", "redose": "Every 6 hours"},
    },
}

SURGERY_CATEGORY_MAP = {
    "cardiac": ["cabg", "valve", "cardiac", "heart"],
    "vascular": ["aortic", "aneurysm", "vascular", "carotid", "femoral", "bypass graft"],
    "abdominal": ["colectomy", "gastrectomy", "cholecystectomy", "hernia", "appendectomy", "bowel", "abdominal", "laparotomy", "whipple"],
    "orthopedic": ["arthroplasty", "knee", "hip", "spine", "fracture", "arthroscopy", "orthopedic"],
}


def select_antibiotic_prophylaxis(surgery_type, allergies, patient, observations):
    """Select appropriate surgical antibiotic prophylaxis."""
    surgery_lower = surgery_type.lower()
    allergy_names = _get_allergy_names(allergies)
    has_pcn_allergy = any("penicillin" in a for a in allergy_names)
    bmi = _get_obs_value(observations, "39156-5")
    weight = _get_obs_value(observations, "29463-7")

    # Determine surgery category
    category = "general"
    for cat, keywords in SURGERY_CATEGORY_MAP.items():
        if any(kw in surgery_lower for kw in keywords):
            category = cat
            break

    protocol = ANTIBIOTIC_PROTOCOLS[category]
    if has_pcn_allergy:
        selected = protocol["penicillin_allergy"]
        allergy_note = "Penicillin allergy documented — using alternative regimen."
    else:
        selected = protocol["standard"]
        allergy_note = "No beta-lactam allergy — standard prophylaxis."

    weight_note = ""
    if weight and weight > 120:
        weight_note = f"Patient weight {weight}kg >120kg — use 3g Cefazolin if applicable."
    elif bmi and bmi > 40:
        weight_note = f"BMI {bmi} >40 — consider higher Cefazolin dose (3g)."

    return {
        "surgery_type": surgery_type,
        "surgery_category": category,
        "allergy_status": allergy_note,
        "recommended_regimen": selected,
        "weight_based_adjustment": weight_note or "Standard dosing appropriate.",
        "duration": "Discontinue within 24 hours post-operatively (48h for cardiac surgery).",
        "additional_notes": [
            "Clip (do not shave) surgical site if hair removal needed.",
            "Ensure skin prep with chlorhexidine-alcohol unless contraindicated.",
            "Verify antibiotic administration documented in surgical safety checklist.",
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. BLOOD PRODUCT ANTICIPATION
# ══════════════════════════════════════════════════════════════════════════════

SURGERY_BLOOD_LOSS = {
    "high": ["aortic", "aneurysm", "aaa", "cardiac", "cabg", "liver", "hepatectomy", "whipple", "spine fusion", "hip revision"],
    "moderate": ["colectomy", "gastrectomy", "hip replacement", "knee replacement", "hysterectomy", "prostatectomy"],
    "low": ["hernia", "cholecystectomy", "appendectomy", "arthroscopy", "thyroidectomy", "mastectomy"],
}


def anticipate_blood_products(surgery_type, patient, conditions, medications, observations):
    """Predict blood product needs based on surgery, Hgb, coagulation, and anticoagulation."""
    surgery_lower = surgery_type.lower()
    hgb = _get_obs_value(observations, "718-7")
    inr = _get_obs_value(observations, "34714-6")
    platelets = _get_obs_value(observations, "777-3")

    # Determine expected blood loss category
    blood_loss = "low"
    for category, keywords in SURGERY_BLOOD_LOSS.items():
        if any(kw in surgery_lower for kw in keywords):
            blood_loss = category
            break

    med_names = _get_med_names(medications)
    on_anticoag = any(kw in " ".join(med_names) for kw in ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "enoxaparin"])

    recommendations = []
    crossmatch_units = 0

    # Type & Screen always for moderate/high
    if blood_loss in ("moderate", "high"):
        recommendations.append("Type and Screen REQUIRED")

    # Crossmatch for high-risk
    if blood_loss == "high":
        crossmatch_units = 4
        recommendations.append(f"Crossmatch {crossmatch_units} units pRBC")
    elif blood_loss == "moderate" and hgb and hgb < 12:
        crossmatch_units = 2
        recommendations.append(f"Crossmatch {crossmatch_units} units pRBC (Hgb {hgb} <12)")

    # Anemia assessment
    if hgb:
        if hgb < 7:
            recommendations.append(f"CRITICAL ANEMIA (Hgb {hgb}): Transfuse before surgery. Target Hgb ≥8 for major surgery.")
            crossmatch_units = max(crossmatch_units, 4)
        elif hgb < 8:
            recommendations.append(f"SEVERE ANEMIA (Hgb {hgb}): Strongly consider pre-op transfusion for major surgery.")
            crossmatch_units = max(crossmatch_units, 2)
        elif hgb < 10:
            recommendations.append(f"MODERATE ANEMIA (Hgb {hgb}): Optimize pre-op. Consider iron infusion if time permits. Have blood available.")
            crossmatch_units = max(crossmatch_units, 2)

    # Coagulation
    if inr and inr > 1.5:
        recommendations.append(f"ELEVATED INR ({inr}): Consider FFP or PCC if urgent surgery. Vitamin K for non-urgent.")

    if platelets and platelets < 100:
        recommendations.append(f"THROMBOCYTOPENIA (Plt {platelets}): Consider platelet transfusion. Target >100 for neuraxial, >50 for most surgery.")

    if on_anticoag:
        recommendations.append("Patient on anticoagulation — verify adequate hold time. Have reversal agents available (Vitamin K, PCC for warfarin; Idarucizumab for dabigatran).")

    # Cell saver
    if blood_loss == "high":
        recommendations.append("Consider intraoperative cell salvage (cell saver) for this high-blood-loss procedure.")

    if not recommendations:
        recommendations.append("Low expected blood loss. Type and Screen not routinely required. No blood products anticipated.")

    return {
        "surgery_type": surgery_type,
        "expected_blood_loss": blood_loss,
        "hemoglobin": hgb,
        "inr": inr,
        "platelets": platelets,
        "on_anticoagulation": on_anticoag,
        "crossmatch_units_prbc": crossmatch_units,
        "recommendations": recommendations,
        "periop_note": f"{'⚠ BLOOD PRODUCTS REQUIRED — notify blood bank.' if crossmatch_units > 0 else 'No blood products anticipated.'} Expected blood loss: {blood_loss}.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. FRAILTY ASSESSMENT
# ══════════════════════════════════════════════════════════════════════════════

def assess_frailty(patient, conditions, medications, observations):
    """Assess frailty using modified FRAIL scale + Clinical Frailty indicators."""
    age = _get_age(patient)
    bmi = _get_obs_value(observations, "39156-5")
    hgb = _get_obs_value(observations, "718-7")

    frail_score = 0
    factors = []

    # F - Fatigue (proxy: CHF, anemia, or age >80)
    if _has_condition(conditions, CHF_CODES) or (hgb and hgb < 10):
        frail_score += 1
        factors.append("Fatigue: CHF or anemia suggests reduced energy reserve")
    elif age >= 80:
        frail_score += 1
        factors.append(f"Fatigue: Age {age} ≥80 — increased fatigue risk")

    # R - Resistance (proxy: multiple comorbidities)
    comorbidity_count = sum([
        _has_condition(conditions, CHF_CODES),
        _has_condition(conditions, DM_CODES),
        _has_condition(conditions, CKD_CODES),
        _has_condition(conditions, COPD_CODES),
        _has_condition(conditions, IHD_CODES),
        _has_condition(conditions, STROKE_TIA_CODES),
    ])
    if comorbidity_count >= 3:
        frail_score += 1
        factors.append(f"Resistance: {comorbidity_count} major comorbidities — functional limitation likely")

    # A - Ambulation (proxy: age + BMI + conditions)
    if (age >= 75 and comorbidity_count >= 2) or (bmi and bmi >= 40):
        frail_score += 1
        factors.append("Ambulation: Limited mobility likely based on age, BMI, and comorbidities")

    # I - Illness (>5 comorbidities is a standard threshold)
    total_conditions = len([c for c in conditions if c.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") == "active"])
    if total_conditions >= 5:
        frail_score += 1
        factors.append(f"Illness: {total_conditions} active conditions (≥5 threshold)")

    # L - Loss of weight (proxy: low BMI or albumin if available)
    albumin = _get_obs_value(observations, "1751-7")
    if albumin and albumin < 3.5:
        frail_score += 1
        factors.append(f"Loss of weight: Albumin {albumin} <3.5 suggests malnutrition")
    elif bmi and bmi < 20:
        frail_score += 1
        factors.append(f"Loss of weight: BMI {bmi} <20 suggests underweight/malnutrition")

    # Polypharmacy (additional frailty indicator)
    med_count = len(medications)
    polypharmacy = med_count >= 5

    # Risk level
    if frail_score == 0:
        frailty_level = "robust"
        recommendation = "Patient appears robust. Standard perioperative care appropriate."
    elif frail_score <= 2:
        frailty_level = "pre-frail"
        recommendation = "Pre-frail. Consider prehabilitation (exercise, nutrition optimization) if surgery can be delayed 2-4 weeks."
    else:
        frailty_level = "frail"
        recommendation = "FRAIL patient. Higher risk of post-op complications, prolonged recovery, delirium, and functional decline. Consider: (1) Goals of care discussion, (2) Geriatrics consultation, (3) Prehabilitation program, (4) Modified surgical approach if available."

    return {
        "score_name": "Modified FRAIL Scale",
        "frail_score": frail_score,
        "max_score": 5,
        "frailty_level": frailty_level,
        "factors": factors,
        "additional_indicators": {
            "age": age,
            "total_active_conditions": total_conditions,
            "active_medications": med_count,
            "polypharmacy": polypharmacy,
            "albumin": albumin,
            "bmi": bmi,
            "hemoglobin": hgb,
        },
        "recommendation": recommendation,
        "periop_note": f"FRAIL score {frail_score}/5 ({frailty_level}). {'Standard care.' if frailty_level == 'robust' else 'Consider geriatrics/prehabilitation referral.'}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. PATIENT EDUCATION GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_patient_education(
    surgery_type, surgery_date, patient, medications, allergies, observations,
    med_actions=None,
):
    """Generate plain-language pre-operative instructions for the patient."""
    name = "Unknown"
    names = patient.get("name", [])
    if names:
        n = names[0]
        name = f"{' '.join(n.get('given', []))} {n.get('family', '')}".strip()

    try:
        surg_date = date.fromisoformat(surgery_date[:10])
    except (ValueError, TypeError):
        surg_date = date.today() + timedelta(days=14)

    allergy_names = _get_allergy_names(allergies)
    med_name_list = _get_med_names(medications)
    bmi = _get_obs_value(observations, "39156-5")
    # Build instruction sections
    sections = []

    # Header
    sections.append({
        "title": "Your Pre-Operative Instructions",
        "content": f"Dear {name},\n\nYou are scheduled for {surgery_type} on {surg_date.strftime('%B %d, %Y')}. Please follow these instructions carefully to ensure a safe surgery.",
    })

    # Medications to stop
    meds_to_stop = []
    meds_to_continue = []
    if med_actions:
        for action in med_actions:
            if isinstance(action, dict):
                if action.get("action") in ("hold", "stop"):
                    meds_to_stop.append(f"• {action.get('medication_name', action.get('medication', 'Unknown'))}: {action.get('timing', '')}")
                elif action.get("action") == "continue":
                    meds_to_continue.append(f"• {action.get('medication_name', action.get('medication', 'Unknown'))}")
                elif action.get("action") == "adjust":
                    meds_to_stop.append(f"• {action.get('medication_name', action.get('medication', 'Unknown'))}: {action.get('timing', '')}")

    if meds_to_stop:
        sections.append({
            "title": "Medications to STOP Before Surgery",
            "content": "\n".join(meds_to_stop) + "\n\n⚠ Do NOT stop any medication without your doctor's approval.",
        })

    if meds_to_continue:
        sections.append({
            "title": "Medications to CONTINUE (take with a small sip of water)",
            "content": "\n".join(meds_to_continue),
        })

    # Fasting
    sections.append({
        "title": "Eating and Drinking (Fasting Rules)",
        "content": (
            f"The day BEFORE surgery ({(surg_date - timedelta(days=1)).strftime('%B %d')}):\n"
            "• Eat a normal dinner. Stay well hydrated.\n\n"
            f"The day OF surgery ({surg_date.strftime('%B %d')}):\n"
            "• DO NOT eat any solid food after midnight.\n"
            "• You may drink CLEAR LIQUIDS (water, black coffee, apple juice — NO milk or cream) up to 2 HOURS before your arrival time.\n"
            "• STOP all liquids 2 hours before your scheduled arrival."
        ),
    })

    # What to bring
    bring_items = [
        "• Photo ID and insurance card",
        "• List of all your medications (or bring the bottles)",
        "• Advance directive / living will (if you have one)",
        "• Comfortable, loose-fitting clothes",
        "• Leave jewelry, valuables, and cash at home",
    ]
    if any("cpap" in m or "sleep apnea" in m for m in med_name_list) or bmi and bmi > 35:
        bring_items.append("• Your CPAP machine (for sleep apnea)")

    sections.append({
        "title": "What to Bring to the Hospital",
        "content": "\n".join(bring_items),
    })

    # Day of surgery
    sections.append({
        "title": "Day of Surgery",
        "content": (
            "• Shower with regular soap the morning of surgery.\n"
            "• Do NOT apply lotion, deodorant, or makeup.\n"
            "• Remove all jewelry, piercings, and nail polish.\n"
            "• Wear loose, comfortable clothing.\n"
            "• Arrange for someone to drive you home (you cannot drive after anesthesia)."
        ),
    })

    # Allergies reminder
    if allergy_names:
        sections.append({
            "title": "⚠ Allergy Alert",
            "content": f"Please remind ALL medical staff about your allergies:\n• {', '.join(a.title() for a in allergy_names if a)}\n\nWear your allergy wristband at all times.",
        })

    # Contact
    sections.append({
        "title": "Questions or Concerns?",
        "content": "If you develop a fever, cold, cough, or any new symptoms before your surgery, contact your surgeon's office immediately — your surgery may need to be rescheduled.",
    })

    return {
        "patient_name": name,
        "surgery": surgery_type,
        "surgery_date": surgery_date,
        "sections": sections,
        "language": "English (plain language, 6th grade reading level)",
        "periop_note": "Patient education document generated. Review with patient and provide printed copy.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. SURGICAL SAFETY CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════

def generate_surgical_checklist(
    surgery_type, surgery_date, patient, conditions, medications, allergies,
    observations, risk_data=None, med_actions=None, lab_data=None,
):
    """Generate a WHO-style surgical safety checklist from all assessment data."""
    name = "Unknown"
    names = patient.get("name", [])
    if names:
        n = names[0]
        name = f"{' '.join(n.get('given', []))} {n.get('family', '')}".strip()

    age = _get_age(patient)
    gender = patient.get("gender", "unknown")
    allergy_names = _get_allergy_names(allergies)
    bmi = _get_obs_value(observations, "39156-5")
    hgb = _get_obs_value(observations, "718-7")
    inr = _get_obs_value(observations, "34714-6")
    creatinine = _get_obs_value(observations, "2160-0")

    # SIGN IN (Before induction)
    sign_in = {
        "phase": "SIGN IN (Before Induction of Anesthesia)",
        "items": [
            {"check": "Patient identity confirmed", "value": f"{name}, {age}y {gender}", "status": "verify"},
            {"check": "Procedure and site confirmed", "value": surgery_type, "status": "verify"},
            {"check": "Consent signed", "value": "Verify on chart", "status": "verify"},
            {"check": "Site marked (if applicable)", "value": "Verify", "status": "verify"},
            {"check": "Allergies", "value": ", ".join(a.title() for a in allergy_names) if allergy_names else "NKDA", "status": "alert" if allergy_names else "ok"},
            {"check": "Difficult airway risk", "value": f"BMI {bmi}" if bmi else "Assess", "status": "alert" if bmi and bmi > 35 else "ok"},
            {"check": "Aspiration risk", "value": "Standard NPO protocol", "status": "ok"},
            {"check": "Blood loss risk", "value": f"Hgb {hgb}, INR {inr}" if hgb else "Check labs", "status": "alert" if (hgb and hgb < 10) or (inr and inr > 1.5) else "ok"},
            {"check": "Blood products available", "value": "Type & Screen / Crossmatch", "status": "verify"},
            {"check": "IV access and monitoring", "value": "Confirm", "status": "verify"},
        ],
    }

    # TIME OUT (Before skin incision)
    time_out = {
        "phase": "TIME OUT (Before Skin Incision)",
        "items": [
            {"check": "All team members introduced", "status": "verify"},
            {"check": "Patient, procedure, site confirmed", "value": f"{name}: {surgery_type}", "status": "verify"},
            {"check": "Antibiotic prophylaxis given within last 60 min", "status": "verify"},
            {"check": "Anticipated critical events — Surgeon", "value": "Expected blood loss, critical steps", "status": "discuss"},
            {"check": "Anticipated critical events — Anesthesia", "value": "Airway plan, hemodynamic concerns", "status": "discuss"},
            {"check": "VTE prophylaxis in place", "value": "SCDs / chemoprophylaxis per Caprini score", "status": "verify"},
            {"check": "Essential imaging displayed", "value": "If applicable", "status": "verify"},
        ],
    }

    # SIGN OUT (Before patient leaves OR)
    sign_out = {
        "phase": "SIGN OUT (Before Patient Leaves OR)",
        "items": [
            {"check": "Procedure recorded", "status": "verify"},
            {"check": "Instrument/sponge/needle counts correct", "status": "verify"},
            {"check": "Specimen labeled", "status": "verify"},
            {"check": "Equipment issues documented", "status": "verify"},
            {"check": "Post-op destination confirmed", "value": "ICU / PACU / Floor", "status": "verify"},
            {"check": "Key post-op concerns communicated", "status": "discuss"},
            {"check": "VTE prophylaxis plan post-op", "status": "verify"},
            {"check": "Pain management plan", "status": "verify"},
        ],
    }

    # Flags from assessments
    flags = []
    if allergy_names:
        flags.append(f"ALLERGY: {', '.join(a.title() for a in allergy_names)}")
    if bmi and bmi > 35:
        flags.append(f"DIFFICULT AIRWAY: BMI {bmi}")
    if hgb and hgb < 10:
        flags.append(f"ANEMIA: Hgb {hgb}")
    if inr and inr > 1.5:
        flags.append(f"COAGULOPATHY: INR {inr}")
    if creatinine and creatinine > 2.0:
        flags.append(f"RENAL IMPAIRMENT: Cr {creatinine}")
    if _has_condition(conditions, CHF_CODES):
        flags.append("HEART FAILURE — monitor fluid balance")
    if _has_condition(conditions, OSA_CODES):
        flags.append("OSA — CPAP post-op, monitored bed")

    return {
        "checklist_type": "WHO Surgical Safety Checklist (PreOp Enhanced)",
        "patient": f"{name}, {age}y {gender}",
        "procedure": surgery_type,
        "date": surgery_date,
        "sign_in": sign_in,
        "time_out": time_out,
        "sign_out": sign_out,
        "safety_flags": flags,
        "periop_note": f"Surgical safety checklist generated with {len(flags)} safety flag(s). All items require verbal confirmation by the surgical team.",
    }
