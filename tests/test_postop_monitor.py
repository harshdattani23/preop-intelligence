"""Tests for the PostOp Monitor companion agent's pure-function logic.

The FHIR-bound tool (assess_postop_complications) is not tested here — it
follows the same A2A pattern as the existing preop tools, which are also
exercised live rather than via ToolContext mocks. This file covers the
non-FHIR logic: surgery classification and monitoring-plan generation.
"""

from postop_agent.tools.postop_tools import (
    _classify_surgery,
    recommend_postop_monitoring,
)


def test_classify_thoracic():
    assert _classify_surgery("CABG with valve replacement")["thoracic"] is True
    assert _classify_surgery("right lobectomy")["thoracic"] is True


def test_classify_vascular_aaa():
    cls = _classify_surgery("AAA repair")
    assert cls["vascular"] is True
    assert cls["abdominal"] is True


def test_classify_abdominal():
    cls = _classify_surgery("colectomy")
    assert cls["abdominal"] is True
    assert cls["vascular"] is False


def test_classify_low_acuity():
    cls = _classify_surgery("knee arthroscopy")
    assert cls == {"thoracic": False, "abdominal": False, "vascular": False}


def test_monitoring_high_tier_aaa():
    result = recommend_postop_monitoring("AAA repair", asa_class=3)
    assert result["status"] == "success"
    assert result["acuity_tier"] == "high"
    assert "q1h" in result["monitoring_plan"]["vitals"]
    assert "step-down" in result["monitoring_plan"]["discharge_floor"] or "ICU" in result["monitoring_plan"]["discharge_floor"]


def test_monitoring_moderate_tier_colectomy():
    result = recommend_postop_monitoring("colectomy", asa_class=3)
    assert result["acuity_tier"] == "moderate"
    assert "q4h" in result["monitoring_plan"]["vitals"]


def test_monitoring_low_tier_arthroscopy():
    result = recommend_postop_monitoring("knee arthroscopy", asa_class=2)
    assert result["acuity_tier"] == "low"
    assert result["monitoring_plan"]["telemetry"] == "not required"


def test_monitoring_high_tier_asa4_overrides_low_acuity_surgery():
    result = recommend_postop_monitoring("knee arthroscopy", asa_class=4)
    assert result["acuity_tier"] == "high"


def test_red_flags_always_present():
    result = recommend_postop_monitoring("colectomy", asa_class=3)
    flags = result["red_flags_to_call_attending"]
    assert any("MAP" in f for f in flags)
    assert any("UOP" in f for f in flags)
    assert any("Lactate" in f for f in flags)


def test_red_flags_vascular_specific():
    result = recommend_postop_monitoring("AAA repair", asa_class=3)
    flags = result["red_flags_to_call_attending"]
    assert any("pulse" in f.lower() or "limb" in f.lower() for f in flags)


def test_red_flags_thoracic_specific():
    result = recommend_postop_monitoring("right lobectomy", asa_class=3)
    flags = result["red_flags_to_call_attending"]
    assert any("chest tube" in f.lower() for f in flags)


def test_monitoring_disclaimer_present():
    result = recommend_postop_monitoring("colectomy", asa_class=3)
    assert "clinician review" in result["disclaimer"]


def test_postop_agent_imports():
    """Smoke test: companion agent module loads, root_agent + a2a_app build."""
    from postop_agent.agent import root_agent
    from postop_agent.app import a2a_app

    assert root_agent.name == "postop_monitor_agent"
    assert len(root_agent.tools) == 8
    assert a2a_app is not None
