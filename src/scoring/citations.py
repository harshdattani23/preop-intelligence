"""
Literature citations for every clinical scoring system used in this codebase.

Surfaces the primary derivation/validation paper alongside each score so
downstream consumers (Prompt Opinion trace panel, demo video, audit logs)
can show that each calculation is evidence-based, not LLM-generated.

Format choice — single-string citations rather than nested objects — keeps
JSON output readable at a glance and avoids breaking existing pydantic
models. Citations follow AMA-ish style (Author Year, journal abbrev).
"""

CITATIONS: dict[str, str] = {
    # Primary 4 (preop screening core)
    "ASA": "ASA Physical Status Classification System. American Society of Anesthesiologists, 2014 (last revised 2020).",
    "RCRI": "Lee TH et al. Derivation and prospective validation of a simple index for prediction of cardiac risk of major noncardiac surgery. Circulation 1999;100:1043-9.",
    "Caprini": "Caprini JA. Thrombosis risk assessment as a guide to quality patient care. Dis Mon 2005;51:70-78.",
    "STOP-BANG": "Chung F et al. STOP questionnaire: a tool to screen patients for obstructive sleep apnea. Anesthesiology 2008;108:812-21.",

    # Advanced 7 (in src/scoring/calculators.py)
    "CHA2DS2-VASc": "Lip GYH et al. Refining clinical risk stratification for predicting stroke and thromboembolism in atrial fibrillation. Chest 2010;137:263-72.",
    "MELD-Na": "Kim WR et al. Hyponatremia and mortality among patients on the liver-transplant waiting list. NEJM 2008;359:1018-26.",
    "Wells-DVT": "Wells PS et al. Value of assessment of pretest probability of deep-vein thrombosis in clinical management. Lancet 1997;350:1795-8.",
    "HEART": "Six AJ, Backus BE, Kelder JC. Chest pain in the emergency room: value of the HEART score. Neth Heart J 2008;16:191-6.",
    "LEMON": "Reed MJ, Dunn MJG, McKeown DW. Can an airway assessment score predict difficulty at intubation in the emergency department? Emerg Med J 2005;22:99-102.",
    "GCS": "Teasdale G, Jennett B. Assessment of coma and impaired consciousness — a practical scale. Lancet 1974;2:81-4.",
    "P-POSSUM": "Prytherch DR et al. POSSUM and Portsmouth POSSUM for predicting mortality. Br J Surg 1998;85:1217-20.",

    # Frailty + comprehensive
    "FRAIL": "Morley JE et al. A simple frailty questionnaire (FRAIL) predicts outcomes in middle aged African Americans. J Nutr Health Aging 2012;16:601-8.",

    # Drug intelligence references
    "renal-dose-CKD-EPI": "Inker LA et al. New creatinine- and cystatin C-based equations to estimate GFR without race. NEJM 2021;385:1737-49.",
    "antibiotic-prophylaxis": "Bratzler DW et al. Clinical practice guidelines for antimicrobial prophylaxis in surgery. Am J Health Syst Pharm 2013;70:195-283.",

    # Postop-specific
    "postop-AKI-KDIGO": "Kidney Disease: Improving Global Outcomes (KDIGO) Acute Kidney Injury Work Group. KDIGO Clinical Practice Guideline for AKI. Kidney Int Suppl 2012;2:1-138.",
    "postop-AFib": "January CT et al. 2019 AHA/ACC/HRS Focused Update on Atrial Fibrillation. Circulation 2019;140:e125-e151.",
    "postop-delirium": "American Geriatrics Society. Postoperative delirium in older adults: best practice statement. J Am Geriatr Soc 2015;63:142-50.",
    "postop-VTE-prophylaxis": "Gould MK et al. Prevention of VTE in nonorthopedic surgical patients (ACCP guideline). Chest 2012;141(Suppl):e227S-e277S.",
}


def cite(key: str) -> str:
    """Return the literature citation for a given scoring key, or empty string."""
    return CITATIONS.get(key, "")
