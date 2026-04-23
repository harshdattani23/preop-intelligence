"""A2A tool for parsing prior operative/surgical reports.

The LLM hands in either the report text (extracted from an uploaded PDF that
Gemini can read natively) or base64-encoded PDF bytes. Returns structured
peri-op-relevant findings with implications for the CURRENT pre-op plan.
"""
from __future__ import annotations

import base64
import logging

from google.adk.tools import ToolContext

from src.scoring.surgical_history import extract_pdf_text, parse_operative_note

logger = logging.getLogger(__name__)


def parse_prior_operative_note_a2a(
    report_text: str | None = None,
    pdf_base64: str | None = None,
    tool_context: ToolContext | None = None,
) -> dict:
    """
    Parse a prior operative/surgical report into structured peri-op findings.

    Extracts: difficult-airway history (Mallampati, video laryngoscope, BMI,
    neck circumference), drug allergies with severity, intra-op hemodynamics
    (CPB time, EBL, LVEF, peak creatinine), transfusion history, post-op
    complications (AFib, AKI, pneumonia, VTE, delirium, stroke, MI), and the
    surgeon's notes for future procedures. Each finding is mapped to a
    concrete implication for the CURRENT pre-op plan.

    Args:
        report_text: Plain text of the operative report. Preferred when Gemini
            has already read an uploaded PDF and can pass the text directly.
        pdf_base64: Base64-encoded PDF bytes. Use when raw PDF data is
            available without text extraction.
    """
    logger.info(
        "tool_parse_prior_operative_note text_len=%d pdf_b64_len=%d",
        len(report_text or ""),
        len(pdf_base64 or ""),
    )

    text = ""
    if report_text:
        text = report_text
    elif pdf_base64:
        try:
            text = extract_pdf_text(base64.b64decode(pdf_base64))
        except Exception as e:
            return {"status": "error", "error_message": f"PDF decode failed: {e}"}
    else:
        return {
            "status": "error",
            "error_message": "Must provide report_text or pdf_base64.",
        }

    result = parse_operative_note(text)
    result["status"] = "success"
    return result
