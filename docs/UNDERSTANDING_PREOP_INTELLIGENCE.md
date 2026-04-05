# Understanding PreOp Intelligence — A Non-Medical Guide

## What Problem Are We Solving?

### The Real-World Scenario

Imagine you need surgery. Before any surgeon can operate on you, a doctor must do a **pre-operative assessment** — basically answering the question: **"Is this patient safe to put under anesthesia and operate on?"**

This process currently takes **30-45 minutes per patient** because a doctor has to:

1. Open your electronic health record (EHR)
2. Manually read through all your conditions, medications, lab results
3. Calculate risk scores by hand or from memory
4. Check if any of your medications need to be stopped before surgery
5. Check if your lab results are recent enough and normal
6. Assess if putting you to sleep will be difficult (airway assessment)
7. Write up a clearance note

**This is tedious, error-prone, and done millions of times a year.** Doctors miss things. A medication that should have been stopped 5 days before surgery gets missed. An expired lab result goes unnoticed. A dangerous drug interaction is overlooked.

**PreOp Intelligence automates this entire process in 30 seconds.**

---

## How Does It Work?

### The Simple Version

```
Patient's Health Record (FHIR)
         ↓
   Our AI Tools (15 tools)
         ↓
   Comprehensive Pre-Op Report
   with risk scores, medication
   instructions, lab checks,
   safety flags, and checklists
```

### The Technical Version

```
Hospital EHR (Epic, Cerner, etc.)
         ↓
   FHIR R4 Server (standardized health data format)
         ↓
   Prompt Opinion Platform (connects agents to data)
         ↓
   PreOp Intelligence Agent (our 15 tools)
         ↓
   Gemini 3.1 Pro (formats and synthesizes results)
         ↓
   Clinical Report (shown to the doctor)
```

---

## What Is FHIR?

**FHIR** (Fast Healthcare Interoperability Resources) is like a **universal language for health data**. Every hospital stores patient data differently, but FHIR provides a standard format so any system can read it.

Think of it like this:
- Hospital A stores "John has diabetes" in their own format
- Hospital B stores the same information differently
- FHIR says: "Here's one standard way to represent 'Patient has Diabetes Type 2 (SNOMED code 44054006)'"

Our tools read FHIR data. This means they work with **any hospital system** that speaks FHIR — which is now required by law in the US.

### Key FHIR Resources We Use

| FHIR Resource | What It Contains | Example |
|---------------|-----------------|---------|
| **Patient** | Name, age, gender, contact info | Burl Reinger, 65M |
| **Condition** | Diagnoses and medical problems | Heart failure, Diabetes |
| **MedicationRequest** | Active prescriptions | Warfarin 5mg daily |
| **Observation** | Lab results and vital signs | Hemoglobin 10.1, BMI 36.2 |
| **AllergyIntolerance** | Allergies and reactions | Penicillin → Anaphylaxis |
| **Procedure** | Past surgeries and procedures | CABG (bypass surgery) |

---

## What Are Our 15 Tools?

### Category 1: Patient Overview (1 tool)

#### 1. Patient Summary
**What it does:** Pulls together all the patient's data — demographics, conditions, medications, labs, vitals, allergies, past surgeries — into one structured view.

**Why it matters:** Normally a doctor has to click through 10 different screens in the EHR to see all this. We show it in one call.

---

### Category 2: Risk Scoring (2 tools, 11 scores total)

#### 2. Basic Surgical Risk Calculator
Calculates 4 validated scoring systems:

**ASA Physical Status (American Society of Anesthesiologists)**
- Classifies patients from I (healthy) to V (not expected to survive)
- Burl scored **ASA IV** — severe systemic disease, constant threat to life
- Why: CHF + CAD + multiple organ dysfunction

**RCRI — Revised Cardiac Risk Index (Lee Index)**
- Predicts risk of heart attack or cardiac death after surgery
- 6 criteria, each worth 1 point:
  1. High-risk surgery (e.g., AAA repair) ✓
  2. History of heart disease ✓
  3. History of heart failure ✓
  4. History of stroke/TIA ✓
  5. Diabetes on insulin ✓
  6. Creatinine >2.0 ✓
