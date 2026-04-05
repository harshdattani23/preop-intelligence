"""Drug intelligence engine — interactions, renal dosing, allergy cross-reactivity.

All functions are pure logic operating on FHIR resource dicts.
No framework dependencies (MCP/ADK).
"""

from __future__ import annotations



# ══════════════════════════════════════════════════════════════════════════════
# 1. DRUG-DRUG INTERACTION DATABASE
# ══════════════════════════════════════════════════════════════════════════════

# Each interaction: (drug_a_keywords, drug_b_keywords, severity, mechanism, clinical_effect, recommendation)
INTERACTION_DB = [
    # Anticoagulant interactions
    (["warfarin"], ["aspirin"], "moderate",
     "Additive antiplatelet + anticoagulant effect",
     "Increased bleeding risk. GI hemorrhage risk elevated.",
     "Monitor INR closely. Consider PPI for GI protection. Assess if dual therapy is warranted."),

    (["warfarin"], ["metoprolol"], "mild",
     "Metoprolol may slightly increase warfarin levels via CYP2C9",
     "Minor INR increase possible",
     "Monitor INR when starting/stopping metoprolol. Usually no dose adjustment needed."),

    (["warfarin"], ["lisinopril"], "mild",
     "ACE inhibitors may have minor interaction with warfarin",
     "Rarely clinically significant",
     "Routine INR monitoring sufficient."),

    (["warfarin"], ["furosemide"], "moderate",
     "Furosemide may displace warfarin from protein binding; dehydration concentrates warfarin",
     "Transient INR increase possible, especially with dehydration",
     "Monitor INR and hydration status. Adjust warfarin if significant fluid shifts."),

    (["warfarin"], ["amiodarone"], "severe",
     "Amiodarone inhibits CYP2C9 and CYP3A4, dramatically increasing warfarin levels",
     "INR may double or triple. Bleeding risk very high.",
     "Reduce warfarin dose by 30-50% when starting amiodarone. Monitor INR weekly for 6-8 weeks."),

    (["warfarin"], ["nsaid", "ibuprofen", "naproxen", "diclofenac", "ketorolac"], "severe",
     "NSAIDs inhibit platelet function + GI mucosal protection",
     "Major GI bleeding risk. Synergistic bleeding effect.",
     "AVOID combination if possible. If necessary, use lowest NSAID dose + PPI."),

    (["warfarin"], ["st. john", "st john"], "severe",
     "St. John's Wort induces CYP3A4 and CYP2C9, reducing warfarin levels",
     "Sub-therapeutic INR. Thromboembolic risk.",
     "CONTRAINDICATED. Discontinue St. John's Wort immediately."),

    # Apixaban interactions
    (["apixaban"], ["aspirin"], "moderate",
     "Additive bleeding risk",
     "Increased major bleeding events",
     "Assess necessity of dual therapy. Add PPI if continuing both."),

    (["apixaban"], ["ketoconazole", "itraconazole", "ritonavir"], "severe",
     "Strong CYP3A4 + P-gp inhibitors increase apixaban levels 2x",
     "Significantly increased bleeding risk",
     "Reduce apixaban dose by 50% or avoid combination."),

    # ACE inhibitor + potassium-sparing
    (["lisinopril", "enalapril", "losartan", "valsartan"], ["spironolactone", "eplerenone", "amiloride"], "severe",
     "Both cause potassium retention",
     "Life-threatening hyperkalemia risk",
     "Monitor potassium closely (within 1 week). Avoid if K+ >5.0."),

    (["lisinopril", "enalapril"], ["potassium"], "moderate",
     "ACE inhibitors reduce aldosterone, retaining potassium",
     "Hyperkalemia risk",
     "Monitor potassium. Avoid potassium supplements unless K+ <3.5."),

    # Metformin interactions
    (["metformin"], ["contrast", "iodinated"], "severe",
     "IV contrast media may cause lactic acidosis in metformin users",
     "Risk of metformin-associated lactic acidosis (MALA)",
     "Hold metformin 48h before and after IV contrast. Check renal function before resuming."),

    (["metformin"], ["furosemide"], "mild",
     "Furosemide may increase metformin levels by reducing renal clearance",
     "Slight increase in metformin exposure",
     "Monitor blood glucose. Usually no adjustment needed."),

    # Insulin interactions
    (["insulin"], ["metoprolol", "atenolol", "propranolol"], "moderate",
     "Beta-blockers mask hypoglycemia symptoms (tachycardia, tremor)",
     "Delayed recognition of hypoglycemia. Prolonged hypoglycemic episodes.",
     "Educate patient on non-adrenergic hypoglycemia symptoms (sweating, hunger). Monitor glucose closely perioperatively."),

    # Triple whammy (ACEi/ARB + diuretic + NSAID)
    (["lisinopril", "enalapril", "losartan"], ["furosemide", "hydrochlorothiazide"], "moderate",
     "ACE inhibitor + diuretic combination",
     "Risk of hypotension and acute kidney injury, especially perioperatively",
     "Hold both morning of surgery. Monitor BP and renal function post-op."),

    # Serotonin syndrome risk
    (["tramadol", "fentanyl", "meperidine"], ["ssri", "sertraline", "fluoxetine", "paroxetine", "citalopram"], "severe",
     "Serotonergic opioids + SSRIs increase serotonin levels",
     "Serotonin syndrome: agitation, hyperthermia, clonus, rigidity",
     "Avoid combination if possible. Monitor for serotonin syndrome signs perioperatively."),

    # QT prolongation
    (["amiodarone"], ["ondansetron", "zofran"], "moderate",
     "Both prolong QT interval",
     "Risk of Torsades de Pointes",
     "Use alternative antiemetic (dexamethasone). If ondansetron necessary, obtain baseline ECG."),

    # Statin + certain drugs
    (["atorvastatin", "simvastatin"], ["amiodarone"], "moderate",
     "Amiodarone inhibits CYP3A4, increasing statin levels",
     "Increased risk of rhabdomyolysis",
     "Limit simvastatin to 20mg/day with amiodarone. Atorvastatin generally safer."),

    # Digoxin + amiodarone
    (["digoxin"], ["amiodarone"], "severe",
     "Amiodarone increases digoxin levels by 70-100%",
     "Digoxin toxicity: nausea, visual changes, arrhythmias",
     "Reduce digoxin dose by 50% when starting amiodarone. Monitor digoxin levels."),
]


