"""Edge-case stress tests for the scoring + protocol layer.

These exercise pathological inputs we expect to encounter in the wild:
empty FHIR records, extreme lab values, missing demographics, surgery
types not in the keyword lists, and the boundary cases that catch off-
by-one errors. Pure-function tests; no FHIR / ToolContext dependency.
"""

from __future__ import annotations

from src.scoring.calculators import (
    _calc_cha2ds2vasc,
    _calc_gcs,
    _calc_heart,
    _calc_lemon_airway,
    _calc_meld,
    _calc_p_possum,
    _calc_wells_dvt,
    _get_age,
)
from src.scoring.clinical_protocols import (
    select_antibiotic_prophylaxis,
)
from postop_agent.tools.postop_tools import (
    _classify_surgery,
    recommend_postop_monitoring,
)


def _patient(birth: str = "1960-01-01", gender: str = "male") -> dict:
    return {"birthDate": birth, "gender": gender}


def _obs(loinc: str, value: float) -> dict:
    return {"code": {"coding": [{"code": loinc}]}, "valueQuantity": {"value": value}}


def _condition(code: str) -> dict:
    return {"code": {"coding": [{"code": code}]}}


# ── Demographics edge cases ──────────────────────────────────────────────────

def test_age_missing_birthdate_returns_zero():
    assert _get_age({}) == 0


def test_age_malformed_birthdate_returns_zero():
    assert _get_age({"birthDate": "not-a-date"}) == 0


def test_age_centenarian_no_overflow():
    age = _get_age({"birthDate": "1920-06-15"})
    assert age >= 100
    assert age < 120


def test_age_pediatric_calculates_correctly():
    age = _get_age({"birthDate": "2015-01-01"})
    assert 10 <= age <= 12


# ── CHA2DS2-VASc edge cases ──────────────────────────────────────────────────

def test_cha2ds2vasc_empty_inputs_returns_zero_for_young_male():
    """Young male with no comorbidities should score 0."""
    result = _calc_cha2ds2vasc(_patient(birth="1990-01-01", gender="male"), [], [])
    assert result["score"] == 0
    assert result["risk_level"] == "low"
    assert "citation" in result and result["citation"]


def test_cha2ds2vasc_young_female_gets_one_point_for_sex():
    result = _calc_cha2ds2vasc(_patient(birth="1990-01-01", gender="female"), [], [])
    assert result["score"] == 1


def test_cha2ds2vasc_max_score_capped_handles_all_factors():
    """Old female with every risk factor — should land at high risk."""
    patient = _patient(birth="1935-01-01", gender="female")
    conditions = [
        _condition("84114007"),  # CHF
        _condition("59621000"),  # HTN
        _condition("44054006"),  # DM
        _condition("230690007"),  # stroke
        _condition("53741008"),  # vascular (CAD)
    ]
    result = _calc_cha2ds2vasc(patient, conditions, [])
    assert result["score"] >= 8
    assert result["risk_level"] == "high"


# ── MELD-Na edge cases ───────────────────────────────────────────────────────

def test_meld_no_labs_returns_unable_to_calculate():
    result = _calc_meld([])
    assert result["score"] is None
    assert result["risk_level"] == "unable_to_calculate"
    assert set(result["missing_labs"]) == {"bilirubin", "creatinine", "INR"}


def test_meld_extreme_values_clamped_to_max():
    """End-stage liver — Cr 8, INR 5, bili 30, hyponatremic. Should saturate."""
    obs = [
        _obs("2160-0", 8.0),
        _obs("34714-6", 5.0),
        _obs("1975-2", 30.0),
        _obs("2951-2", 120.0),
    ]
    result = _calc_meld(obs)
    assert result["score"] is not None
    assert result["score"] >= 30
    assert result["score"] <= 40
    assert result["risk_level"] in ("high", "very_high")


def test_meld_missing_sodium_falls_back_to_classic():
    obs = [
        _obs("2160-0", 1.5),
        _obs("34714-6", 1.2),
        _obs("1975-2", 1.0),
    ]
    result = _calc_meld(obs)
    assert result["score"] is not None
    assert result["score"] == result["meld_classic"]


# ── Wells DVT edge cases ─────────────────────────────────────────────────────

def test_wells_dvt_no_factors_returns_moderate_due_to_periop_baseline():
    """Wells auto-adds +1 for 'major surgery planned' since this is a pre-op
    tool. So a patient with no other risk factors lands at 'moderate' (not
    'low') — that's the intended pre-op screening behavior."""
    result = _calc_wells_dvt(_patient(), [], [])
    assert result["risk_level"] == "moderate"
    assert result["score"] == 1


# ── HEART score edge cases ───────────────────────────────────────────────────

def test_heart_no_data_returns_structured_result():
    result = _calc_heart(_patient(), [], [])
    assert "score" in result
    assert "risk_level" in result


