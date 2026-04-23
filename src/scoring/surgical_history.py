"""Parse prior operative/surgical reports into structured peri-op-relevant findings.

Takes unstructured text from a prior operative note (typically extracted from a PDF)
and pulls out findings that directly inform the CURRENT pre-op plan:

- Prior procedure and date
- Anesthesia complications (difficult airway, intubation issues, Mallampati, BMI, neck)
- Drug allergies with severity
- Intra-op hemodynamics (CPB time, EBL, LVEF, peak creatinine)
- Transfusion history
- Post-op complications (AFib, AKI, pneumonia, VTE, delirium, stroke, MI)
- Discharge medications
- Surgeon's "notes for future procedures" block when present

Each finding is mapped to a concrete implication for the CURRENT pre-op.
"""
from __future__ import annotations

import re
from io import BytesIO

# ── Regex patterns ────────────────────────────────────────────────────────────

_MALLAMPATI_RX = re.compile(r"mallampati(?:\s+class)?\s+(I{1,4}|IV|[1-4])\b", re.I)
_BMI_RX = re.compile(r"\bBMI\s*:?\s*(\d{1,2}(?:\.\d)?)", re.I)
_NECK_RX = re.compile(r"neck\s+circumference\s*:?\s*(\d{2,3})\s*cm", re.I)
_EF_RX = re.compile(r"(?:LVEF|ejection\s+fraction)\s*:?\s*(\d{2,3})\s*%?", re.I)
_CPB_RX = re.compile(r"cardiopulmonary\s+bypass\s+time\s*:?\s*(\d+)\s*minutes", re.I)
_EBL_RX = re.compile(r"blood\s+loss\s*:?\s*([\d,]+)\s*mL", re.I)
_CREATININE_RX = re.compile(r"creatinine\s+peaked\s+at\s+([\d.]+)", re.I)
_DATE_RX = re.compile(
    r"(?:date\s+of\s+surgery|surgery\s+date|date\s+of\s+procedure)\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
    re.I,
)
_PROCEDURE_RX = re.compile(r"\bprocedure(?:\s+performed)?\s*:\s*([^\n]+)", re.I)
_TRANSFUSION_RX = re.compile(
    r"(\d+)\s+units?\s+((?:packed\s+)?"
    r"(?:red\s+blood\s+cells?|RBC|FFP|fresh\s+frozen\s+plasma|platelets?|cryoprecipitate|pRBCs?))",
    re.I,
)
_FUTURE_NOTES_RX = re.compile(
    r"(?:important\s+notes?\s+for\s+future\s+procedures?|"
    r"notes?\s+for\s+future\s+surger(?:y|ies)|"
    r"recommendations?\s+for\s+future)\s*:?\s*(.+?)"
    r"(?=electronically\s+signed|\bsigned\s*:|\Z)",
    re.I | re.S,
)
_ALLERGY_SECTION_RX = re.compile(
    r"allergies\s*:?\s*\n(.+?)(?=\n\s*[A-Z][A-Z\s]{3,}\n|important\s+notes|\Z)",
    re.I | re.S,
)
_DISCHARGE_MEDS_RX = re.compile(
    r"discharge\s+medications?(?:\s+include[ds]?)?\s*:?\s*([^\.\n]+)",
    re.I,
)

# Difficult-airway text signals
_AIRWAY_SIGNALS = [
    "difficult intubation",
    "difficult airway",
    "failed direct laryngoscopy",
    "video laryngoscope",
    "glidescope",
    "fiberoptic",
    "fibreoptic",
    "awake intubation",
    "two-person mask",
    "cannot intubate",
]

# Post-op complications → (stable code, current-pre-op implication)
_POSTOP_COMPLICATIONS: dict[str, tuple[str, str]] = {
    "atrial fibrillation": (
        "POST_OP_AFIB",
        "Prior post-op AFib — consider prophylactic beta-blocker; plan rate control",
    ),
    "acute kidney injury": (
        "POST_OP_AKI",
        "Prior peri-op AKI — renal-protective strategy (avoid nephrotoxins; maintain MAP >65)",
    ),
    "pneumonia": (
        "POST_OP_PNA",
        "Prior post-op pneumonia — incentive spirometry, early mobilization",
    ),
    "respiratory failure": (
        "POST_OP_RESP",
        "Prior prolonged ventilation — anticipate extended ventilatory support",
    ),
    "sepsis": (
        "POST_OP_SEPSIS",
        "Prior post-op sepsis — heightened infection surveillance",
    ),
    "deep vein thrombosis": (
        "POST_OP_VTE",
        "Prior peri-op VTE — escalated thromboprophylaxis",
    ),
    "pulmonary embolism": (
        "POST_OP_PE",
        "Prior peri-op PE — escalated thromboprophylaxis; consider IVC filter",
    ),
    "wound dehiscence": (
        "WOUND_COMPLICATION",
        "Prior wound healing issue — optimize nutrition and glycemic control",
    ),
    "stroke": (
        "POST_OP_CVA",
        "Prior peri-op stroke — heightened neurologic monitoring",
    ),
    "myocardial infarction": (
        "POST_OP_MI",
        "Prior peri-op MI — cardiology clearance mandatory",
    ),
    "delirium": (
        "POST_OP_DELIRIUM",
        "Prior post-op delirium — minimize benzodiazepines; orient early",
    ),
}