def check_drug_interactions(medications: list[dict]) -> dict:
    """Check all active medications for drug-drug interactions.

    Args:
        medications: List of FHIR MedicationRequest resources

    Returns:
        Dict with interactions found, grouped by severity
    """
    # Extract medication names
    med_names = []
    for med in medications:
        concept = med.get("medicationCodeableConcept", {})
        name = concept.get("text", "")
        if not name:
            codings = concept.get("coding", [])
            name = codings[0].get("display", "") if codings else ""
        med_names.append(name.lower())

    interactions = []
    checked_pairs = set()

    for i, name_a in enumerate(med_names):
        for j, name_b in enumerate(med_names):
            if i >= j:
                continue
            pair_key = (min(i, j), max(i, j))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            for drug_a_kw, drug_b_kw, severity, mechanism, effect, recommendation in INTERACTION_DB:
                a_match = any(kw in name_a for kw in drug_a_kw)
                b_match = any(kw in name_b for kw in drug_b_kw)
                # Check both directions
                if not (a_match and b_match):
                    a_match = any(kw in name_b for kw in drug_a_kw)
                    b_match = any(kw in name_a for kw in drug_b_kw)

                if a_match and b_match:
                    interactions.append({
                        "drug_a": medications[i].get("medicationCodeableConcept", {}).get("text", med_names[i]),
                        "drug_b": medications[j].get("medicationCodeableConcept", {}).get("text", med_names[j]),
                        "severity": severity,
                        "mechanism": mechanism,
                        "clinical_effect": effect,
                        "recommendation": recommendation,
                    })

    # Sort by severity
    severity_order = {"severe": 0, "moderate": 1, "mild": 2}
    interactions.sort(key=lambda x: severity_order.get(x["severity"], 3))

    severe = [i for i in interactions if i["severity"] == "severe"]
    moderate = [i for i in interactions if i["severity"] == "moderate"]
    mild = [i for i in interactions if i["severity"] == "mild"]

    return {
        "total_interactions": len(interactions),
        "severe_count": len(severe),
        "moderate_count": len(moderate),
        "mild_count": len(mild),
        "interactions": interactions,
        "periop_note": f"{'⚠ SEVERE INTERACTIONS DETECTED — review before proceeding.' if severe else 'No severe interactions detected.'} {len(interactions)} total interaction(s) identified.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. RENAL DOSE ADJUSTMENT
# ══════════════════════════════════════════════════════════════════════════════

# Drug dosing adjustments based on GFR/CrCl
# (drug_keywords, adjustments_by_gfr_range)
RENAL_DOSE_DB = [
    ("metformin", [
        (60, None, "No adjustment needed"),
        (45, 60, "Reduce to max 1000mg/day. Monitor renal function every 3-6 months."),
        (30, 45, "Reduce to max 500mg/day. Monitor renal function every 3 months."),
        (0, 30, "CONTRAINDICATED. Risk of lactic acidosis. Discontinue immediately."),
    ]),
    ("apixaban", [
        (25, None, "Standard dose 5mg BID"),
        (15, 25, "Reduce to 2.5mg BID if also age ≥80 or weight ≤60kg"),
        (0, 15, "Use with caution. Limited data. Consider alternative anticoagulant."),
    ]),
    ("dabigatran", [
        (50, None, "Standard dose 150mg BID"),
        (30, 50, "Reduce to 75mg BID"),
        (0, 30, "CONTRAINDICATED. Do not use."),
    ]),
    ("rivaroxaban", [
        (50, None, "Standard dose"),
        (30, 50, "Use 15mg daily (not 20mg) for AFib indication"),
        (15, 30, "Use with caution. Limited data."),
        (0, 15, "AVOID. Not recommended."),
    ]),
    ("enoxaparin", [
        (30, None, "Standard dose: 1mg/kg BID (treatment) or 40mg daily (prophylaxis)"),
        (0, 30, "Reduce to 1mg/kg ONCE daily (treatment) or 30mg daily (prophylaxis). Monitor anti-Xa levels."),
    ]),
    ("gabapentin", [
        (60, None, "No adjustment needed. Max 3600mg/day."),
        (30, 60, "Max 600mg TID (1800mg/day)"),
        (15, 30, "Max 300mg BID (600mg/day)"),
        (0, 15, "Max 300mg daily. Give supplemental dose after dialysis."),
    ]),
    ("morphine", [
        (50, None, "Standard dosing. Use with caution."),
        (30, 50, "Reduce dose by 25%. Active metabolites accumulate."),
        (0, 30, "Reduce dose by 50-75%. Consider alternative opioid (fentanyl, hydromorphone). Active metabolite (M6G) accumulation causes prolonged sedation."),
    ]),
    ("vancomycin", [
        (50, None, "Standard loading dose. Adjust maintenance per trough levels."),
        (30, 50, "Extend interval to q12-24h. Target trough 15-20 for serious infections."),
        (0, 30, "Extend interval to q24-48h. Trough-guided dosing essential. Consider loading dose."),
    ]),
    ("gentamicin", [
        (60, None, "Standard dosing with trough monitoring"),
        (40, 60, "Extend interval to q12h. Monitor levels."),
        (20, 40, "Extend interval to q24h. Monitor levels closely."),
        (0, 20, "Extend interval to q48h or use single daily dosing with levels. Nephrotoxicity risk very high."),
    ]),
    ("lisinopril", [
        (30, None, "No adjustment needed"),
        (10, 30, "Start at lower dose (2.5-5mg). Titrate carefully. Monitor K+ and creatinine."),
        (0, 10, "Use with extreme caution. Risk of hyperkalemia and worsening renal function."),
    ]),
    ("furosemide", [
        (30, None, "Standard dosing. May need higher doses with reduced GFR for equivalent effect."),
        (0, 30, "May need significantly higher doses (80-200mg). IV preferred for reliability. Monitor electrolytes closely."),
    ]),
    ("insulin glargine", [
        (50, None, "No adjustment needed"),
        (30, 50, "Reduce dose by 25%. Insulin clearance reduced."),
        (0, 30, "Reduce dose by 50%. High risk of hypoglycemia due to reduced renal insulin clearance."),
    ]),
]


def _estimate_gfr(creatinine: float, age: int, gender: str, weight_kg: float | None = None) -> float:
    """Estimate GFR using CKD-EPI 2021 equation (race-free)."""
    if creatinine <= 0:
        return 120.0

    female = gender.lower() in ("female", "f")

    if female:
        kappa = 0.7
        alpha = -0.241 if creatinine <= kappa else -1.2
    else:
        kappa = 0.9
        alpha = -0.302 if creatinine <= kappa else -1.2

    gfr = 142 * (min(creatinine / kappa, 1.0) ** alpha) * (max(creatinine / kappa, 1.0) ** -1.2) * (0.9938 ** age)
    if female:
        gfr *= 1.012

    return round(gfr, 1)


def calculate_renal_adjustments(
    medications: list[dict], creatinine: float, age: int, gender: str,
) -> dict:
    """Calculate renal dose adjustments for all active medications.

    Args:
        medications: FHIR MedicationRequest resources
        creatinine: Serum creatinine in mg/dL
        age: Patient age in years
        gender: Patient gender

    Returns:
        Dict with GFR, adjustments needed, and recommendations
    """
    gfr = _estimate_gfr(creatinine, age, gender)

    adjustments = []
    for med in medications:
        concept = med.get("medicationCodeableConcept", {})
        med_name = (concept.get("text", "") or "").lower()
        if not med_name:
            codings = concept.get("coding", [])
            med_name = (codings[0].get("display", "") if codings else "").lower()

        display_name = concept.get("text") or (concept.get("coding", [{}])[0].get("display", "Unknown"))

        for drug_kw, ranges in RENAL_DOSE_DB:
            if drug_kw.lower() in med_name:
                for low, high, recommendation in ranges:
                    if high is None:
                        if gfr >= low:
                            adjustments.append({
                                "medication": display_name,
                                "gfr_range": f"≥{low}",
                                "adjustment": recommendation,
                                "needs_change": "no adjustment" not in recommendation.lower() and "standard" not in recommendation.lower(),
                            })
                            break
                    elif low <= gfr < high:
                        adjustments.append({
                            "medication": display_name,
                            "gfr_range": f"{low}-{high}",
                            "adjustment": recommendation,
                            "needs_change": True,
                        })
                        break
                break

    needs_adjustment = [a for a in adjustments if a.get("needs_change")]

    return {
        "estimated_gfr": gfr,
        "gfr_unit": "mL/min/1.73m²",
        "creatinine_used": creatinine,
        "ckd_stage": (
            "Stage 1 (≥90)" if gfr >= 90 else
            "Stage 2 (60-89)" if gfr >= 60 else
            "Stage 3a (45-59)" if gfr >= 45 else
            "Stage 3b (30-44)" if gfr >= 30 else
            "Stage 4 (15-29)" if gfr >= 15 else
            "Stage 5 (<15)"
        ),
        "total_medications_checked": len(adjustments),
        "adjustments_needed": len(needs_adjustment),
        "adjustments": adjustments,
        "periop_note": f"eGFR {gfr} mL/min ({('No renal dose adjustments needed.' if not needs_adjustment else f'{len(needs_adjustment)} medication(s) require dose adjustment.')})",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. ALLERGY CROSS-REACTIVITY
# ══════════════════════════════════════════════════════════════════════════════

CROSS_REACTIVITY_DB = {
    "penicillin": {
        "class": "Beta-lactam antibiotics",
        "cross_reactive_drugs": [
            {
                "drug_class": "Cephalosporins (1st gen)",
                "examples": ["cefazolin", "cephalexin"],
                "cross_reactivity_rate": "1-2%",
                "risk": "low",
                "recommendation": "Can use with caution. 1st-gen cephalosporins have slightly higher cross-reactivity. Administer first dose under observation.",
            },
            {
                "drug_class": "Cephalosporins (3rd/4th gen)",
                "examples": ["ceftriaxone", "cefepime", "ceftazidime"],
                "cross_reactivity_rate": "<0.5%",
                "risk": "very_low",
                "recommendation": "Generally safe. Cross-reactivity extremely rare with 3rd/4th gen cephalosporins.",
            },
            {
                "drug_class": "Carbapenems",
                "examples": ["meropenem", "imipenem", "ertapenem"],
                "cross_reactivity_rate": "<1%",
                "risk": "very_low",
                "recommendation": "Generally safe to use. Previous concerns about cross-reactivity were overstated.",
            },
            {
                "drug_class": "Aztreonam",
                "examples": ["aztreonam"],
                "cross_reactivity_rate": "0%",
                "risk": "none",
                "recommendation": "No cross-reactivity. Safe to use in penicillin-allergic patients.",
            },
        ],
        "safe_alternatives": [
            "Vancomycin (for gram-positive coverage)",
            "Clindamycin (for surgical prophylaxis)",
            "Azithromycin/Fluoroquinolones (for respiratory infections)",
            "Aztreonam (for gram-negative coverage)",
        ],
        "periop_surgical_prophylaxis": "Use Clindamycin 900mg IV + Gentamicin (or Aztreonam) instead of standard Cefazolin.",
    },
    "sulfonamide": {
        "class": "Sulfonamide antibiotics",
        "cross_reactive_drugs": [
            {
                "drug_class": "Sulfonamide non-antibiotics",
                "examples": ["furosemide", "thiazides", "celecoxib", "sumatriptan"],
                "cross_reactivity_rate": "Very low",
                "risk": "very_low",
                "recommendation": "Sulfonamide non-antibiotics (furosemide, thiazides) have a different chemical structure. Cross-reactivity is unlikely but not impossible. Use with monitoring.",
            },
        ],
        "safe_alternatives": [
            "Alternative diuretics: ethacrynic acid (if furosemide reaction)",
            "Alternative antibiotics: fluoroquinolones, macrolides",
        ],
        "periop_surgical_prophylaxis": "Standard cefazolin prophylaxis is safe — no cross-reactivity with sulfonamides.",
    },
    "codeine": {
        "class": "Opioid analgesics",
        "cross_reactive_drugs": [
            {
                "drug_class": "Natural opiates",
                "examples": ["morphine", "hydrocodone", "oxycodone"],
                "cross_reactivity_rate": "Variable",
                "risk": "moderate",
                "recommendation": "True allergy to codeine may indicate sensitivity to natural opiates. Consider synthetic opioids (fentanyl, tramadol) instead.",
            },
            {
                "drug_class": "Synthetic opioids",
                "examples": ["fentanyl", "meperidine", "methadone"],
                "cross_reactivity_rate": "<1%",
                "risk": "very_low",
                "recommendation": "Synthetic opioids are structurally different. Generally safe to use.",
            },
        ],
        "safe_alternatives": [
            "Fentanyl (synthetic — no cross-reactivity)",
            "Hydromorphone (semi-synthetic — lower risk)",
            "Non-opioid: acetaminophen, NSAIDs, regional anesthesia",
        ],
        "periop_surgical_prophylaxis": "Use fentanyl for intraoperative analgesia. Consider multimodal pain management.",
    },
    "latex": {
        "class": "Natural rubber latex",
        "cross_reactive_drugs": [
            {
                "drug_class": "Tropical fruits (oral allergy syndrome)",
                "examples": ["banana", "avocado", "kiwi", "chestnut"],
                "cross_reactivity_rate": "30-50%",
                "risk": "moderate",
                "recommendation": "Latex-fruit syndrome. Ask about food allergies. Avoid latex gloves — use nitrile.",
            },
        ],
        "safe_alternatives": [
            "Nitrile gloves for all procedures",
            "Latex-free equipment throughout OR",
        ],
        "periop_surgical_prophylaxis": "Schedule as FIRST CASE of the day. Latex-free OR environment mandatory.",
    },
}


def check_allergy_cross_reactivity(allergies: list[dict], medications: list[dict]) -> dict:
    """Check allergies for cross-reactivity with current and potential perioperative medications.

    Args:
        allergies: FHIR AllergyIntolerance resources
        medications: FHIR MedicationRequest resources (to check for conflicts)

    Returns:
        Dict with cross-reactivity warnings and safe alternatives
    """
    results = []

    for allergy in allergies:
        allergy_code = allergy.get("code", {})
        allergy_name = (allergy_code.get("text", "") or "").lower()
        if not allergy_name:
            codings = allergy_code.get("coding", [])
            allergy_name = (codings[0].get("display", "") if codings else "").lower()

        display_name = allergy_code.get("text") or (allergy_code.get("coding", [{}])[0].get("display", "Unknown"))
        criticality = allergy.get("criticality", "unknown")

        reactions = allergy.get("reaction", [])
        reaction_text = None
        severity = None
        if reactions:
            manifestations = reactions[0].get("manifestation", [])
            if manifestations:
                man_codings = manifestations[0].get("coding", [])
                reaction_text = man_codings[0].get("display", "") if man_codings else ""
            severity = reactions[0].get("severity")

        # Check against cross-reactivity database
        matched = None
        for key, data in CROSS_REACTIVITY_DB.items():
            if key in allergy_name:
                matched = data
                break

        if matched:
            # Check if any current medication is in the cross-reactive list
            active_conflicts = []
            for med in medications:
                med_concept = med.get("medicationCodeableConcept", {})
                med_name = (med_concept.get("text", "") or "").lower()
                for cross in matched["cross_reactive_drugs"]:
                    if any(ex in med_name for ex in cross["examples"]):
                        active_conflicts.append({
                            "medication": med_concept.get("text", med_name),
                            "cross_reactive_class": cross["drug_class"],
                            "risk": cross["risk"],
                            "recommendation": cross["recommendation"],
                        })

            results.append({
                "allergy": display_name,
                "criticality": criticality,
                "reaction": reaction_text,
                "severity": severity,
                "allergy_class": matched["class"],
                "cross_reactive_drugs": matched["cross_reactive_drugs"],
                "active_conflicts": active_conflicts,
                "safe_alternatives": matched["safe_alternatives"],
                "surgical_prophylaxis": matched["periop_surgical_prophylaxis"],
            })
        else:
            results.append({
                "allergy": display_name,
                "criticality": criticality,
                "reaction": reaction_text,
                "severity": severity,
                "allergy_class": "Unknown",
                "cross_reactive_drugs": [],
                "active_conflicts": [],
                "safe_alternatives": ["Consult pharmacy for alternatives."],
                "surgical_prophylaxis": "Review with anesthesia team.",
            })

    has_conflicts = any(r["active_conflicts"] for r in results)

    return {
        "allergies_checked": len(results),
        "active_conflicts_found": sum(len(r["active_conflicts"]) for r in results),
        "results": results,
        "periop_note": f"{'⚠ ACTIVE ALLERGY CONFLICTS DETECTED with current medications.' if has_conflicts else 'No active allergy-medication conflicts.'} Surgical antibiotic prophylaxis guidance included.",
    }
