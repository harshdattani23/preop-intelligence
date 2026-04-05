"""Advanced clinical scoring systems for perioperative risk assessment.

Scores implemented:
- CHA₂DS₂-VASc: Stroke risk in atrial fibrillation
- MELD: Model for End-Stage Liver Disease severity
- Wells Criteria: DVT probability assessment
- HEART Score: Chest pain risk stratification
- LEMON Airway Assessment: Difficult airway prediction
- Glasgow Coma Scale: Neurological assessment
- P-POSSUM: Surgical mortality/morbidity prediction
"""

from __future__ import annotations

import math
from datetime import date


# SNOMED codes
AFib_CODES = {"49436004"}
CHF_CODES = {"84114007", "42343007"}
HTN_CODES = {"59621000", "38341003"}
DM_CODES = {"44054006", "46635009", "73211009"}
STROKE_TIA_CODES = {"230690007", "266257000", "422504002"}
VASCULAR_CODES = {"53741008", "413844008", "399957001", "840580004"}  # CAD, PAD, aortic plaque
DVT_PE_CODES = {"128053003", "59282003", "706870000", "233935004"}
CANCER_CODES = {"363346000", "254637007", "93761005"}
LIVER_CODES = {"19943007", "235856003", "197321007", "271737000"}  # cirrhosis, chronic liver disease
COPD_CODES = {"13645005"}
CKD_CODES = {"433144002", "46177005"}
IHD_CODES = {"414545008", "22298006", "413844008", "59021001", "53741008"}
OSA_CODES = {"73430006"}


def _has_condition(conditions: list[dict], code_set: set[str]) -> bool:
    for cond in conditions:
        for coding in cond.get("code", {}).get("coding", []):
            if coding.get("code") in code_set:
                return True
    return False


def _get_obs_value(observations: list[dict], loinc_code: str) -> float | None:
    for obs in observations:
        for coding in obs.get("code", {}).get("coding", []):
            if coding.get("code") == loinc_code:
                return obs.get("valueQuantity", {}).get("value")
    return None


def _get_age(patient: dict) -> int:
    bd = patient.get("birthDate", "")
    if not bd:
        return 0
    try:
        bd_date = date.fromisoformat(bd[:10])
    except ValueError:
        return 0
    today = date.today()
    return today.year - bd_date.year - ((today.month, today.day) < (bd_date.month, bd_date.day))


# ── CHA₂DS₂-VASc ─────────────────────────────────────────────────────────────

def _calc_cha2ds2vasc(patient, conditions, observations) -> dict:
    """CHA₂DS₂-VASc stroke risk score for atrial fibrillation patients."""
    age = _get_age(patient)
    gender = patient.get("gender", "").lower()

    score = 0
    factors = []

    if _has_condition(conditions, CHF_CODES):
        score += 1; factors.append("CHF (+1)")
    if _has_condition(conditions, HTN_CODES):
        score += 1; factors.append("Hypertension (+1)")
    if age >= 75:
        score += 2; factors.append(f"Age {age} ≥75 (+2)")
    elif age >= 65:
        score += 1; factors.append(f"Age {age} 65-74 (+1)")
    if _has_condition(conditions, DM_CODES):
        score += 1; factors.append("Diabetes (+1)")
    if _has_condition(conditions, STROKE_TIA_CODES):
        score += 2; factors.append("Prior stroke/TIA (+2)")
    if _has_condition(conditions, VASCULAR_CODES):
        score += 1; factors.append("Vascular disease (+1)")
    if gender == "female":
        score += 1; factors.append("Female sex (+1)")

    if score == 0:
        risk = "low"
        recommendation = "No anticoagulation needed"
        annual_stroke_risk = "0.2%"
    elif score == 1:
        risk = "low-moderate"
        recommendation = "Consider anticoagulation (oral anticoagulant preferred over aspirin)"
        annual_stroke_risk = "0.6%"
    elif score == 2:
        risk = "moderate"
        recommendation = "Anticoagulation recommended"
        annual_stroke_risk = "2.2%"
    else:
        risk = "high"
        risk_map = {3: "3.2%", 4: "4.8%", 5: "7.2%", 6: "9.7%", 7: "11.2%", 8: "10.8%", 9: "12.2%"}
        annual_stroke_risk = risk_map.get(score, ">12%")
        recommendation = "Anticoagulation strongly recommended"

    return {
        "score_name": "CHA₂DS₂-VASc (Stroke Risk in AFib)",
        "score": score, "max_score": 9, "risk_level": risk,
        "annual_stroke_risk": annual_stroke_risk,
        "factors": factors, "recommendation": recommendation,
        "periop_note": "If patient requires anticoagulation interruption for surgery, assess thromboembolic vs bleeding risk to determine bridging strategy.",
    }