- Burl scored **5/6** = >15% risk of major cardiac event
- This means: **Get a cardiologist to clear this patient before surgery**

**Caprini VTE Score**
- Predicts risk of blood clots (DVT/PE) after surgery
- Considers age, surgery type, BMI, medical history
- Burl scored **Very High** = needs blood thinner injections after surgery + compression stockings

**STOP-BANG (Sleep Apnea Screening)**
- S: Snoring, T: Tired, O: Observed apnea, P: Pressure (HTN)
- B: BMI >35, A: Age >50, N: Neck >40cm, G: Gender male
- Burl hit almost every criterion = **High risk for difficult airway during anesthesia**

#### 3. Advanced Risk Scores (7 additional scores)

**CHA₂DS₂-VASc** — Stroke risk for patients with atrial fibrillation
- Burl scored **7/9** = 11.2% annual stroke risk
- Critical for deciding if he needs blood thinner bridging when we stop his warfarin for surgery

**MELD-Na** — Liver disease severity
- Uses bilirubin, creatinine, INR, sodium to predict liver-related mortality
- Important: if the liver is failing, surgery is much more dangerous

**Wells Criteria** — Probability of having a blood clot right now
- Before surgery, we need to make sure the patient doesn't already have a DVT

**HEART Score** — Chest pain risk
- If a patient has chest pain before surgery, is it a heart attack?
- Helps decide if surgery should be postponed

**LEMON Airway Assessment** — Will it be hard to intubate this patient?
- L: Look externally (obesity, facial anatomy)
- E: Evaluate 3-3-2 rule (mouth opening distances)
- M: Mallampati score (how much of the throat you can see)
- O: Obstruction (sleep apnea, tumors)
- N: Neck mobility
- Burl scored **High** — BMI 36.2, neck 43cm, OSA

**GCS (Glasgow Coma Scale)** — Neurological assessment
- Checks eye opening, verbal response, motor response
- Relevant for patients with brain injuries or altered consciousness

**P-POSSUM** — Surgical mortality prediction
- Comprehensive model using 12 physiological + 6 operative factors
- Outputs a specific mortality percentage

---

### Category 3: Medication Management (1 tool)

#### 4. Perioperative Medication Checker
**What it does:** Goes through every active medication and tells the doctor:
- **HOLD** — stop this drug X days before surgery (with specific date)
- **CONTINUE** — keep taking, even on surgery day
- **ADJUST** — change the dose
- **STOP** — discontinue permanently (herbal supplements)

**Burl's results:**

| Medication | Action | Why |
|-----------|--------|-----|
| **Warfarin** | HOLD 5 days before (April 26) | Blood thinner — will cause uncontrolled bleeding during surgery |
| **Metoprolol** | CONTINUE | Heart rate control — stopping it causes dangerous rebound tachycardia |
| **Insulin Glargine** | ADJUST (reduce 25%) | Fasting before surgery = hypoglycemia risk with full dose |
| **Lisinopril** | HOLD morning of surgery | Blood pressure drug — causes dangerous hypotension under anesthesia |
| **Furosemide** | HOLD morning of surgery | Water pill — can cause dehydration and electrolyte problems |
| **Aspirin** | CONTINUE | Heart protection outweighs bleeding risk for this patient |

**Why this matters:** If warfarin isn't stopped 5 days before, the patient will bleed uncontrollably during surgery. If metoprolol is accidentally stopped, the heart rate could spike dangerously. These are real patient safety issues that get missed in manual reviews.

---

### Category 4: Lab Assessment (1 tool)

#### 5. Lab Readiness Checker
**What it does:** Checks if all required pre-op labs are:
- **Current** (drawn within 30 days)
- **Normal** (within reference ranges)
- **Complete** (no missing required tests)

**Burl's abnormal labs:**

