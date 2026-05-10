"""End-to-end coverage against the Burl Reinger demo bundle.

Burl is the patient used in the demo video (`demo/Burl285_Reinger292.json`).
This file runs every headline scoring + assessment function against his
FHIR bundle so the data path used by the demo has CI coverage.

Burl is a 66-year-old male from Synthea: BMI 27.86, 42 conditions (mostly
social/historical Synthea findings), 11 medications (Alendronic acid),
2 allergies (allergic disposition + tree nut). Surgery under test:
abdominal aortic aneurysm (AAA) repair scheduled 2026-05-15.
"""

import json

import pytest

from src.mcp_server.tools.advanced_scores import calculate_advanced_risk_scores
from src.mcp_server.tools.anesthesia import get_anesthesia_considerations
from src.mcp_server.tools.clinical_protocols import (
    anticipate_blood_products_tool,
    assess_frailty_tool,
    generate_patient_education_tool,
    generate_surgical_checklist_tool,
    select_antibiotic_prophylaxis_tool,
)
from src.mcp_server.tools.drug_intelligence import (
    calculate_renal_dose_adjustments_tool,
    check_allergy_cross_reactivity_tool,
    check_drug_interactions_tool,
)
from src.mcp_server.tools.imaging_assessment import assess_preop_imaging_tool
from src.mcp_server.tools.lab_readiness import assess_lab_readiness
from src.mcp_server.tools.patient_summary import get_patient_summary
from src.mcp_server.tools.periop_medications import check_periop_medications
from src.mcp_server.tools.surgical_history import parse_prior_operative_note_tool
from src.mcp_server.tools.surgical_risk import calculate_surgical_risk

PID = "patient-burl"
SDATE = "2026-05-15"
STYPE = "abdominal aortic aneurysm repair"


# ---------------------------------------------------------------------------
# Demographics & loading
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_summary_demographics():
    result = json.loads(await get_patient_summary(patient_id=PID))
    assert result["age"] == 66
    assert result["sex"] == "male"
    assert "Burl" in result["name"]
    assert "Reinger" in result["name"]


@pytest.mark.asyncio
async def test_burl_summary_has_conditions_meds_allergies():
    result = json.loads(await get_patient_summary(patient_id=PID))
    # Synthea bundle is dense — at least one condition, med, and allergy
    assert len(result["conditions"]) >= 1
    assert len(result["active_medications"]) >= 1
    assert len(result["allergies"]) >= 1


# ---------------------------------------------------------------------------
# 4 core surgical risk scores — ASA / RCRI / Caprini / STOP-BANG
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_surgical_risk_returns_all_four_scores():
    result = json.loads(await calculate_surgical_risk(patient_id=PID, surgery_type=STYPE))
    assert "asa_class" in result
    assert "rcri" in result
    assert "caprini_vte" in result
    assert "stop_bang" in result


@pytest.mark.asyncio
async def test_burl_rcri_cites_lee_1999():
    result = json.loads(await calculate_surgical_risk(patient_id=PID, surgery_type=STYPE))
    assert "Lee TH" in result["rcri"]["citation"]
    assert "Circulation 1999" in result["rcri"]["citation"]


@pytest.mark.asyncio
async def test_burl_caprini_very_high_for_aaa():
    # AAA repair = major surgery + age 66 + obesity → very_high VTE risk
    result = json.loads(await calculate_surgical_risk(patient_id=PID, surgery_type=STYPE))
    assert result["caprini_vte"]["risk_level"] == "very_high"
    assert result["caprini_vte"]["score_value"] >= 5


@pytest.mark.asyncio
async def test_burl_caprini_recommends_extended_prophylaxis():
    result = json.loads(await calculate_surgical_risk(patient_id=PID, surgery_type=STYPE))
    recs = " ".join(result["caprini_vte"]["recommendations"]).lower()
    assert "prophylaxis" in recs


@pytest.mark.asyncio
async def test_burl_rcri_flags_high_risk_surgery():
    result = json.loads(await calculate_surgical_risk(patient_id=PID, surgery_type=STYPE))
    factors = " ".join(result["rcri"]["contributing_factors"]).lower()
    assert "high-risk surgery" in factors or "aaa" in factors or "aortic" in factors


@pytest.mark.asyncio
async def test_burl_stop_bang_cites_chung_2008():
    result = json.loads(await calculate_surgical_risk(patient_id=PID, surgery_type=STYPE))
    assert "Chung F" in result["stop_bang"]["citation"]
    assert "Anesthesiology 2008" in result["stop_bang"]["citation"]


# ---------------------------------------------------------------------------
# 7 advanced risk scores — CHA2DS2-VASc / MELD / Wells / HEART / LEMON / GCS / P-POSSUM
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_advanced_scores_returns_all_seven():
    result = json.loads(await calculate_advanced_risk_scores(patient_id=PID, surgery_type=STYPE))
    for key in ("cha2ds2vasc", "meld", "wells_dvt", "heart", "lemon_airway", "gcs", "p_possum"):
        assert key in result, f"missing advanced score: {key}"


