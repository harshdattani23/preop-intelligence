"""Tests for prior operative-note parsing."""

from src.scoring.surgical_history import parse_operative_note

# Sample CABG operative note — matches demo/prior_surgical_report.pdf
CABG_REPORT = """
CLEVELAND MEDICAL CENTER
Department of Surgery — Operative Report
Patient: Burl C. Reinger MRN: MCM-2024-88431
DOB: April 23, 1960 (Age 65) Sex: Male
Date of Surgery: January 22, 2019 Surgeon: Dr. Robert Chen, MD, FACS
Procedure: CABG x3 (Triple Coronary Artery Bypass Graft)

PREOPERATIVE DIAGNOSIS
1. Three-vessel coronary artery disease (LAD 90% stenosis, RCA 85% stenosis, LCx 75% stenosis)
2. Unstable angina, refractory to medical management
3. Type 2 Diabetes Mellitus
4. Essential Hypertension

ANESTHESIA
General endotracheal anesthesia. Difficult intubation encountered — required video laryngoscope
(GlideScope) after failed direct laryngoscopy attempt. Mallampati Class III. BMI 34.8 at time of surgery.
Neck circumference 42cm.

INTRAOPERATIVE DETAILS
Cardiopulmonary bypass time: 142 minutes. Aortic cross-clamp time: 98 minutes.
Estimated blood loss: 850 mL. Transfusions: 2 units packed red blood cells, 2 units fresh frozen plasma.
Intraoperative TEE showed: LV ejection fraction 35%, moderate mitral regurgitation.

POSTOPERATIVE COURSE
Extubated POD #1. Developed postoperative atrial fibrillation on POD #2, rate-controlled with IV amiodarone.
Transient acute kidney injury (creatinine peaked at 2.8 mg/dL POD #3, baseline 1.6).
Discharge medications included: aspirin, metoprolol, warfarin, atorvastatin, lisinopril, furosemide, insulin glargine.

ALLERGIES
Penicillin — ANAPHYLAXIS (documented 2005, required epinephrine). Cefazolin was avoided;
Vancomycin 1.5g IV used for surgical prophylaxis.

IMPORTANT NOTES FOR FUTURE PROCEDURES
1. DIFFICULT AIRWAY: Video laryngoscope required. Failed direct laryngoscopy.
2. PENICILLIN ANAPHYLAXIS: Do NOT use cefazolin or any beta-lactam.
3. POST-BYPASS AKI: Renal-protective strategies recommended for any future surgery.
4. POST-OP AFIB: History of post-surgical atrial fibrillation — high recurrence risk.
5. TRANSFUSION HISTORY: Required 2u pRBC + 2u FFP.

Electronically signed: Robert Chen, MD, FACS
"""


def test_prior_procedure():
    r = parse_operative_note(CABG_REPORT)
    assert r["prior_procedure"]["procedure"].startswith("CABG x3")
    assert r["prior_procedure"]["date"] == "January 22, 2019"


def test_difficult_airway_detected():
    r = parse_operative_note(CABG_REPORT)
    aw = r["airway"]
    assert aw["difficult_airway"] is True
    assert aw["mallampati"] == 3
    assert aw["bmi"] == 34.8
    assert aw["neck_circumference_cm"] == 42
    assert "video laryngoscope" in aw["signals"]
    assert "glidescope" in aw["signals"]
    assert "DIFFICULT AIRWAY" in aw["implication"]


def test_penicillin_anaphylaxis_extracted():
    r = parse_operative_note(CABG_REPORT)
    allergens = [a["allergen"].lower() for a in r["allergies"]]
    assert "penicillin" in allergens
    pen = next(a for a in r["allergies"] if a["allergen"].lower() == "penicillin")
    assert pen["severity"] == "severe"


def test_alternatives_are_not_flagged_as_allergens():
    """Cefazolin and Vancomycin appear in the report as alternatives used BECAUSE
    of the penicillin allergy. They must not be flagged as allergens themselves."""
    r = parse_operative_note(CABG_REPORT)
    allergens = [a["allergen"].lower() for a in r["allergies"]]
    assert "cefazolin" not in allergens
    assert "vancomycin" not in allergens


def test_transfusion_history():
    r = parse_operative_note(CABG_REPORT)
    products = {t["product"]: t["units"] for t in r["transfusion_history"]}
    assert products.get("pRBC") == 2
    assert products.get("FFP") == 2


def test_postop_complications():
    r = parse_operative_note(CABG_REPORT)
    codes = {c["code"] for c in r["postop_complications"]}
    assert "POST_OP_AFIB" in codes
    assert "POST_OP_AKI" in codes


def test_intraop_findings():
    r = parse_operative_note(CABG_REPORT)
    io = r["intraop"]
    assert io["cpb_minutes"] == 142
    assert io["ebl_ml"] == 850
    assert io["intraop_ef_percent"] == 35
    assert io["peak_creatinine"] == 2.8


def test_future_procedure_notes():
    r = parse_operative_note(CABG_REPORT)
    notes = r["future_procedure_notes"]
    assert len(notes) >= 4
    joined = " ".join(notes).lower()
    assert "airway" in joined
    assert "penicillin" in joined


def test_preop_implications_rolled_up():
    r = parse_operative_note(CABG_REPORT)
    impl = r["preop_implications"]
    categories = {i["category"] for i in impl}
    assert "airway" in categories
    assert "allergy" in categories
    assert "postop_history" in categories
    assert "cardiac" in categories  # EF 35%
    assert "renal" in categories    # peak creatinine 2.8

    severities = {i["severity"] for i in impl}
    assert "critical" in severities
    assert "high" in severities


def test_summary_counts():
    r = parse_operative_note(CABG_REPORT)
    s = r["summary"]
    assert s["total_implications"] >= 5
    assert s["critical_count"] >= 2  # airway + penicillin
    assert s["has_prior_findings"] is True


def test_empty_text_returns_empty_findings():
    r = parse_operative_note("")
    assert r["summary"]["total_implications"] == 0
    assert r["summary"]["has_prior_findings"] is False
    assert r["airway"]["difficult_airway"] is False