# ── MELD Score ────────────────────────────────────────────────────────────────

def _calc_meld(observations) -> dict:
    """MELD score for liver disease severity. Uses MELD-Na formula."""
    bilirubin = _get_obs_value(observations, "1975-2") or _get_obs_value(observations, "42719-5")  # total bilirubin
    creatinine = _get_obs_value(observations, "2160-0")
    inr = _get_obs_value(observations, "34714-6")
    sodium = _get_obs_value(observations, "2951-2")

    missing = []
    if bilirubin is None: missing.append("bilirubin")
    if creatinine is None: missing.append("creatinine")
    if inr is None: missing.append("INR")

    if missing:
        return {
            "score_name": "MELD-Na (Liver Disease Severity)",
            "score": None, "risk_level": "unable_to_calculate",
            "missing_labs": missing,
            "recommendation": f"Cannot calculate MELD — missing: {', '.join(missing)}",
        }

    # Clamp values per MELD formula
    bilirubin = max(bilirubin, 1.0)
    creatinine = min(max(creatinine, 1.0), 4.0)
    inr = max(inr, 1.0)

    meld = 10 * (0.957 * math.log(creatinine) + 0.378 * math.log(bilirubin) + 1.120 * math.log(inr) + 0.643)
    meld = round(min(meld, 40))

    # MELD-Na adjustment
    if sodium is not None:
        sodium = min(max(sodium, 125), 137)
        meld_na = meld + 1.32 * (137 - sodium) - 0.033 * meld * (137 - sodium)
        meld_na = round(min(max(meld_na, 6), 40))
    else:
        meld_na = meld

    if meld_na < 10:
        risk = "low"
        mortality = "<2% 90-day mortality"
    elif meld_na < 20:
        risk = "moderate"
        mortality = "6-20% 90-day mortality"
    elif meld_na < 30:
        risk = "high"
        mortality = "20-50% 90-day mortality"
    else:
        risk = "very_high"
        mortality = ">50% 90-day mortality"

    return {
        "score_name": "MELD-Na (Liver Disease Severity)",
        "score": meld_na, "meld_classic": meld, "max_score": 40,
        "risk_level": risk, "mortality_estimate": mortality,
        "values_used": {"bilirubin": bilirubin, "creatinine": creatinine, "inr": inr, "sodium": sodium},
        "periop_note": f"MELD {meld_na}: {'Hepatology consultation required before elective surgery.' if meld_na >= 15 else 'Acceptable hepatic risk for surgery.'}",
    }


# ── Wells Criteria for DVT ────────────────────────────────────────────────────

def _calc_wells_dvt(patient, conditions, observations) -> dict:
    """Wells criteria for DVT probability assessment."""
    score = 0
    factors = []

    if _has_condition(conditions, CANCER_CODES):
        score += 1; factors.append("Active cancer (+1)")
    # Paralysis/paresis, recently bedridden — check conditions
    if _has_condition(conditions, DVT_PE_CODES):
        score += 1; factors.append("Previous DVT/PE documented (+1)")

    # Surgical/bedridden — assumed if asking about pre-op
    score += 1; factors.append("Recently bedridden / major surgery planned (+1)")

    # Tenderness, swelling, pitting edema, collateral veins — clinical exam findings
    # These require bedside assessment
    factors.append("NOTE: Calf swelling, tenderness, pitting edema require bedside assessment")

    if score <= 0:
        risk = "low"
        dvt_probability = "5%"
        recommendation = "D-dimer testing; if negative, DVT unlikely"
    elif score <= 2:
        risk = "moderate"
        dvt_probability = "17%"
        recommendation = "D-dimer testing or ultrasound"
    else:
        risk = "high"
        dvt_probability = "53%"
        recommendation = "Ultrasound recommended; do not rely on D-dimer alone"

    return {
        "score_name": "Wells Criteria (DVT Probability)",
        "score": score, "risk_level": risk,
        "dvt_probability": dvt_probability,
        "factors": factors, "recommendation": recommendation,
        "periop_note": "Pre-operative DVT screening is critical for patients with elevated Wells score. Consider IPC and pharmacologic prophylaxis.",
    }


