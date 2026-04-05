"""Pre-operative imaging assessment — required imaging checklist and report parsing.

Determines what imaging is required based on surgery type and patient conditions,
checks what's available in the FHIR record, and parses diagnostic report findings.
"""

from __future__ import annotations

from datetime import date

# ── Required imaging by surgery type and risk factors ─────────────────────────

# (surgery_keywords, required_imaging)
SURGERY_IMAGING_REQUIREMENTS = {
    "cardiac": [
        {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 30, "reason": "Baseline pulmonary status, cardiomegaly assessment"},
        {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 30, "reason": "Rhythm assessment, ischemia screening"},
        {"study": "Transthoracic Echocardiogram", "loinc": "42148-7", "max_age_days": 365, "reason": "Ventricular function, valve assessment"},
        {"study": "Coronary Angiogram", "loinc": "18745-0", "max_age_days": 365, "reason": "Coronary anatomy if not recently evaluated"},
    ],
    "vascular": [
        {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 30, "reason": "Pulmonary assessment before major vascular surgery"},
        {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 30, "reason": "Baseline rhythm, ischemia screening"},
        {"study": "Transthoracic Echocardiogram", "loinc": "42148-7", "max_age_days": 365, "reason": "LV function mandatory before aortic surgery"},
        {"study": "CT Angiogram (Aorta)", "loinc": "36813-4", "max_age_days": 90, "reason": "Aortic anatomy and sizing for surgical planning"},
        {"study": "Pulmonary Function Tests", "loinc": "81459-0", "max_age_days": 365, "reason": "Pulmonary reserve assessment for thoraco-abdominal approach"},
    ],
    "abdominal": [
        {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 30, "reason": "Baseline pulmonary status"},
        {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 30, "reason": "Baseline rhythm for patients >50 or with cardiac history"},
    ],
    "orthopedic": [
        {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 90, "reason": "Required if age >60 or significant comorbidities"},
        {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 90, "reason": "Required if age >50 or cardiac history"},
    ],
    "general": [
        {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 90, "reason": "If age >60 or pulmonary/cardiac conditions"},
        {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 90, "reason": "If age >50 or cardiac conditions"},
    ],
}

