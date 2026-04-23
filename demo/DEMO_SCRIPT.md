# Demo Script — Burl Reinger, AAA Repair

A scripted walkthrough for the Prompt Opinion marketplace demo video and live
judging walkthrough. Every beat is chosen so that at least one agent output
would have killed the patient if missed. Total runtime target: **3 minutes**.

---

## Patient at a glance

| | |
|---|---|
| Name | Burl C. Reinger |
| Age / Sex | 65 / Male |
| Planned surgery | **Open AAA repair — May 1, 2026** |
| Active conditions | CHF, CAD (post-CABG 2019), AFib, T2DM, HTN, OSA, CKD stage 3, prior TIA |
| Active meds | Warfarin, aspirin, insulin glargine, metoprolol, lisinopril, furosemide, atorvastatin |
| Key allergy | **Penicillin — anaphylaxis** (1 epi dose in 2005) |
| Prior op record | 2019 CABG x3 — difficult airway, post-op AFib, AKI, 2u pRBC (uploaded as PDF) |
| FHIR bundle | `demo/Burl285_Reinger292.json` (702 resources) |
| Prior op note | `demo/prior_surgical_report.pdf` (2 pages) |

Why this patient: every validated score fires non-trivially, every drug rule
triggers, the airway is borderline difficult, the allergy forces an antibiotic
swap, and the prior op PDF adds four findings that pure FHIR data misses.

---

## The 3-minute script

### Beat 1 — Setup (0:00 – 0:15)

**Narration:**
> "Pre-op clearance for a surgical patient takes a resident 30 to 45 minutes
> of manual chart review. We do it in 30 seconds, and catch things that
> resident would miss."

**On screen:** Prompt Opinion marketplace, patient Burl selected, AAA repair
scheduled May 1. Agent called "PreOp Intelligence".

---

### Beat 2 — First message (0:15 – 0:30)

**User types:**
> Run a pre-op clearance for AAA repair on May 1, 2026.

**Agent calls** (in order, visible in the trace):
1. `get_patient_preop_summary`
2. `calculate_surgical_risk`
3. `calculate_advanced_risk_scores`
4. `check_periop_medications`
5. `assess_lab_readiness`
6. `get_anesthesia_considerations`
7. `check_drug_interactions`
8. `calculate_renal_dose_adjustments`
9. `check_allergy_cross_reactivity`
10. `assess_preop_imaging`

**Pause on:** tool list in the trace — judges should see **10 parallel tool
calls** coming back in seconds. None of the marketplace competitors hit this
density.

---

### Beat 3 — The risk scores (0:30 – 0:55)

**Agent output (abbreviated):**

| Score | Value | Meaning |
|---|---|---|
| ASA | **IV** | Severe systemic disease, constant threat to life |
| RCRI | **5/6** | **>15% major cardiac event risk** |
| Caprini VTE | **Very High** | Extended prophylaxis required |
| STOP-BANG | **7/8** | High OSA risk, CPAP needed post-op |
| CHA₂DS₂-VASc | **7/9** | 11.2% annual stroke risk |
| MELD-Na | — | Liver function OK |
| Wells DVT | 2 | Moderate probability |
| HEART | 7 | High cardiac risk |
| LEMON | 4 | Difficult airway predicted |
| P-POSSUM | elevated | Surgical mortality prediction elevated |

**Narration:**
> "Eleven validated scoring systems — ASA, RCRI, Caprini, STOP-BANG,
> CHA₂DS₂-VASc — computed from peer-reviewed literature. No LLM guessing.
> These are the same scores an anesthesiologist runs by hand."

**Pause on:** RCRI 5/6 — "That single number means cardiology consult is
mandatory."

---

### Beat 4 — The killer medication moment (0:55 – 1:20)

**Agent output:**

| Drug | Action | Date |
|---|---|---|
| **Warfarin** | **HOLD** | **April 26** — exactly 5 days before surgery |
| Aspirin | Continue | cardiac indication |
| Insulin glargine | **Reduce 25%** | eGFR 34.3 — kidneys can't clear |
| Lisinopril | Hold morning of | hypotension risk |
| Furosemide | Hold morning of | volume status |
| Metoprolol | Continue | protective; withdrawal risk |
| Atorvastatin | Continue | — |

**Narration:**
> "The warfarin hold date is *calculated* from the surgery date, not guessed.
> Off by one day and the patient bleeds on the table or throws a clot. The
> insulin reduction is because his kidneys can't clear it — the agent used
> CKD-EPI 2021 on his current creatinine. A manual review misses this when
> the resident forgets to check eGFR before dosing."

**Pause on:** the April 26 date. Make it huge.

---

### Beat 5 — Labs & escalation (1:20 – 1:40)

**Agent flags:**

