# PreOp Intelligence — 3-Minute Demo Video Script

For: Agents Assemble Hackathon (May 2026)
Target length: ≤ 3:00 (judges aren't required to watch beyond this)
Platform: YouTube/Vimeo (per submission rules)
Tone: clinical, confident, dense — not salesy

## Strategic guardrails

**Lead with breadth, not depth.** SOAR is deeper for one surgery. We're broader across all surgeries. That's the wedge.

**Lead with the clinician, not the patient.** Josanshi/TinyDx own the patient-impact narrative. We own the clinician-efficiency narrative — measurable and defensible.

**Drop these claims:** "only multi-agent submission", "uncontested perioperative niche", "first MCP server for X". They're contestable and a judge clicking through the marketplace will catch them.

**Anchor every claim to something visible on screen** — a tool call, a citation, a FHIR resource ID. Avoid voiceover-only claims.

---

## Shot list (180 seconds)

### 0:00 – 0:12 — Hook
**Visual:** Cold open on a doctor scrolling a 40-tab EMR (b-roll or screen recording of FHIR R4 bundle JSON), timestamp clock running fast in corner.

**Voiceover:**
> "Pre-operative chart review takes 30 to 45 minutes per patient. It's the highest-burnout, lowest-prestige task in perioperative medicine — and it's where the biggest preventable harms hide. Missed risk factors. Wrong anticoagulation hold dates. Expired labs. Forgotten allergies."

**On-screen text (corner):** *"Pre-op chart review: 30–45 min/patient — manual"*

---

### 0:12 – 0:22 — Title + framing
**Visual:** Logo card cuts in. Two agent icons connected by an arrow: "PreOp Intelligence ⟶ PostOp Monitor."

**Voiceover:**
> "PreOp Intelligence is a two-agent perioperative handoff system on the Prompt Opinion platform. Pre-op clearance hands off to post-op surveillance — the highest-risk transition in surgical care, made auditable."

**On-screen text:** *"Two agents. One FHIR context. Perioperative handoff, end-to-end."*

---

### 0:22 – 0:55 — Breadth demo: 4 surgeries in 30 seconds
**Visual:** Split-screen or rapid-cut sequence on the Prompt Opinion platform. Same agent, four prompts, four reports.

**On-screen text overlay (one per cut):**
1. *"Patient A — knee arthroscopy. Low risk. Cleared."* (5 sec)
2. *"Patient B — inguinal hernia repair. Moderate. Hold ACE-I 24h."* (5 sec)
3. *"Patient C — abdominal aortic aneurysm repair. High risk. Cardiology consult."* (10 sec)
4. *"Patient D — laparoscopic cholecystectomy. Edge case: difficult airway flagged."* (10 sec)

**Voiceover (over the cuts):**
> "Four patients. Four different surgeries. Same agent. ASA classification, RCRI cardiac risk, Caprini VTE, STOP-BANG, Wells, MELD, P-POSSUM — eleven validated clinical scores, every one cited from primary literature. No surgery-specific specialization required."

**Ending freeze frame:** all four reports tiled in a grid.

---

### 0:55 – 1:25 — Citation + safety layer
**Visual:** Zoom into Patient C's report. Highlight the RCRI score row. Click expand on the trace JSON. Pop a callout box around `Lee TH, Circulation 1999;100:1043-9` inline in the trace.

**On-screen text:** *"Every score → primary literature citation, inline in the trace JSON"*

**Voiceover:**
> "Every recommendation is auditable. Each clinical score carries its primary literature citation right next to the value — Lee, Circulation 1999 for RCRI; Caprini for VTE; the original STOP-BANG validation paper. An anesthesiologist auditing the agent sees the source, not just the answer."

Cut to the verification panel. Show the structured output:
```
Overall confidence: medium
Per-section:
  patient_summary:    high   (Patient/c-001)
  surgical_risk:      high   (5 source resources)
  medication_review:  high   (8 source resources)
  lab_readiness:      medium (HbA1c expired 47d ago)
  anesthesia:         high   (BMI + 2 allergies)
Unverified areas:
  - HbA1c — expired (>30d before surgery)
Physician review required: TRUE
```

**Voiceover:**
> "After the assessment, an independent verification pass re-fetches every FHIR resource, scores per-section confidence, and flags anything it can't ground in the record. This is the safety layer — physician-review draft, never auto-approval."

---

### 1:25 – 1:55 — Multimodal: PDF op-note parsing
**Visual:** User drags a PDF (a prior operative note) into the Prompt Opinion chat. Agent ingests. Cut to extracted findings:

```
Prior operative note — extracted:
  • Difficult intubation: Cormack-Lehane Grade 3 (video laryngoscope used)
  • Intra-op peak Cr: 2.1 mg/dL (baseline 1.0) — AKI episode
  • Transfusion: 2 units pRBC
  • Post-op AFib (POD 2)

Pre-op implications:
  → Plan video laryngoscope ready
  → Heightened AKI surveillance post-op
  → Cardiology consult for AFib history
```

**Voiceover:**
> "Multimodal: drop in a prior operative note as a PDF, the agent extracts difficult-airway history, intra-op events, transfusion needs, and prior post-op complications — and maps each finding to a concrete pre-op implication. No other agent on the marketplace does this for clinical documents."

---

### 1:55 – 2:30 — The handoff: PreOp → PostOp
**Visual:** Same conversation. User types: "Patient C is out of surgery. POD 1." PostOp Monitor takes over in the same thread. Show:

```
PostOp Monitor — POD 1 surveillance plan for Patient C (AAA repair):

ESCALATION FLAGS:
  ⚠ AKI risk — pre-op Cr 1.4, intra-op peak 2.1 (per op note)
  ⚠ AFib history — telemetry continuous, low threshold for cardiology

Monitoring plan:
  Vitals     q1h × 12h, q2h × 24h, q4h thereafter
  Labs       BMP q12h × 48h (Cr trend)
  Renal redose: enoxaparin 30mg SC daily (eGFR 38)
                                    ↑ was 40mg pre-op

Verification: high confidence, all FHIR resources present.
```

**Voiceover:**
> "When surgery's done, the patient hands off to PostOp Monitor — same FHIR context, same conversation, different specialist. The pre-op risk profile carries forward: every recommendation is anchored to what the pre-op team flagged. Renal dosing automatically rebases on the new creatinine. Telemetry triggers fire on the AFib history. Pre-op to post-op is the highest-risk handoff in surgical care, and we make it auditable."

---

### 2:30 – 2:50 — Architecture + standards
**Visual:** Architecture card.

```
┌─ Prompt Opinion Platform ─────────────────┐
│  PreOp Intelligence Agent  (A2A · 17 skills)│
│  PostOp Monitor Agent      (A2A · 7 skills) │
│              ↓                            │
│  PreOp Intelligence MCP Server (10 tools) │
│              ↓                            │
│         FHIR R4 Server                    │
└───────────────────────────────────────────┘

Stack: Python 3.13 · Google ADK · Gemini 3.1 Pro · MCP · A2A · FHIR R4
Aligned with: ACS NSQIP · SCIP · CMS BPCI-Advanced
```

**Voiceover:**
> "Built on MCP, A2A, and FHIR R4. Twenty-four skills across two agents and a shared tool server. Aligned with ACS NSQIP risk-adjusted reporting and SCIP perioperative quality measures — the same risk metrics CMS uses to score surgical episodes."

---

### 2:50 – 3:00 — Close
**Visual:** Tagline card.

**On-screen text:**
> *"PreOp Intelligence + PostOp Monitor"*
> *"The deepest perioperative specialist on Prompt Opinion."*
> *"Every score cited. Every recommendation verified. Every handoff audited."*

**Voiceover (calm, confident):**
> "PreOp Intelligence. The deepest perioperative specialist on Prompt Opinion. Every score cited. Every recommendation verified. Every handoff audited."

End card.

---

## Recording checklist

- [ ] Use synthetic patients only (Patients A–D from `src/data/synthetic_patients/`) — rules require no real PHI
- [ ] No copyrighted music; use royalty-free or none
- [ ] Show the live Prompt Opinion platform UI for the demo segments — not localhost
- [ ] Show the live `https://app.promptopinion.ai/marketplace` listing once
- [ ] Capture at 1080p minimum, 60fps preferred for screen recording
- [ ] Burn-in subtitles (judges may watch with sound off)
- [ ] Upload publicly to YouTube/Vimeo before submission deadline
- [ ] Test the YouTube link from an incognito window — must not be unlisted

## What this script deliberately does NOT include

- ❌ "Only multi-agent submission" — confirmed false (10+ teams)
- ❌ "First MCP server for perioperative care" — unverifiable
- ❌ Skill-count comparisons against named competitors — looks petty
- ❌ Mentions of specific judges or Cleveland Clinic — judges may change
- ❌ Health-equity or patient-mortality framing — Josanshi/TinyDx own that lane
- ❌ Made-up statistics — every number must be defensible

## What it leans into (the wedge)

1. **Breadth across surgeries** (4 cases in 30 seconds) — counters SOAR's single-procedure depth
2. **Citations in the trace** (visible callout) — counters AuthBridge/AuthClear technical polish
3. **Verification + confidence panel** (visible JSON output) — matches AuthClear/CareRelay safety claims with substance
4. **Multimodal PDF op-note** (drag and drop demo) — only AetherMed claims multimodal and they're generalist
5. **Preop→PostOp handoff in the same conversation** — counters CareRelay's "handoff" framing with a more specific perioperative variant
6. **Regulatory anchor** spoken aloud (ACS NSQIP, SCIP) — matches AuthBridge's CMS-0057-F, AuthClear's state laws

## Voiceover delivery notes

- Pace: ~150 words per minute (this script is ~430 words → ~2:50 of voiceover, leaving 10s of breathing room)
- Tone: clinical and matter-of-fact, not enthusiastic. Judges have watched 90+ pitch videos; under-selling is the move
- Avoid: "revolutionary", "game-changing", "first-of-its-kind", "AI-powered" (every other submission says this)
- Use the words: "auditable", "verified", "cited", "validated", "physician-review draft", "perioperative handoff"