| Lab | Value | Normal Range | Meaning |
|-----|-------|-------------|---------|
| Hemoglobin 10.1 | Low | 12-17.5 g/dL | **Anemia** — may need blood transfusion during surgery |
| Creatinine 2.1 | High | 0.7-1.3 mg/dL | **Kidney failure** — drugs clear slower, contrast dye is dangerous |
| INR 2.6 | High | 0.9-1.1 | **Blood too thin** (from warfarin) — must correct before surgery |
| BNP 520 | High | <100 pg/mL | **Heart failure is active** — the heart is under stress |
| HbA1c 7.8% | High | <7% | **Diabetes not well controlled** — wound healing and infection risk |
| Glucose 158 | High | 70-100 mg/dL | **High blood sugar** — confirms poor diabetes control |

---

### Category 5: Anesthesia (1 tool)

#### 6. Anesthesia Considerations
**What it does:** Evaluates everything the anesthesiologist needs to know:

- **Airway risk:** Can we safely put the breathing tube in?
  - Burl: HIGH risk — BMI 36.2 (obese), neck 43cm (thick), OSA (sleep apnea)
  - Recommendation: Have video laryngoscope and fiberoptic scope ready

- **NPO (fasting) rules:** When to stop eating/drinking
  - No food after midnight
  - Clear liquids OK until 2 hours before

- **Allergies:** What drugs to avoid
  - Penicillin allergy with anaphylaxis → NO cefazolin (standard surgical antibiotic)
  - Use clindamycin or vancomycin instead

- **Special precautions:**
  - CPAP machine needed after surgery (for sleep apnea)
  - Monitored bed post-op (not regular floor)
  - Minimize opioid pain medications (respiratory depression risk with OSA)

---

### Category 6: Drug Intelligence (3 tools)

#### 7. Drug-Drug Interaction Checker
**What it does:** Cross-checks ALL active medications against each other for dangerous combinations.