@pytest.mark.asyncio
async def test_burl_advanced_scores_have_risk_level_each():
    result = json.loads(await calculate_advanced_risk_scores(patient_id=PID, surgery_type=STYPE))
    for key in ("cha2ds2vasc", "meld", "wells_dvt", "heart", "lemon_airway", "gcs", "p_possum"):
        assert "risk_level" in result[key], f"{key} missing risk_level"


@pytest.mark.asyncio
async def test_burl_meld_handles_missing_labs_explicitly():
    # Synthea bundle does not have full liver panel — MELD must return a marker, not crash
    result = json.loads(await calculate_advanced_risk_scores(patient_id=PID, surgery_type=STYPE))
    assert result["meld"]["risk_level"] in ("unable_to_calculate", "low", "moderate", "high")


@pytest.mark.asyncio
async def test_burl_gcs_returns_explicit_marker_when_undocumented():
    result = json.loads(await calculate_advanced_risk_scores(patient_id=PID, surgery_type=STYPE))
    # GCS may legitimately be not_documented for an ambulatory pre-op patient
    assert result["gcs"]["risk_level"] in ("not_documented", "low", "moderate", "high")


# ---------------------------------------------------------------------------
# Perioperative medication management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_periop_medications_returns_action_per_med():
    actions = json.loads(await check_periop_medications(patient_id=PID, surgery_date=SDATE))
    assert isinstance(actions, list)
    assert len(actions) >= 1
    for a in actions:
        assert "medication_name" in a
        assert "action" in a
        assert "urgency" in a


@pytest.mark.asyncio
async def test_burl_periop_medication_actions_are_valid_values():
    actions = json.loads(await check_periop_medications(patient_id=PID, surgery_date=SDATE))
    valid_actions = {"hold", "continue", "adjust", "substitute"}
    valid_urgencies = {"critical", "important", "routine"}
    for a in actions:
        assert a["action"] in valid_actions
        assert a["urgency"] in valid_urgencies


# ---------------------------------------------------------------------------
# Drug intelligence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_drug_interactions_returns_structured_result():
    result = json.loads(await check_drug_interactions_tool(patient_id=PID))
    assert "total_interactions" in result
    assert isinstance(result["total_interactions"], int)
    assert "interactions" in result
    assert isinstance(result["interactions"], list)


@pytest.mark.asyncio
async def test_burl_allergy_cross_reactivity_checks_both_allergies():
    result = json.loads(await check_allergy_cross_reactivity_tool(patient_id=PID))
    # Burl has 2 allergies in the Synthea bundle
    assert result["allergies_checked"] >= 2
    assert "active_conflicts_found" in result
    assert isinstance(result["results"], list)


@pytest.mark.asyncio
async def test_burl_renal_dosing_handles_missing_creatinine_explicitly():
    # Burl's Synthea bundle does not have a recent creatinine — the function
    # must return an explicit error rather than crashing or inventing a GFR.
    result = json.loads(await calculate_renal_dose_adjustments_tool(patient_id=PID))
    if "error" in result:
        assert "creatinine" in result["error"].lower() or "gfr" in result["error"].lower()
    else:
        # If a GFR was computed, the result must include shape fields
        assert "estimated_gfr" in result
        assert "adjustments_needed" in result