# ── HEART Score ───────────────────────────────────────────────────────────────

def _calc_heart(patient, conditions, observations) -> dict:
    """HEART score for chest pain risk stratification."""
    age = _get_age(patient)
    score = 0
    factors = []

    # History — requires clinical assessment
    factors.append("History: Requires clinical assessment of chest pain characteristics")

    # ECG — requires clinical assessment
    factors.append("ECG: Requires bedside ECG interpretation")

    # Age
    if age >= 65:
        score += 2; factors.append(f"Age {age} ≥65 (+2)")
    elif age >= 45:
        score += 1; factors.append(f"Age {age} 45-64 (+1)")

    # Risk factors
    risk_factor_count = sum([
        _has_condition(conditions, HTN_CODES),
        _has_condition(conditions, DM_CODES),
        bool(_get_obs_value(observations, "39156-5") and _get_obs_value(observations, "39156-5") > 30),
        _has_condition(conditions, IHD_CODES),
    ])
    if risk_factor_count >= 3:
        score += 2; factors.append(f"≥3 risk factors ({risk_factor_count}) (+2)")
    elif risk_factor_count >= 1:
        score += 1; factors.append(f"1-2 risk factors ({risk_factor_count}) (+1)")

    # Troponin
    troponin = _get_obs_value(observations, "6598-7") or _get_obs_value(observations, "49563-0")
    if troponin is not None:
        if troponin > 0.1:
            score += 2; factors.append(f"Troponin elevated: {troponin} (+2)")
        elif troponin > 0.04:
            score += 1; factors.append(f"Troponin borderline: {troponin} (+1)")
    else:
        factors.append("Troponin: Not available — order if chest pain present")

    if score <= 3:
        risk = "low"
        recommendation = "Low risk for MACE. Consider discharge with outpatient follow-up."
        mace_risk = "0.9-1.7%"
    elif score <= 6:
        risk = "moderate"
        recommendation = "Moderate risk. Observation, serial troponins, and further workup recommended."
        mace_risk = "12-16.6%"
    else:
        risk = "high"
        recommendation = "High risk for MACE. Admit, cardiology consult, early invasive strategy."
        mace_risk = "50-65%"

    return {
        "score_name": "HEART Score (Chest Pain Risk)",
        "score": score, "max_score": 10, "risk_level": risk,
        "mace_risk_6weeks": mace_risk,
        "factors": factors, "recommendation": recommendation,
        "periop_note": "HEART score ≥4 in pre-op setting warrants cardiology clearance before elective surgery.",
    }


# ── LEMON Airway Assessment ──────────────────────────────────────────────────

def _calc_lemon_airway(patient, conditions, observations) -> dict:
    """LEMON criteria for difficult airway prediction.
    L = Look externally, E = Evaluate 3-3-2, M = Mallampati, O = Obstruction, N = Neck mobility.
    """
    factors = []
    risk_points = 0
    bmi = _get_obs_value(observations, "39156-5")
    neck = _get_obs_value(observations, "56072-2")

    # L - Look externally
    if bmi and bmi >= 35:
        risk_points += 1
        factors.append(f"L - Look: Obesity BMI {bmi} — facial/neck fat deposits may impair ventilation")
    if bmi and bmi >= 40:
        risk_points += 1
        factors.append(f"L - Look: Morbid obesity BMI {bmi} — high risk for difficult mask ventilation")

    # E - Evaluate 3-3-2 rule (requires bedside measurement)
    factors.append("E - Evaluate: 3-3-2 rule requires bedside measurement (mouth opening, hyoid-mentum, thyroid-floor of mouth distances)")

    # M - Mallampati (requires bedside exam)
    factors.append("M - Mallampati: Requires bedside oropharyngeal examination (Class I-IV)")

    # O - Obstruction
    has_osa = _has_condition(conditions, OSA_CODES)
    if has_osa:
        risk_points += 1
        factors.append("O - Obstruction: OSA diagnosed — potential upper airway obstruction")

    # N - Neck mobility
    if neck and neck > 40:
        risk_points += 1
        factors.append(f"N - Neck: Circumference {neck}cm >40cm — reduced neck mobility, difficult laryngoscopy")
    if neck and neck > 43:
        risk_points += 1
        factors.append(f"N - Neck: Circumference {neck}cm >43cm — high probability of difficult intubation")

    if risk_points == 0:
        risk = "low"
        recommendation = "Standard airway management anticipated"
    elif risk_points <= 2:
        risk = "moderate"
        recommendation = "Have video laryngoscope available. Consider supraglottic airway as backup."
    else:
        risk = "high"
        recommendation = "Anticipate difficult airway. Prepare video laryngoscope, fiberoptic scope, and surgical airway equipment. Consider awake fiberoptic intubation."

    return {
        "score_name": "LEMON Airway Assessment",
        "risk_points": risk_points, "risk_level": risk,
        "factors": factors, "recommendation": recommendation,
        "periop_note": "LEMON assessment supplements but does not replace bedside airway examination. Mallampati and 3-3-2 evaluation are mandatory before induction.",
    }