**Burl's interactions found:**
- Warfarin + Aspirin = **increased bleeding risk** (both thin the blood)
- Warfarin + Furosemide = **INR fluctuation** (dehydration concentrates warfarin)
- Metoprolol + Insulin = **masks hypoglycemia** (can't feel low blood sugar symptoms)
- Furosemide + Lisinopril = **hypotension + kidney injury risk**

#### 8. Renal Dose Adjustment Calculator
**What it does:** Calculates the patient's kidney function (eGFR) and adjusts medication doses accordingly.

- Burl's eGFR: **34.3 mL/min** (CKD Stage 3b — kidneys working at ~34% capacity)
- Insulin glargine: **Reduce by 25%** (kidneys can't clear insulin as fast → hypoglycemia)
- Many drugs clear through kidneys — if kidneys are impaired, drugs accumulate to toxic levels

#### 9. Allergy Cross-Reactivity Checker
**What it does:** Determines if the patient's allergies create risks with other drugs they might receive during surgery.

- Penicillin allergy → Is it safe to use cephalosporins? (Same drug family)
  - 1st gen cephalosporins: 1-2% cross-reactivity risk (avoid for anaphylaxis history)
  - 3rd/4th gen: <0.5% risk (generally safe)
  - Carbapenems: <1% risk (generally safe)
  - Aztreonam: 0% risk (completely safe)
- **Surgical antibiotic alternative:** Clindamycin 900mg IV instead of standard Cefazolin

---

### Category 7: Clinical Protocols (5 tools)

#### 10. Antibiotic Prophylaxis Selector
**What it does:** Picks the right antibiotic to prevent surgical site infections.

Every surgery type has a recommended antibiotic given before the first incision:
- Cardiac surgery → Cefazolin (or Vancomycin if penicillin allergy)
- Vascular surgery → Cefazolin (or Clindamycin + Gentamicin)
- Abdominal surgery → Cefazolin + Metronidazole

For Burl: Can't use Cefazolin (penicillin allergy) → **Clindamycin 900mg IV, within 60 min before incision, redose every 6h**

#### 11. Blood Product Anticipation
**What it does:** Predicts how much blood the patient might need during surgery.

- AAA repair = **high blood loss** expected
- Burl's hemoglobin is already low (10.1) → higher transfusion risk
- INR 2.6 → bleeding risk from anticoagulation
- Recommendation: **Crossmatch 4 units of red blood cells, have cell saver ready**

#### 12. Frailty Assessment
**What it does:** Determines if the patient is "frail" — a clinical term meaning their body has limited reserves to recover from the stress of surgery.

FRAIL Scale (5 points):
- **F**atigue — does the patient tire easily? (CHF + anemia = yes)
- **R**esistance — can they climb stairs? (multiple comorbidities = likely limited)
- **A**mbulation — can they walk a block? (age 65 + BMI 36 + conditions = likely limited)
- **I**llness — do they have 5+ conditions? (9 conditions = yes)
- **L**oss of weight — are they malnourished? (check albumin/BMI)

Burl scored **3/5 = FRAIL**. This means:
- Higher risk of post-op delirium (confusion)
- Longer hospital stay
- Higher chance of going to rehab instead of home
- Should consider "prehabilitation" — exercise and nutrition program before surgery

#### 13. Patient Education Generator
**What it does:** Creates a plain-language instruction sheet for the patient explaining:
- What medications to stop and when
- What medications to continue
- Fasting rules (when to stop eating/drinking)
- What to bring to the hospital
- What to do the morning of surgery
- Allergy reminders

Written at a **6th-grade reading level** so any patient can understand it.

#### 14. Surgical Safety Checklist (WHO)
**What it does:** Generates a personalized version of the World Health Organization's Surgical Safety Checklist — the standard safety protocol used in operating rooms worldwide.

Three phases:
1. **SIGN IN** (before anesthesia): Verify identity, allergies, airway risk, blood availability
2. **TIME OUT** (before incision): Confirm procedure, antibiotic given, team introductions
3. **SIGN OUT** (before leaving OR): Confirm counts, specimens, post-op plan

Auto-populated with Burl's specific safety flags:
- ⚠ ALLERGY: Penicillin (Anaphylaxis)
- ⚠ DIFFICULT AIRWAY: BMI 36.2
- ⚠ COAGULOPATHY: INR 2.6
- ⚠ RENAL IMPAIRMENT: Cr 2.1
- ⚠ HEART FAILURE
- ⚠ OSA — needs CPAP post-op

---

### Category 8: Orchestration (1 tool)

#### 15. Complete Pre-Op Clearance Report
**What it does:** Calls ALL the above tools in one shot and produces a comprehensive pre-operative clearance report with:
- Patient summary
- All risk scores
- Medication action plan
- Lab readiness assessment
- Anesthesia evaluation
- Escalation flags

**This is the flagship tool** — one command generates a complete pre-op workup.

---

## How Does the Technology Stack Work?

### Layer 1: Data (FHIR)
```
Hospital EHR → FHIR R4 Server → Standardized patient data
```
The platform provides a FHIR server. When a doctor selects a patient, the platform sends three things to our tools:
- `x-fhir-server-url` — where the data is
- `x-fhir-access-token` — permission to access it
- `x-patient-id` — which patient

### Layer 2: Tools (MCP + A2A)
```
MCP Server (Model Context Protocol):
  - 15 tools that any agent can discover and use
  - Deployed on Google Cloud Run
  - Registered on Prompt Opinion platform

A2A Agent (Agent-to-Agent):
  - 14 skills that other agents can invoke
  - Can be consulted by any agent on the marketplace
  - Uses Gemini 3.1 Pro for clinical synthesis
```

**MCP** = tools that an AI can call (like functions)
**A2A** = agents that can talk to each other (like consultants)

### Layer 3: AI (Gemini 3.1 Pro)
```
Tool results (structured data) → Gemini → Clinical narrative
```
The tools return structured JSON data (numbers, scores, lists). Gemini formats this into readable clinical text. **Gemini never makes up data** — it only presents what the tools found.

### Layer 4: Platform (Prompt Opinion)
```
Doctor opens patient → Selects our agent → Asks a question →
Platform sends FHIR context → Our tools query FHIR → 
Results synthesized by Gemini → Doctor reads the report
```

---

## Why Is This Different From ChatGPT?

| Aspect | ChatGPT / Generic AI | PreOp Intelligence |
|--------|---------------------|-------------------|
| Data source | Guesses from training data | Queries real patient FHIR records |
| Accuracy | Can hallucinate lab values | Every number verified from FHIR |
| Risk scores | Describes what RCRI is | **Calculates** RCRI from actual data |
| Medications | Generic advice | Specific hold dates (e.g., "stop warfarin April 26") |
| Clinical validity | Not validated | Uses published, peer-reviewed scoring systems |
| Integration | Standalone chatbot | Integrated into clinical workflow via Prompt Opinion |
| Patient safety | No guardrails | Escalation flags, allergy cross-checks, drug interactions |

---

## The Demo Patient: Burl Reinger

### Who is Burl?
A 65-year-old man from Cleveland, OH scheduled for **elective AAA (abdominal aortic aneurysm) repair** — a major vascular surgery to fix a bulging aorta that could rupture.

### Why is he a perfect demo case?
He triggers **every single tool** with clinically significant findings:

- **9 serious conditions** — heart failure, coronary artery disease, prior heart attack, atrial fibrillation, diabetes, hypertension, sleep apnea, kidney disease, prior stroke
- **6 medications** — including warfarin (blood thinner requiring careful perioperative management)
- **Penicillin allergy with anaphylaxis** — can't use standard surgical antibiotics
- **6 abnormal lab values** — anemia, kidney failure, coagulopathy, uncontrolled diabetes, heart failure marker
- **Difficult airway** — obese with thick neck and sleep apnea
- **Frail** — 3/5 on frailty scale

### What our system catches that a busy doctor might miss:
1. Warfarin needs to stop **exactly 5 days before** (April 26, not April 27, not April 25)
2. INR of 2.6 needs correction before surgery (bleeding risk)
3. BNP of 520 means heart failure is **active** — cardiology clearance needed
4. Penicillin allergy means standard Cefazolin antibiotic is **contraindicated** — must use Clindamycin
5. Insulin dose needs to be **reduced 25%** because kidneys can't clear it
6. Metoprolol + insulin = **hidden hypoglycemia risk** (beta-blockers mask symptoms)
7. BMI 36.2 + neck 43cm + OSA = **need difficult airway equipment ready**
8. eGFR 34.3 = Stage 3b kidney disease — affects drug dosing across the board
9. CHA₂DS₂-VASc of 7 = needs **bridging anticoagulation** when warfarin is held (otherwise stroke risk)
10. FRAIL score 3/5 = should discuss goals of care, consider prehabilitation

**Any single missed item could cause a serious complication or death.**

---

## Competitive Landscape

### Hackathon Marketplace (33 agents)
- **7 agents** do Prior Authorization (all doing the same thing)
- **4 agents** do medication safety
- **3 agents** do generic clinical decision support
- **2 agents** do clinical trial matching
- **Several** are placeholders or non-healthcare

### Our Position
**We are the ONLY agent doing perioperative assessment.** Zero competitors in our category.

No one else has:
- Validated surgical risk scoring
- Medication hold timing with specific dates
- Drug interaction checking
- Renal dose adjustments
- Allergy cross-reactivity
- Antibiotic prophylaxis selection
- Blood product anticipation
- Frailty assessment
- Surgical safety checklists
- Patient education generation

---

## Numbers That Matter

| Metric | Value |
|--------|-------|
| MCP Tools | 15 |
| A2A Skills | 14 |
| Clinical Scoring Systems | 11 |
| Drug Interaction Rules | 20+ |
| Renal Dosing Rules | 12 drugs |
| Allergy Cross-Reactivity Classes | 4 |
| Antibiotic Protocols | 5 surgery types |
| Automated Tests | 28 (all passing) |
| Lines of Clinical Logic | ~3,000 |
| Surgeries Per Year (globally) | 300+ million |
| Time Saved Per Assessment | ~30 minutes |
| Potential Lives Impacted | Millions |
