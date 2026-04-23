"""MCP tool for parsing prior operative/surgical reports.

Accepts raw report text, base64-encoded PDF, or a FHIR DocumentReference ID.
Extracts peri-op-relevant findings (difficult airway, allergies, post-op
complications, transfusion history, intra-op hemodynamics) and maps each to
a specific implication for the CURRENT pre-op plan.
"""
from __future__ import annotations

import base64
import json
from typing import Annotated

from src.mcp_server.app import mcp
from src.mcp_server.fhir_client import FHIRClient
from src.scoring.surgical_history import extract_pdf_text, parse_operative_note


@mcp.tool(
    name="parse_prior_operative_note",
    description=(
        "Parse a prior operative report and extract findings that inform the "
        "CURRENT pre-op plan: difficult-airway history (Mallampati, video "
        "laryngoscope, BMI, neck), drug allergies with severity, intra-op "
        "hemodynamics (CPB time, EBL, LVEF, peak creatinine), transfusion "
        "history, post-op complications (AFib, AKI, pneumonia, VTE, delirium, "
        "stroke, MI), and the surgeon's notes for future procedures. "
        "Each finding is mapped to a concrete pre-op implication with severity. "
        "Accepts: raw report text, base64-encoded PDF, or a FHIR "
        "DocumentReference ID."
    ),
)
async def parse_prior_operative_note_tool(
    report_text: Annotated[
        str | None,
        "Plain text of the operative report (preferred for LLM-extracted content).",
    ] = None,
    pdf_base64: Annotated[
        str | None,
        "Base64-encoded PDF bytes of the operative report.",
    ] = None,
    document_reference_id: Annotated[
        str | None,
        "FHIR DocumentReference ID containing the operative note.",
    ] = None,
) -> str:
    text = ""

    if report_text:
        text = report_text
    elif pdf_base64:
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
            text = extract_pdf_text(pdf_bytes)
        except Exception as e:
            return f"Error decoding PDF: {e}"
    elif document_reference_id:
        client, _ = FHIRClient.from_headers()
        doc_ref = None
        if client.base_url:
            doc_ref = await client._fetch(
                f"{client.base_url}/DocumentReference/{document_reference_id}"
            )
        if not doc_ref:
            return f"Error: DocumentReference {document_reference_id} not found"

        for content in doc_ref.get("content", []):
            attachment = content.get("attachment", {})
            data = attachment.get("data")
            content_type = attachment.get("contentType", "")
            if not data:
                continue
            try:
                raw = base64.b64decode(data)
            except Exception:
                continue
            if "pdf" in content_type.lower():
                try:
                    text = extract_pdf_text(raw)
                except Exception as e:
                    return f"Error extracting PDF from DocumentReference: {e}"
            else:
                text = raw.decode("utf-8", errors="replace")
            if text:
                break

        if not text:
            return "Error: Could not extract content from DocumentReference"
    else:
        return (
            "Error: Must provide one of report_text, pdf_base64, "
            "or document_reference_id."
        )

    result = parse_operative_note(text)
    return json.dumps(result, indent=2)