# ── LEMON airway edge cases ──────────────────────────────────────────────────

def test_lemon_no_observations_returns_low_risk():
    result = _calc_lemon_airway(_patient(), [], [])
    assert result["risk_level"] == "low"


def test_lemon_obese_with_osa_returns_elevated():
    patient = _patient()
    conditions = [_condition("73430006")]  # OSA
    obs = [_obs("39156-5", 42.0), _obs("56072-2", 45.0)]  # BMI 42, neck 45
    result = _calc_lemon_airway(patient, conditions, obs)
    assert result["risk_level"] in ("moderate", "high")


# ── GCS edge cases ───────────────────────────────────────────────────────────

def test_gcs_not_documented_returns_explicit_marker():
    result = _calc_gcs([])
    assert result["score"] is None
    assert result["risk_level"] == "not_documented"


def test_gcs_components_summed_when_total_missing():
    obs = [
        _obs("9267-6", 4),  # eye
        _obs("9270-0", 5),  # verbal
        _obs("9268-4", 6),  # motor
    ]
    result = _calc_gcs(obs)
    assert result["score"] == 15
    assert result["severity"] == "mild"


# ── P-POSSUM edge cases ──────────────────────────────────────────────────────

def test_possum_minor_unknown_surgery_falls_back_to_minor():
    """Surgery type not in any keyword list — should default to minor."""
    result = _calc_p_possum(_patient(), [], [], "rare_zebra_procedure_xyz")
    assert result["operative_severity_score"] == 1
    assert result["predicted_mortality_pct"] >= 0.0


def test_possum_extreme_physiology_yields_high_mortality():
    """Old, CHF + IHD + COPD, every lab abnormal, AAA repair."""
    patient = _patient(birth="1935-01-01")
    conditions = [
        _condition("84114007"),  # CHF
        _condition("414545008"),  # IHD
        _condition("13645005"),  # COPD
    ]
    obs = [
        _obs("8480-6", 80),    # SBP low
        _obs("8867-4", 130),   # HR high
        _obs("718-7", 8.0),    # Hgb low
        _obs("6690-2", 22.0),  # WBC high
        _obs("2951-2", 125),   # Na low
        _obs("2823-3", 6.2),   # K high
        _obs("3094-0", 50),    # BUN high
    ]
    result = _calc_p_possum(patient, conditions, obs, "open AAA repair")
    assert result["predicted_mortality_pct"] >= 15
    assert result["risk_level"] in ("high", "very_high")


def test_possum_healthy_minor_surgery_yields_low_mortality():
    obs = [
        _obs("8480-6", 120), _obs("8867-4", 70), _obs("718-7", 14.0),
        _obs("6690-2", 7.0), _obs("2951-2", 140), _obs("2823-3", 4.2),
        _obs("3094-0", 12),
    ]
    result = _calc_p_possum(_patient(birth="1985-01-01"), [], obs, "knee arthroscopy")
    assert result["predicted_mortality_pct"] < 5
    assert result["risk_level"] == "low"


# ── Antibiotic prophylaxis edge cases ────────────────────────────────────────

def test_antibiotic_unknown_surgery_falls_back_to_general():
    result = select_antibiotic_prophylaxis("unspecified_procedure_zzz", [], _patient(), [])
    assert result["surgery_category"] == "general"
    assert "recommended_regimen" in result
    assert "citation" in result


def test_antibiotic_pcn_anaphylaxis_picks_alternative():
    allergies = [{"code": {"coding": [{"display": "penicillin"}]}}]
    result = select_antibiotic_prophylaxis("vascular surgery", allergies, _patient(), [])
    regimen = result["recommended_regimen"]
    regimen_str = str(regimen).lower()
    assert "cefazolin" not in regimen_str
    assert "penicillin allergy documented" in result["allergy_status"].lower()


# ── PostOp monitor edge cases ────────────────────────────────────────────────

def test_postop_classify_unknown_surgery_returns_all_false():
    cls = _classify_surgery("rare_zebra_procedure_xyz")
    assert cls == {"thoracic": False, "abdominal": False, "vascular": False}


def test_postop_recommend_handles_unknown_surgery_low_asa():
    result = recommend_postop_monitoring("rare_zebra_procedure_xyz", asa_class=2)
    assert result["acuity_tier"] == "low"
    assert result["status"] == "success"


def test_postop_recommend_asa5_always_high_tier():
    result = recommend_postop_monitoring("knee arthroscopy", asa_class=5)
    assert result["acuity_tier"] == "high"


def test_postop_recommend_red_flags_never_empty():
    """Every monitoring plan must include red-flag thresholds."""
    for surgery in ["AAA repair", "colectomy", "knee arthroscopy", "lobectomy"]:
        for asa in [1, 3, 5]:
            result = recommend_postop_monitoring(surgery, asa_class=asa)
            assert len(result["red_flags_to_call_attending"]) >= 4