# ── Glasgow Coma Scale ────────────────────────────────────────────────────────

def _calc_gcs(observations) -> dict:
    """Glasgow Coma Scale — checks if documented in FHIR observations."""
    gcs_total = _get_obs_value(observations, "9269-2")  # GCS total
    gcs_eye = _get_obs_value(observations, "9267-6")
    gcs_verbal = _get_obs_value(observations, "9270-0")
    gcs_motor = _get_obs_value(observations, "9268-4")

    if gcs_total is not None:
        total = int(gcs_total)
    elif all(v is not None for v in [gcs_eye, gcs_verbal, gcs_motor]):
        total = int(gcs_eye) + int(gcs_verbal) + int(gcs_motor)
    else:
        return {
            "score_name": "Glasgow Coma Scale (GCS)",
            "score": None, "risk_level": "not_documented",
            "recommendation": "GCS not documented in FHIR records. Perform bedside neurological assessment.",
            "periop_note": "GCS assessment is standard for any patient with altered mental status or neurological conditions prior to surgery.",
        }

    if total >= 13:
        severity = "mild"
    elif total >= 9:
        severity = "moderate"
    else:
        severity = "severe"

    return {
        "score_name": "Glasgow Coma Scale (GCS)",
        "score": total, "max_score": 15, "severity": severity,
        "components": {"eye": gcs_eye, "verbal": gcs_verbal, "motor": gcs_motor},
        "periop_note": f"GCS {total} ({severity}). {'Proceed with standard anesthesia.' if total >= 13 else 'Neurosurgery/neurology consultation required before elective surgery.'}",
    }


# ── P-POSSUM (Portsmouth Physiological and Operative Severity Score) ─────────