- Hemoglobin **10.1 g/dL** → ANEMIA — crossmatch 4 units pRBC
- **INR 2.6** → supratherapeutic — must correct pre-op
- BNP **520** → active CHF — optimize before proceeding
- HbA1c **7.8%** → uncontrolled diabetes
- Creatinine 1.9 → stage 3 CKD
- ECG > 30 days old → **EXPIRED — order new one**

**Narration:**
> "The agent sees the ECG is stale and refuses to clear the patient until
> it's repeated. A human resident on hour six of chart review misses this."

---

### Beat 6 — The PDF moment (1:40 – 2:10) 🔥

**User drags in** `demo/prior_surgical_report.pdf` (Burl's 2019 CABG note).

**User types:**
> This is the operative report from his prior heart surgery. Any
> implications for the current pre-op?

**Agent calls:** `parse_prior_operative_note` with the extracted text.

**Agent returns 7 new implications**, 2 critical:

| Severity | Finding | Implication |
|---|---|---|
| **CRITICAL** | Difficult airway (Mallampati III, GlideScope in 2019, BMI 34.8, neck 42 cm) | **Video laryngoscope on standby; awake fiberoptic plan; notify anesthesia in advance** |
| **CRITICAL** | Penicillin anaphylaxis (epinephrine administered 2005) | **Do NOT use Cefazolin or any β-lactam** |
| HIGH | Prior post-op AFib | Prophylactic beta-blocker; plan rate control |
| HIGH | Prior peri-op AKI (peak Cr 2.8) | Renal-protective strategy; MAP > 65 |
| HIGH | Prior LVEF 35% | Obtain current echo; cardiology clearance |
| MODERATE | 2u pRBC + 2u FFP in 2019 | Anticipate similar transfusion need |

**Narration:**
> "Prior operative notes are PDFs. They live in the chart. Nobody reads
> them. This agent does — and it extracted four findings that would change
> today's anesthesia plan. The airway history alone decides whether the
> patient wakes up."

**Pause on:** the critical airway implication. This is the moment.

---

### Beat 7 — The antibiotic swap (2:10 – 2:30)

**User types:**
> What antibiotic should we give for prophylaxis?

**Agent calls:** `select_antibiotic_prophylaxis` with surgery type + penicillin
allergy context.

**Agent returns:**
> **Clindamycin 900 mg IV**, 60 min pre-incision.
>
> Do **not** use Cefazolin (the standard for vascular surgery) — the patient
> has a documented severe penicillin allergy with ~2% cross-reactivity risk to
> first-generation cephalosporins. Clindamycin is the safe alternative for
> vascular procedures.

**Narration:**
> "Cefazolin is the textbook answer for vascular surgery. For this patient,
> the textbook answer kills him. The agent knew that without being asked."

---

### Beat 8 — Synthesis (2:30 – 2:50)

**User types:**
> Give me the full clearance report.

**Agent calls:** `generate_preop_clearance_report`.

**Output:** Structured clearance document with:

- **6 escalation flags** at the top (cardiology consult, difficult airway,
  critical meds, very high VTE, active CHF, anemia)
- Risk-score table (11 scores)
- Medication hold/continue/adjust table with dates
- Lab status
- Anesthesia plan (airway, NPO, allergy)
- Blood product plan: **crossmatch 4 units pRBC, 2 units FFP on hold**
- Surgical safety checklist auto-populated
- Patient education sheet

**Footer line**, always:
> *This is AI-generated decision support requiring clinician review.*

---

### Beat 9 — Close (2:50 – 3:00)

**Narration:**
> "Fifteen clinical tools. Eleven validated scoring systems. PDF parsing for
> prior operative notes. Dual MCP and A2A deployment. Three hundred million
> surgeries a year, every one needs this. That's PreOp Intelligence."

---

## What manual review would miss

| Finding | Why humans miss it |
|---|---|
| Warfarin hold date April 26 | Date math error under time pressure |
| Insulin dose reduction | Requires calculating eGFR first — often skipped |
| INR 2.6 supratherapeutic | Buried in lab list |
| 2019 difficult-airway history | PDF never opened |
| Penicillin → Clindamycin swap for vascular | Reflex is Cefazolin |
| ECG > 30 days expired | No systematic currency check |
| CHA₂DS₂-VASc 7 → bridging needed | Score rarely recomputed pre-op |
| BNP 520 → active CHF | Not on standard pre-op checklist |

Any **single** one of these missed can cause death or major morbidity.

---

## What to record

- Screen recording of the Prompt Opinion chat with trace panel open (so tool
  calls are visible).
- Cursor highlights on: RCRI 5/6, warfarin April 26, Cefazolin→Clindamycin,
  airway implication from PDF.
- Voice-over following the narration lines above.
- Final still frame: the escalation-flags summary with all 6 flags visible.

## Backup: if the platform is flaky

Run the MCP server locally:

```bash
python -m src.mcp_server.server
```

Call each tool with `patient_id="patient-c"` (the high-risk synthetic patient
that stands in for Burl). Every tool returns the same shape of structured
output — the demo still works entirely from JSON.