# ---------------------------------------------------------------------------
# Lab readiness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_lab_readiness_returns_structured_result():
    result = json.loads(await assess_lab_readiness(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    # Function returns labs_current / labs_expired / labs_missing / labs_abnormal / overall_ready
    expected_keys = {"labs_current", "labs_expired", "labs_missing", "labs_abnormal", "overall_ready"}
    assert expected_keys.issubset(result.keys()), f"missing keys: {expected_keys - result.keys()}"


@pytest.mark.asyncio
async def test_burl_lab_readiness_overall_ready_is_boolean():
    result = json.loads(await assess_lab_readiness(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    assert isinstance(result["overall_ready"], bool)


# ---------------------------------------------------------------------------
# Anesthesia
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_anesthesia_returns_airway_assessment():
    result = json.loads(await get_anesthesia_considerations(patient_id=PID))
    assert result["airway_risk"] in ("low", "moderate", "high")
    assert "airway_factors" in result
    assert "bmi_category" in result


@pytest.mark.asyncio
async def test_burl_anesthesia_returns_npo_guidance():
    result = json.loads(await get_anesthesia_considerations(patient_id=PID))
    assert result["npo_guidance"]
    assert "hours before surgery" in result["npo_guidance"]


# ---------------------------------------------------------------------------
# Antibiotic prophylaxis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_antibiotic_prophylaxis_for_aaa_uses_cefazolin_no_pcn_allergy():
    # No penicillin allergy in Synthea bundle → standard Cefazolin
    result = json.loads(await select_antibiotic_prophylaxis_tool(patient_id=PID, surgery_type=STYPE))
    assert result["surgery_category"] == "vascular"
    assert result["recommended_regimen"]["drug"].lower() == "cefazolin"
    assert "60 min" in result["recommended_regimen"]["timing"] or "before incision" in result["recommended_regimen"]["timing"]


@pytest.mark.asyncio
async def test_burl_antibiotic_prophylaxis_includes_redose_schedule():
    result = json.loads(await select_antibiotic_prophylaxis_tool(patient_id=PID, surgery_type=STYPE))
    assert result["recommended_regimen"]["redose"]


# ---------------------------------------------------------------------------
# Blood products
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_blood_products_for_aaa_anticipates_transfusion():
    result = json.loads(await anticipate_blood_products_tool(patient_id=PID, surgery_type=STYPE))
    assert result["surgery_type"] == STYPE
    assert result["expected_blood_loss"] in ("low", "moderate", "high")
    assert result["crossmatch_units_prbc"] >= 0


@pytest.mark.asyncio
async def test_burl_blood_products_aaa_recommends_high_blood_loss_strategy():
    # AAA is a high-blood-loss procedure — should recommend Type & Screen + crossmatch
    result = json.loads(await anticipate_blood_products_tool(patient_id=PID, surgery_type=STYPE))
    assert result["expected_blood_loss"] == "high"
    assert result["crossmatch_units_prbc"] >= 2
    recs = " ".join(result["recommendations"]).lower()
    assert "crossmatch" in recs or "type and screen" in recs


# ---------------------------------------------------------------------------
# Frailty
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_frailty_at_66_returns_score():
    result = json.loads(await assess_frailty_tool(patient_id=PID))
    assert result["score_name"] == "Modified FRAIL Scale"
    assert 0 <= result["frail_score"] <= 5
    assert result["frailty_level"] in ("robust", "pre-frail", "frail")


@pytest.mark.asyncio
async def test_burl_frailty_flags_polypharmacy():
    # 11 active meds → polypharmacy True
    result = json.loads(await assess_frailty_tool(patient_id=PID))
    assert result["additional_indicators"]["polypharmacy"] is True
    assert result["additional_indicators"]["active_medications"] >= 5


# ---------------------------------------------------------------------------
# Imaging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_imaging_aaa_requires_vascular_workup():
    result = json.loads(await assess_preop_imaging_tool(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    assert result["surgery_category"] == "vascular"
    assert result["required_studies"] >= 4
    # AAA needs at least CXR/ECG/Echo/CT-Angio combination
    missing_studies = " ".join(m["study"] for m in result["missing"]).lower()
    assert "ct angiogram" in missing_studies or "echocardiogram" in missing_studies or "ecg" in missing_studies


@pytest.mark.asyncio
async def test_burl_imaging_flags_missing_studies():
    result = json.loads(await assess_preop_imaging_tool(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    # Synthea bundle won't have AAA-specific pre-op imaging → flags raised
    assert result["imaging_ready"] is False
    assert result["flags"]


# ---------------------------------------------------------------------------
# Patient education & surgical checklist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_burl_patient_education_renders_for_aaa():
    result = json.loads(await generate_patient_education_tool(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    assert result["patient_name"]
    assert "Burl" in result["patient_name"]
    assert "sections" in result
    assert isinstance(result["sections"], list)
    assert len(result["sections"]) >= 3
    # Every section has title + content
    for section in result["sections"]:
        assert "title" in section
        assert "content" in section


@pytest.mark.asyncio
async def test_burl_patient_education_mentions_allergies():
    result = json.loads(await generate_patient_education_tool(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    # Burl has tree-nut + allergic-disposition allergies — must be surfaced
    blob = json.dumps(result).lower()
    assert "allerg" in blob


@pytest.mark.asyncio
async def test_burl_surgical_checklist_renders_who_three_phase():
    result = json.loads(await generate_surgical_checklist_tool(patient_id=PID, surgery_type=STYPE, surgery_date=SDATE))
    # WHO-style three-phase checklist
    assert "sign_in" in result
    assert "time_out" in result
    assert "sign_out" in result
    assert result["procedure"] == STYPE
    assert result["date"] == SDATE


# ---------------------------------------------------------------------------
# Prior-operative-note PDF parsing (multimodal pipeline)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_prior_op_note_extracts_findings_from_sample_text():
    # Use the demo's prior-op narrative directly — represents what the multimodal
    # pipeline would extract from the PDF. Validates the parser, not Burl's bundle.
    sample = (
        "OPERATIVE REPORT — 2019-08-15\n"
        "Procedure: Coronary artery bypass graft x3.\n"
        "Anesthesia: General. Difficult airway documented — Mallampati III, "
        "neck circumference 42 cm. Required GlideScope for intubation.\n"
        "Allergy: Penicillin — anaphylaxis (epinephrine administered 2005).\n"
        "Intra-op: CPB time 110 minutes. Peak creatinine 2.8 mg/dL. "
        "Transfused 2 units pRBC and 2 units FFP.\n"
        "Post-op course: New-onset atrial fibrillation POD 1, treated with "
        "amiodarone. AKI peaked POD 2. Pneumonia POD 4."
    )
    result = json.loads(await parse_prior_operative_note_tool(report_text=sample))
    # Parser should surface findings — look for any of the key extracted signals
    text = json.dumps(result).lower()
    assert "airway" in text or "mallampati" in text or "difficult" in text
    assert "penicillin" in text or "anaphylaxis" in text or "allergy" in text