def _calc_p_possum(patient, conditions, observations, surgery_type) -> dict:
    """P-POSSUM surgical mortality and morbidity prediction."""
    age = _get_age(patient)

    # Physiological score components
    physio_score = 0
    factors = []

    # Age
    if age <= 60:
        physio_score += 1
    elif age <= 70:
        physio_score += 2; factors.append(f"Age {age} (61-70: +2)")
    else:
        physio_score += 4; factors.append(f"Age {age} (>70: +4)")

    # Cardiac
    has_chf = _has_condition(conditions, CHF_CODES)
    has_ihd = _has_condition(conditions, IHD_CODES)
    if has_chf and has_ihd:
        physio_score += 8; factors.append("Cardiac: CHF + IHD (+8)")
    elif has_chf or has_ihd:
        physio_score += 4; factors.append("Cardiac: CHF or IHD (+4)")
    elif _has_condition(conditions, HTN_CODES):
        physio_score += 2; factors.append("Cardiac: Hypertension (+2)")
    else:
        physio_score += 1

    # Respiratory
    if _has_condition(conditions, COPD_CODES):
        physio_score += 4; factors.append("Respiratory: COPD (+4)")
    else:
        physio_score += 1

    # Blood pressure (systolic)
    systolic = _get_obs_value(observations, "8480-6")
    if systolic:
        if systolic < 90 or systolic > 170:
            physio_score += 4; factors.append(f"BP: Systolic {systolic} (abnormal +4)")
        elif systolic < 100 or systolic > 159:
            physio_score += 2; factors.append(f"BP: Systolic {systolic} (borderline +2)")
        else:
            physio_score += 1

    # Pulse
    hr = _get_obs_value(observations, "8867-4")
    if hr:
        if hr < 40 or hr > 120:
            physio_score += 4; factors.append(f"Pulse: {hr} (abnormal +4)")
        elif hr < 50 or hr > 100:
            physio_score += 2; factors.append(f"Pulse: {hr} (borderline +2)")
        else:
            physio_score += 1

    # Hemoglobin
    hgb = _get_obs_value(observations, "718-7")
    if hgb:
        if hgb < 10 or hgb > 17:
            physio_score += 4; factors.append(f"Hemoglobin: {hgb} (abnormal +4)")
        elif hgb < 11.5 or hgb > 16:
            physio_score += 2; factors.append(f"Hemoglobin: {hgb} (borderline +2)")
        else:
            physio_score += 1

    # WBC
    wbc = _get_obs_value(observations, "6690-2")
    if wbc:
        if wbc < 3 or wbc > 20:
            physio_score += 4; factors.append(f"WBC: {wbc} (abnormal +4)")
        elif wbc < 4 or wbc > 10:
            physio_score += 2; factors.append(f"WBC: {wbc} (borderline +2)")
        else:
            physio_score += 1

    # Sodium
    na = _get_obs_value(observations, "2951-2")
    if na:
        if na < 126 or na > 150:
            physio_score += 4; factors.append(f"Sodium: {na} (abnormal +4)")
        elif na < 131 or na > 145:
            physio_score += 2; factors.append(f"Sodium: {na} (borderline +2)")
        else:
            physio_score += 1

    # Potassium
    k = _get_obs_value(observations, "2823-3")
    if k:
        if k < 2.9 or k > 5.9:
            physio_score += 4; factors.append(f"Potassium: {k} (abnormal +4)")
        elif k < 3.2 or k > 5.4:
            physio_score += 2; factors.append(f"Potassium: {k} (borderline +2)")
        else:
            physio_score += 1

    # Urea/BUN
    bun = _get_obs_value(observations, "3094-0")
    if bun:
        if bun > 40:
            physio_score += 4; factors.append(f"BUN: {bun} (high +4)")
        elif bun > 20:
            physio_score += 2; factors.append(f"BUN: {bun} (borderline +2)")
        else:
            physio_score += 1

    # Operative severity score
    surgery_lower = surgery_type.lower()
    if any(kw in surgery_lower for kw in ["aortic", "aneurysm", "esophagectomy", "pancreatectomy", "whipple"]):
        operative_score = 4
        factors.append(f"Operative severity: Major+ ({surgery_type}) (+4)")
    elif any(kw in surgery_lower for kw in ["abdominal", "thoracic", "vascular", "colectomy", "gastrectomy"]):
        operative_score = 3
        factors.append(f"Operative severity: Major ({surgery_type}) (+3)")
    elif any(kw in surgery_lower for kw in ["hernia", "cholecystectomy", "appendectomy"]):
        operative_score = 2
        factors.append(f"Operative severity: Moderate ({surgery_type}) (+2)")
    else:
        operative_score = 1
        factors.append(f"Operative severity: Minor ({surgery_type}) (+1)")

    # P-POSSUM mortality calculation (logistic regression)
    # ln(R/(1-R)) = -9.065 + (0.1692 × physio) + (0.1550 × operative)
    logit = -9.065 + (0.1692 * physio_score) + (0.1550 * operative_score)
    predicted_mortality = round(1 / (1 + math.exp(-logit)) * 100, 1)
    predicted_mortality = max(predicted_mortality, 0.1)

    # Morbidity calculation
    logit_morb = -5.91 + (0.1692 * physio_score) + (0.1550 * operative_score)
    predicted_morbidity = round(1 / (1 + math.exp(-logit_morb)) * 100, 1)
    predicted_morbidity = min(predicted_morbidity, 99.9)

    if predicted_mortality < 5:
        risk = "low"
    elif predicted_mortality < 15:
        risk = "moderate"
    elif predicted_mortality < 30:
        risk = "high"
    else:
        risk = "very_high"

    return {
        "score_name": "P-POSSUM (Surgical Mortality Prediction)",
        "physiological_score": physio_score,
        "operative_severity_score": operative_score,
        "predicted_mortality_pct": predicted_mortality,
        "predicted_morbidity_pct": predicted_morbidity,
        "risk_level": risk,
        "factors": factors,
        "periop_note": f"P-POSSUM predicts {predicted_mortality}% mortality and {predicted_morbidity}% morbidity. {'Proceed with appropriate monitoring.' if predicted_mortality < 10 else 'Consider ICU bed reservation and discuss risk with patient/family.'}",
    }