_ALLERGY_SEVERE = [
    "anaphylaxis", "anaphylactic", "epinephrine", "angioedema",
    "stevens-johnson", "dress syndrome",
]
_ALLERGY_MODERATE = ["rash", "hives", "urticaria", "pruritus"]

# Phrases that disqualify a nearby drug from being the allergen
# (e.g., the drug was given as an alternative, not reacted to)
_ALLERGY_NEGATORS = [
    "was avoided", "avoided;", "avoided.", "used for", "was used",
    "alternative", "substitut", "administered", "prophylaxis",
    "was given", "is the proven", "safe alternative",
]

_COMMON_ALLERGENS = [
    "penicillin", "amoxicillin", "cephalosporin", "cefazolin",
    "sulfa", "sulfonamide",
    "nsaid", "aspirin", "ibuprofen", "ketorolac",
    "contrast", "iodine",
    "latex",
    "morphine", "codeine", "vancomycin",
    "shellfish",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _mallampati_to_int(raw: str) -> int | None:
    raw = raw.upper()
    roman = {"I": 1, "II": 2, "III": 3, "IIII": 4, "IV": 4}
    if raw in roman:
        return roman[raw]
    if raw.isdigit():
        n = int(raw)
        return n if 1 <= n <= 4 else None
    return None


def _first_match(rx: re.Pattern, text: str, group: int = 1) -> str | None:
    m = rx.search(text)
    return m.group(group) if m else None


# ── Extractors ────────────────────────────────────────────────────────────────

def _extract_prior_procedure(text: str) -> dict:
    proc = _first_match(_PROCEDURE_RX, text)
    surgery_date = _first_match(_DATE_RX, text)
    return {"procedure": _clean(proc) if proc else None, "date": surgery_date}


def _extract_airway(text: str) -> dict:
    text_lower = text.lower()
    signals = [s for s in _AIRWAY_SIGNALS if s in text_lower]

    mallampati = None
    m = _MALLAMPATI_RX.search(text)
    if m:
        mallampati = _mallampati_to_int(m.group(1))

    bmi: float | None = None
    m = _BMI_RX.search(text)
    if m:
        try:
            bmi = float(m.group(1))
        except ValueError:
            bmi = None

    neck: int | None = None
    m = _NECK_RX.search(text)
    if m:
        try:
            neck = int(m.group(1))
        except ValueError:
            neck = None

    difficult = bool(signals) or bool(
        (mallampati and mallampati >= 3)
        or (neck and neck >= 43)
        or (bmi and bmi >= 40)
    )

    if difficult:
        plan = ["video laryngoscope on standby"]
        if any(s in signals for s in ("fiberoptic", "fibreoptic", "awake intubation", "cannot intubate")):
            plan.append("awake fiberoptic intubation plan")
        if bmi and bmi >= 35:
            plan.append("ramped position for intubation")
        implication = "DIFFICULT AIRWAY — " + "; ".join(plan) + "; notify anesthesia in advance"
    else:
        implication = "No prior airway difficulty documented"

    return {
        "difficult_airway": difficult,
        "signals": signals,
        "mallampati": mallampati,
        "bmi": bmi,
        "neck_circumference_cm": neck,
        "implication": implication,
    }


def _extract_allergies(text: str) -> list[dict]:
    """Detect allergens and severity, preferring text within an ALLERGIES section.

    Severity is based on reaction keywords that appear AFTER the allergen name.
    Drugs that appear with negator phrases (e.g. "Vancomycin was used" or
    "Cefazolin was avoided") are skipped — those are alternatives, not allergens.
    """
    section_m = _ALLERGY_SECTION_RX.search(text)
    scope = section_m.group(1) if section_m else text

    found: list[dict] = []
    seen: set[str] = set()
    for allergen in _COMMON_ALLERGENS:
        if allergen in seen:
            continue
        for m in re.finditer(r"\b" + re.escape(allergen) + r"\b", scope, re.I):
            after = scope[m.end(): m.end() + 150].lower()

            # Skip if the drug is immediately described as a treatment/alternative
            # (short window — otherwise we'd catch downstream mentions of other drugs)
            if any(neg in after[:30] for neg in _ALLERGY_NEGATORS):
                continue

            severity_window = after[:80]
            severity: str | None = None
            if any(kw in severity_window for kw in _ALLERGY_SEVERE):
                severity = "severe"
            elif any(kw in severity_window for kw in _ALLERGY_MODERATE):
                severity = "moderate"

            if severity:
                found.append({
                    "allergen": allergen.title(),
                    "severity": severity,
                    "context": _clean(scope[max(0, m.start() - 10): m.end() + 150])[:200],
                })
                seen.add(allergen)
                break
    return found


def _extract_transfusions(text: str) -> list[dict]:
    results: list[dict] = []
    for m in _TRANSFUSION_RX.finditer(text):
        units = int(m.group(1))
        product_raw = _clean(m.group(2)).lower()
        if "packed" in product_raw or "prbc" in product_raw or "red blood" in product_raw or product_raw == "rbc":
            product = "pRBC"
        elif "plasma" in product_raw or "ffp" in product_raw:
            product = "FFP"
        elif "platelet" in product_raw:
            product = "Platelets"
        elif "cryo" in product_raw:
            product = "Cryoprecipitate"
        else:
            product = product_raw.title()
        results.append({"units": units, "product": product})
    return results


def _extract_postop_complications(text: str) -> list[dict]:
    text_lower = text.lower()
    out: list[dict] = []
    seen: set[str] = set()
    for keyword, (code, implication) in _POSTOP_COMPLICATIONS.items():
        if code in seen:
            continue
        if keyword in text_lower:
            out.append({"complication": keyword.title(), "code": code, "implication": implication})
            seen.add(code)
    return out


def _extract_intraop(text: str) -> dict:
    result: dict = {}

    m = _CPB_RX.search(text)
    if m:
        result["cpb_minutes"] = int(m.group(1))

    m = _EBL_RX.search(text)
    if m:
        try:
            result["ebl_ml"] = int(m.group(1).replace(",", ""))
        except ValueError:
            pass

    m = _EF_RX.search(text)
    if m:
        try:
            ef = int(m.group(1))
            if 5 <= ef <= 85:
                result["intraop_ef_percent"] = ef
        except ValueError:
            pass

    m = _CREATININE_RX.search(text)
    if m:
        try:
            result["peak_creatinine"] = float(m.group(1))
        except ValueError:
            pass

    return result


def _extract_discharge_meds(text: str) -> list[str]:
    m = _DISCHARGE_MEDS_RX.search(text)
    if not m:
        return []
    meds_text = m.group(1)
    meds = [_clean(x) for x in re.split(r",|\band\b", meds_text, flags=re.I)]
    return [x for x in meds if x and 1 < len(x) < 50]


def _extract_future_notes(text: str) -> list[str]:
    m = _FUTURE_NOTES_RX.search(text)
    if not m:
        return []
    block = m.group(1)
    items = re.split(r"\n\s*(?:\d+\.|-|•)\s+", block)
    return [_clean(x)[:500] for x in items if len(_clean(x)) > 10]


# ── Public API ────────────────────────────────────────────────────────────────

def parse_operative_note(text: str) -> dict:
    """Parse an operative-note text into structured peri-op findings.

    Args:
        text: Plain text of the operative report (from PDF extraction or FHIR
              DocumentReference.content.attachment).

    Returns:
        Structured dict — see module docstring for the shape.
    """
    text = text or ""
    prior = _extract_prior_procedure(text)
    airway = _extract_airway(text)
    allergies = _extract_allergies(text)
    transfusions = _extract_transfusions(text)
    postop = _extract_postop_complications(text)
    intraop = _extract_intraop(text)
    discharge_meds = _extract_discharge_meds(text)
    future_notes = _extract_future_notes(text)

    implications: list[dict] = []

    if airway["difficult_airway"]:
        implications.append({
            "category": "airway",
            "severity": "critical",
            "message": airway["implication"],
        })

    for a in allergies:
        if a["severity"] == "severe":
            implications.append({
                "category": "allergy",
                "severity": "critical",
                "message": (
                    f"{a['allergen']} — severe reaction previously documented. "
                    f"AVOID; use alternatives at every care step."
                ),
            })

    for c in postop:
        implications.append({
            "category": "postop_history",
            "severity": "high",
            "message": f"Prior {c['complication']} — {c['implication']}",
        })

    total_prbc = sum(t["units"] for t in transfusions if t["product"] == "pRBC")
    if total_prbc >= 2:
        implications.append({
            "category": "blood_products",
            "severity": "moderate",
            "message": (
                f"Prior surgery required {total_prbc} units pRBC — "
                f"type & crossmatch accordingly; anticipate similar or greater need"
            ),
        })

    ef = intraop.get("intraop_ef_percent")
    if ef and ef < 40:
        implications.append({
            "category": "cardiac",
            "severity": "high",
            "message": (
                f"Prior intraop LVEF {ef}% — obtain CURRENT echocardiogram; "
                f"cardiology clearance"
            ),
        })

    pc = intraop.get("peak_creatinine")
    if pc and pc >= 2.0:
        implications.append({
            "category": "renal",
            "severity": "high",
            "message": (
                f"Prior peri-op AKI (peak creatinine {pc} mg/dL) — "
                f"renal-protective strategy required"
            ),
        })

    return {
        "prior_procedure": prior,
        "airway": airway,
        "allergies": allergies,
        "transfusion_history": transfusions,
        "postop_complications": postop,
        "intraop": intraop,
        "discharge_medications": discharge_meds,
        "future_procedure_notes": future_notes,
        "preop_implications": implications,
        "summary": {
            "total_implications": len(implications),
            "critical_count": sum(1 for i in implications if i["severity"] == "critical"),
            "high_count": sum(1 for i in implications if i["severity"] == "high"),
            "has_prior_findings": bool(
                airway["difficult_airway"] or allergies or postop or transfusions
            ),
        },
    }


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)