# Additional imaging triggered by conditions
CONDITION_IMAGING_REQUIREMENTS = {
    "84114007": {"study": "Transthoracic Echocardiogram", "loinc": "42148-7", "max_age_days": 365, "reason": "CHF — LV function assessment required"},
    "42343007": {"study": "Transthoracic Echocardiogram", "loinc": "42148-7", "max_age_days": 365, "reason": "CHF — LV function assessment required"},
    "53741008": {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 30, "reason": "CAD — ischemia screening"},
    "49436004": {"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 30, "reason": "AFib — rate/rhythm assessment"},
    "13645005": {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 30, "reason": "COPD — pulmonary assessment"},
    "73430006": {"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 90, "reason": "OSA — pulmonary/airway assessment"},
}

# Surgery type categorization
SURGERY_CATEGORY_MAP = {
    "cardiac": ["cabg", "valve", "cardiac", "heart"],
    "vascular": ["aortic", "aneurysm", "vascular", "carotid", "femoral", "aaa"],
    "abdominal": ["colectomy", "gastrectomy", "cholecystectomy", "hernia", "appendectomy", "bowel", "abdominal", "whipple"],
    "orthopedic": ["arthroplasty", "knee", "hip", "spine", "fracture", "arthroscopy"],
}

# ── Key findings to extract from diagnostic reports ───────────────────────────

CXR_FINDINGS = {
    "abnormal": [
        "cardiomegaly", "pleural effusion", "pulmonary edema", "consolidation",
        "pneumothorax", "mass", "nodule", "infiltrate", "atelectasis",
        "widened mediastinum", "aortic calcification", "hyperinflation",
    ],
    "normal_indicators": ["normal", "unremarkable", "no acute", "clear lungs", "no infiltrate"],
}

ECG_FINDINGS = {
    "abnormal": [
        "atrial fibrillation", "atrial flutter", "st elevation", "st depression",
        "t wave inversion", "q waves", "left bundle branch block", "lbbb",
        "right bundle branch block", "rbbb", "left ventricular hypertrophy", "lvh",
        "prolonged qt", "first degree av block", "second degree", "third degree",
        "ventricular tachycardia", "bradycardia", "tachycardia",
        "premature ventricular", "pvc", "ischemia", "infarct",
    ],
    "normal_indicators": ["normal sinus rhythm", "nsr", "no acute changes", "within normal"],
}

ECHO_FINDINGS_TO_EXTRACT = [
    "ejection fraction", "ef ", "lvef", "left ventricular",
    "wall motion", "diastolic", "systolic", "valve", "stenosis",
    "regurgitation", "mitral", "aortic", "tricuspid", "pulmonic",
    "pulmonary artery pressure", "pasp", "pericardial effusion",
    "right ventricle", "rv ", "dilated", "hypertrophy",
]


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


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


def _categorize_surgery(surgery_type):
    surgery_lower = surgery_type.lower()
    for cat, keywords in SURGERY_CATEGORY_MAP.items():
        if any(kw in surgery_lower for kw in keywords):
            return cat
    return "general"


def _extract_report_text(report):
    """Extract readable text from a DiagnosticReport."""
    # Try conclusion first
    conclusion = report.get("conclusion", "")
    if conclusion:
        return conclusion

    # Try presentedForm (text attachments)
    for form in report.get("presentedForm", []):
        if form.get("data"):
            import base64
            try:
                return base64.b64decode(form["data"]).decode("utf-8", errors="replace")
            except Exception:
                pass

    # Try text.div
    text = report.get("text", {}).get("div", "")
    if text:
        # Strip HTML tags
        import re
        return re.sub(r"<[^>]+>", "", text).strip()

    return ""


def _parse_findings(text, finding_dict):
    """Check report text against known findings."""
    text_lower = text.lower()

    abnormal_found = []
    for finding in finding_dict.get("abnormal", []):
        if finding in text_lower:
            abnormal_found.append(finding.title())

    is_normal = any(ind in text_lower for ind in finding_dict.get("normal_indicators", []))

    return {
        "is_normal": is_normal and not abnormal_found,
        "abnormal_findings": abnormal_found,
        "raw_text": text[:500],
    }


def assess_preop_imaging(
    surgery_type, surgery_date, patient, conditions,
    diagnostic_reports, imaging_studies,
):
    """Assess pre-operative imaging requirements and parse available reports.

    Args:
        surgery_type: Planned surgery type
        surgery_date: Surgery date YYYY-MM-DD
        patient: FHIR Patient resource
        conditions: List of FHIR Condition resources
        diagnostic_reports: List of FHIR DiagnosticReport resources
        imaging_studies: List of FHIR ImagingStudy resources
    """
    age = _get_age(patient)
    category = _categorize_surgery(surgery_type)

    try:
        ref_date = date.fromisoformat(surgery_date[:10])
    except (ValueError, TypeError):
        ref_date = date.today()

    # Determine required imaging
    required = list(SURGERY_IMAGING_REQUIREMENTS.get(category, SURGERY_IMAGING_REQUIREMENTS["general"]))

    # Add condition-triggered imaging
    condition_codes = set()
    for cond in conditions:
        for coding in cond.get("code", {}).get("coding", []):
            condition_codes.add(coding.get("code", ""))

    for code, imaging in CONDITION_IMAGING_REQUIREMENTS.items():
        if code in condition_codes:
            # Don't duplicate
            if not any(r["loinc"] == imaging["loinc"] for r in required):
                required.append(imaging)

    # Age-based requirements
    if age >= 50 and not any(r["loinc"] == "11524-6" for r in required):
        required.append({"study": "12-Lead ECG", "loinc": "11524-6", "max_age_days": 90, "reason": "Age ≥50 — baseline ECG recommended"})
    if age >= 60 and not any(r["loinc"] == "36643-5" for r in required):
        required.append({"study": "Chest X-ray", "loinc": "36643-5", "max_age_days": 90, "reason": "Age ≥60 — baseline CXR recommended"})

    # Check available imaging
    available = []
    missing = []
    expired = []
    parsed_reports = []

    for req in required:
        loinc = req["loinc"]
        max_age = req["max_age_days"]
        study_name = req["study"]

        # Search diagnostic reports by code
        matching_reports = []
        for report in diagnostic_reports:
            report_code = report.get("code", {})
            for coding in report_code.get("coding", []):
                if coding.get("code") == loinc:
                    matching_reports.append(report)
                    break
            # Also match by display text
            report_text = report_code.get("text", "").lower()
            for coding in report_code.get("coding", []):
                if study_name.lower() in coding.get("display", "").lower():
                    if report not in matching_reports:
                        matching_reports.append(report)

        if not matching_reports:
            missing.append({
                "study": study_name,
                "reason": req["reason"],
                "action": f"Order {study_name} before surgery",
            })
            continue

        # Get most recent
        matching_reports.sort(key=lambda r: r.get("effectiveDateTime", r.get("issued", "")), reverse=True)
        latest = matching_reports[0]
        report_date_str = latest.get("effectiveDateTime", latest.get("issued", ""))
        report_date = _parse_date(report_date_str)
        days_old = (ref_date - report_date).days if report_date else 999

        report_text = _extract_report_text(latest)

        # Determine if expired
        is_expired = days_old > max_age

        # Parse findings
        findings = None
        if "x-ray" in study_name.lower() or "chest" in study_name.lower():
            findings = _parse_findings(report_text, CXR_FINDINGS)
        elif "ecg" in study_name.lower() or "electrocardiog" in study_name.lower():
            findings = _parse_findings(report_text, ECG_FINDINGS)
        elif "echo" in study_name.lower():
            # Extract echo-specific findings
            text_lower = report_text.lower()
            echo_findings = []
            for keyword in ECHO_FINDINGS_TO_EXTRACT:
                if keyword in text_lower:
                    # Extract the sentence containing the keyword
                    idx = text_lower.find(keyword)
                    start = max(0, text_lower.rfind(".", 0, idx) + 1)
                    end = text_lower.find(".", idx)
                    if end == -1:
                        end = min(len(report_text), idx + 100)
                    sentence = report_text[start:end].strip()
                    if sentence:
                        echo_findings.append(sentence)
            findings = {
                "is_normal": not echo_findings,
                "key_findings": echo_findings[:10],
                "raw_text": report_text[:500],
            }

        entry = {
            "study": study_name,
            "date": report_date_str[:10] if report_date_str else "Unknown",
            "days_old": days_old,
            "is_expired": is_expired,
            "status": latest.get("status", "unknown"),
            "findings": findings,
        }

        if is_expired:
            entry["action"] = f"EXPIRED ({days_old} days old, max {max_age}). Repeat {study_name}."
            expired.append(entry)
        else:
            available.append(entry)

        parsed_reports.append(entry)

    # Summary flags
    flags = []
    if missing:
        flags.append(f"MISSING IMAGING: {', '.join(m['study'] for m in missing)}")
    if expired:
        flags.append(f"EXPIRED IMAGING: {', '.join(e['study'] for e in expired)}")

    # Check for abnormal findings
    for report in parsed_reports:
        if report.get("findings") and not report["findings"].get("is_normal", True):
            abnormals = report["findings"].get("abnormal_findings", [])
            if abnormals:
                flags.append(f"ABNORMAL {report['study'].upper()}: {', '.join(abnormals)}")

    imaging_ready = len(missing) == 0 and len(expired) == 0

    return {
        "surgery_type": surgery_type,
        "surgery_category": category,
        "imaging_ready": imaging_ready,
        "required_studies": len(required),
        "available": available,
        "expired": expired,
        "missing": missing,
        "parsed_reports": parsed_reports,
        "flags": flags,
        "periop_note": f"{'All required imaging is current and available.' if imaging_ready else f'{len(missing)} missing and {len(expired)} expired imaging studies must be addressed before surgery.'}",
    }
