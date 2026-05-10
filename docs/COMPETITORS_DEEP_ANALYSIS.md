# Competitive Deep Analysis — Agents Assemble Hackathon

Snapshot: 2026-05-03, 8 days to deadline. **Updated 2026-05-10, 1 day to deadline** with new entries — see Section 11 ("Late entries — what changed at T-1"). ~88 agents observed in marketplace dumps + 3 late entries. This document goes beyond the tier list in `COMPETITORS.md` — it analyzes judge psychology, vote-splitting math, Stage One survival, and our specific risks per prize bracket.

## 1. The actual competition pool, after Stage One filtering

Stage One is **pass/fail** on 4 gates: marketplace-published + protocol-adherent + platform-discoverable + synthetic-data-only. Of ~88 visible:

### Definite Stage One failures (zero competition risk)
| Agent | Why it likely fails |
|---|---|
| **DevGuard** (Ankit Sen & Vivek Garari) | Not a healthcare agent — CI/CD security tool with Auth0/GitHub. Rules require a healthcare AI solution. |
| **David Agent Survey** (David Pratama) | Description: "This is about david agent survey." No skills wired. |
| **Doctoral student "Po Agent"** (Dr. Bettina Soós) | Skill name = "Doctoral student". Looks unfinished. |
| **Guideline Agent** (122) | Single skill `guideline_followup`, no description. Placeholder handle "122". |
| **KBC Agent Test, Master_Test_001** (Shivam) | Names contain "Test", description is leaked system prompt. |
| **MindCare AI** | Student stress assessment. Not clinical, may fail "healthcare AI" clause. |
| **Zodiac Sign Agent** (Prompt Opinion Publisher) | Official demo, not a real entry. |
| **Po Python Sample** (Prompt Opinion Publisher) | Official sample, not a real entry. |

**~8 agents culled.** Real competition pool ≈ **80 submissions**.

### At-risk submissions (could fail Stage One on weak grounds)
- Submissions with single placeholder skills (Memusi Robi's "Clinical Synthesizer", several others)
- Submissions whose marketplace card is just a system prompt dump (CareTeam AI's verbose prompt-leak)
- Submissions claiming MCP or A2A but missing the `.well-known/agent-card.json` (need to verify case-by-case)

Estimate **3-5 more attrition** during judging. **Functional pool ≈ 75-77 agents.**

## 2. Prize bracket math

| Prize | Winners | Entrants per slot |
|---|---|---|
| 1st ($7,500) | 1 | 75-77 |
| 2nd ($5,000) | 1 | 75-77 |
| 3rd ($2,500) | 1 | 75-77 |
| Honorable Mention ($1,000) | 10 | 7-8 |
| **Total prize slots** | **13** | — |

**13 / 75 ≈ 17%** of qualifying submissions win something. PreOp Intelligence is currently in the top 5-8 by visible signal. Honorable Mention is highly likely; top-3 is contestable.

## 3. Categorical breakdown of the field

| Category | Count | Top contender(s) | Crowding effect |
|---|---|---|---|
| Prior authorization / appeals | **9** | AuthBridge (8 tools), AuthClear (state regs), Shailesh's PA (11 tools), AuthPilot (Da Vinci PAS) | Severe vote-splitting |
| Clinical handoffs / care coordination | **5** | CareRelay OS (4 agents), HealthcareValleyAgent, CarePath AI, CareTeam AI, PsyBridge | Moderate vote-splitting |
| Medication safety / drug interactions | **8** | MedBridge (Pritish, Beers Criteria), CascadeBreaker, MedGuard, RX Guard, RenalGuard, MediCare Connect, A2A-MediFlow | Heavy crowding, all narrow |
| Triage / ED / symptom assessment | **5** | ED Triage Intel (ESI), Duckteer, LagosSmartTriageOrchestrator, AetherMed, Clinical Triage agents | Geographic + clinical splits |
| Care gap / preventive | **3** | Care Gap Agent (Soham), Clinical Promise Keeper, MedBridge (Philippe) | Light crowding |
| Specialty (deep niche) | **10** | Josanshi (maternal), TinyDx (rare pediatric), PEDS GUARD, DaktariTB, ThyroidInterpreter, **us (perioperative preop+postop)**, **SOAR (perioperative-VATS)**, **Aegis Perioperative Copilot system ×3 cards (Supervisor + Consent EN + Consent HI)**, AnakUnggul (ASD), Demrisk, Adverse Event Investigator (pharmacovigilance), Homeward (post-surgical + PGx) | Perioperative now a 3-system cluster; Aegis matches our multi-agent architecture |
| Multi-agent orchestrators | **6** | CareTeam AI (12 skills), Curaiva, Diagora, MediFlow Clinical AI, AuthBridge Orchestrator, Sentinel AI | Architecture-as-pitch, varying depth |
| Document / multimodal | **4** | AetherMed, CyberDog (Slainte Scan), us, AuthClear (5-phase) | Light crowding |
| Generic / placeholder / single-skill utility | **30+** | (the rest) | Background noise |

**Key insight (revised again 2026-05-10 evening after second marketplace dump): prior auth has 9 contenders, perioperative now has 6 systems / 9 cards (us 2 + SOAR 1 + Aegis 3 + Surgical Pre-habilitation Optimizer 1 + Recovery Coach 1 + Homeward 1).** The niche went from "uncontested" on May 3 → "contested by Aegis" (May 10 AM) → "6-system cluster" (May 10 PM/eve). Vote-splitting math still favors us over the PA pack, but the perioperative niche advantage is materially eroded. Sub-niche breakdown:
- **Preop assessment**: us, Aegis Supervisor, SOAR (one-surgery scope), Surgical Pre-habilitation Optimizer
- **Postop / recovery**: us (PostOp Intelligence), Homeward, Recovery Coach

## 4. Judge psychology per criterion

The rules state three **equally weighted** criteria. Each judge applies their own framing.

### Criterion 1 — The AI Factor
> *"Does the solution leverage Generative AI to address a challenge that traditional rule-based software cannot?"*

**What scores high here:**
- Multimodal interpretation (image + text → integrated finding)
- Generative output that requires reasoning across heterogeneous sources (FHIR + PDF + image)
- Letter generation, narrative synthesis
- Confidence scoring under uncertainty

**Top contenders for this criterion:**
| Agent | Why |
|---|---|
| **AuthBridge / AuthClear / Shailesh** | Generating defensible PA letters that survive verification — clearly generative |
| **AetherMed Agentic** | Multimodal images + docs + symptoms — most visible "AI Factor" surface |
| **Us** | PDF op-note → structured findings → integrated with FHIR; multimodal image (now); Gemini-synthesized clinical reasoning across 11 cited scores |
| **CareRelay OS** | 4-agent reasoning on heterogeneous data, hallucination prevention |

**Risk for us:** rule-based scoring (RCRI, Caprini, etc.) is *not* generative AI per se. We need to make the synthesis layer the visible AI Factor — Gemini extracting from PDF op-notes, integrating image findings, narrative escalation flag generation.

### Criterion 2 — Potential Impact
> *"Does this address a significant pain point? Is there a clear hypothesis for how this improves outcomes, reduces costs, or saves time?"*

**What scores high here:**
- Emotional / equity narratives (sick mothers, sick kids, underserved geographies)
- Universal pain points (every patient has dealt with prior auth)
- Concrete time/cost savings with defensible numbers
- High-mortality clinical scenarios

**Top contenders for this criterion:**
| Agent | Why |
|---|---|
| **Josanshi** | Maternal mortality crisis + Medicaid coverage equity — strong emotional + equity narrative |
| **TinyDx** | Rare pediatric disease diagnostic odyssey — devastating story, well-known healthcare problem |
| **PEDS GUARD** | Pediatric medication safety, vulnerable population |
| **CareRelay OS** | "#1 cause of medical errors" framing — universal hospital pain point |
| **AuthBridge / AuthClear etc.** | Prior auth is the most-hated workflow in US healthcare |
| **DaktariTB** | TB/HIV in Kenya — global health equity |
| **AnakUnggul** | ASD caregiver support — emotional family narrative |
| **Us** | Surgical risk assessment — clinician-efficiency angle (30-45 min/patient → 30 sec) |

**Risk for us:** "perioperative risk assessment" sounds like back-office optimization unless we frame it sharply. Our story is **clinician burnout + missed risk factors** (the hidden harms), not patient mortality directly. We're objectively in the bottom half on emotional impact, top half on defensible numerics. The video MUST land a hard number in the first 30 seconds — see `VIDEO_SCRIPT.md`.

### Criterion 3 — Feasibility
> *"Could this exist in a real healthcare system today? Does architecture respect data privacy, safety standards, and regulatory constraints?"*

**What scores high here:**
- Named regulatory anchors (CMS-0057-F, state laws, Da Vinci PAS, ACS NSQIP, SCIP)
- Verification + human-in-the-loop framing
- FHIR R4 standards adherence
- Cited clinical literature
- Privacy: token handling, no PHI

**Top contenders for this criterion:**
| Agent | Why |
|---|---|
| **Us** | 11 cited validated scores from primary literature, ACS NSQIP + SCIP + BPCI-Advanced, verification tool with provenance, PHYSICIAN-REVIEW DRAFT framing, FHIR R4 |
| **AuthBridge** | CMS-0057-F compliance, `verify_pa_letter` tool, full audit trail |
| **AuthClear** | TX SB 490 + AZ HB 2417 + MD HB 1174 (state-specific), 5-phase Validation, confidence scoring |
| **Shailesh's PA Auth** | CMS-0057-F + 11 MCP tools + HITL physician review |
| **AuthPilot** | Da Vinci PAS-compliant (real HL7 IG) |
| **Josanshi** | Safety review layer, FHIR R4, ethical framing |

**Risk for us:** lower than other criteria. We're competitive here. The 11 cited scores from primary literature is a feasibility moat that's hard for general-purpose agents to fake.

## 5. Composite ranking by weighted criteria

Assigning a 1-5 score per criterion based on visible evidence:

| Agent | AI Factor | Impact | Feasibility | Composite |
|---|---|---|---|---|
| **Us** | 4 | 3 | 5 | **12** |
| **CareRelay OS** | 4 | 5 | 4 | **13** |
| **AuthBridge** | 4 | 4 | 5 | **13** |
| **Josanshi** | 4 | 5 | 4 | **13** |
| **AuthClear** | 4 | 4 | 5 | **13** |
| **TinyDx** | 4 | 5 | 3 | **12** |
| **Shailesh's PA Auth** | 4 | 4 | 5 | **13** |
| **MedBridge / Pritish** | 3 | 4 | 4 | **11** |
| **PEDS GUARD** | 3 | 5 | 3 | **11** |
| **CareTeam AI** | 3 | 3 | 3 | **9** (penalized for prompt leak) |
| **SOAR** | 4 | 3 | 4 | **11** |
| **AetherMed** | 5 | 3 | 3 | **11** |
| **HealthcareValleyAgent** | 3 | 3 | 4 | **10** |
| **Aegis Perioperative Copilot system** (Supervisor + Consent EN + Consent HI) | 4 | 4 | 4 | **12** |

**Honest read (revised 2026-05-10 PM): we're in a 6-way tie at the top with CareRelay, AuthBridge, AuthClear, Josanshi, and now Aegis.** Each beats us on one criterion and loses to us on another. The differentiator is still the demo video — but Aegis specifically targets our niche with a matching multi-agent architecture, so video execution against Aegis is more important than against any other competitor.

**Aegis composite went from 11 → 12 once their Supervisor was visible.** AI Factor is now 4 (they compute scores + LLM synthesis, comparable to us minus multimodal); Impact is 4 (perioperative + bilingual + patient-facing); Feasibility is 4 (FHIR R4 + guideline citations + multi-agent A2A + AIDAA/ISA/AIIMS regulatory hook). They are a credible top-3 contender, and they explicitly contest the perioperative niche.

## 6. Vote-splitting analysis

If judges pick one agent per category for top-3:

| Category | Best contender (likely chosen) | Runners-up (denied) |
|---|---|---|
| Prior auth | **AuthBridge** (most named tools, best regulatory) | AuthClear, AuthPilot, Shailesh, ALICE+ARIA, AuthArmor |
| Maternal/pediatric | **Josanshi** OR **TinyDx** OR **PEDS GUARD** (only one wins) | The other two |
| Handoffs / coordination | **CareRelay OS** | HealthcareValleyAgent, CarePath, CareTeam |
| Perioperative — full preop assessment | **Us** OR **Aegis** | The other; SOAR (one-surgery scope); Surgical Pre-hab Optimizer (single skill) |
| Perioperative — patient communication / bilingual | **Aegis EN/HI** | (uncontested in this sub-niche) |
| Postoperative recovery / handoff | **Us (PostOp Intelligence)** OR **Recovery Coach** (lived-experience narrative) | The other; Homeward (post-surgical + PGx; narrower) |
| Multimodal | **AetherMed** OR **us** | The other |
| Specialty (other) | DaktariTB, AnakUnggul, Demrisk, ThyroidInterpreter — fight for honorable mentions | — |

**Realistic top-3 scenarios** (judges picking one per category):

**Scenario A** (Impact-weighted judges):
1. CareRelay OS or Josanshi (Impact narrative wins)
2. AuthBridge (universal pain point + regulatory)
3. **Us** or TinyDx (specialty depth)

**Scenario B** (Feasibility-weighted judges):
1. **Us** (most cited scores + regulatory hooks + verification)
2. AuthBridge (most regulatory + verification tool)
3. CareRelay OS or AuthClear

**Scenario C** (AI Factor-weighted judges):
1. AetherMed (most visible multimodal AI)
2. **Us** (multimodal + synthesis + scoring)
3. CareRelay OS or AuthBridge

**Probability we win:**
- Top-3: **40-55%** under any reasonable judge weighting
- 1st: **15-25%** — depends entirely on video quality and Impact framing
- Honorable mention: **>85%** — even worst case, our depth + verification gets us a $1K prize

## 7. Specific risks to PreOp Intelligence

### Risk 1: Generic-sounding name/framing
"PreOp Intelligence" sounds like a back-office tool. Compare to "Josanshi" (named like a person, maternal-health connotation) or "TinyDx" (memorable, evocative of children). Judges browsing 80 agents see the name first.

**Mitigation**: video opens with a hook that re-anchors — "preventing the missed risk factor that kills a surgical patient." Name is locked, but framing isn't.

### Risk 2: SOAR exists in our exact lane
SOAR (lohjo_) is *the* direct perioperative competitor — voice-directed surgical co-pilot for VATS lobectomy. Their voice UX is genuinely innovative. Our "broader across all surgeries" pitch holds, but only if the demo video shows breadth visibly (4 surgery types in 30s).

**Mitigation**: per `VIDEO_SCRIPT.md`, lead with breadth. Don't try to compete on intraop coverage.

### Risk 3: Prior auth pack might consolidate behind one agent
If judges deliberate and one prior-auth agent (likely AuthBridge or AuthClear) emerges as the consensus PA pick, vote-splitting collapses. AuthBridge or AuthClear winning 1st-3rd is the realistic scenario where we're pushed to honorable mention.

**Mitigation**: minimal — we can't influence prior-auth dynamics. Stay focused on perioperative depth.

### Risk 4: Equity-narrative judges may auto-pick Josanshi/TinyDx
A judge who values health equity above all else may pick Josanshi or TinyDx for top-3 reflexively. We can't compete on emotional narrative.

**Mitigation**: clinician-efficiency narrative + specific harm numbers (preventable surgical complications, missed RCRI factors). Make the impact concrete and measurable, not emotional.

### Risk 5: Judges don't watch past 3:00
Rules state judges aren't required to watch beyond 3 minutes. Our verification tool, regulatory hook, and multimodal demo must all be visible **in the first 3 minutes** of the video. The script handles this.

### Risk 6: Marketplace card hasn't been judged yet
The first impression a judge gets is the marketplace card description, not the video. Ours should mention:
- ✅ Perioperative niche
- ✅ ACS NSQIP / SCIP / BPCI-Advanced
- ✅ Verification + confidence + provenance
- ✅ Multi-agent perioperative handoff
- ✅ Multimodal (PDF + clinical images)

The current description is good. Confirmed via the agent card.

### Risk 7-bis: Aegis Perioperative Copilot — direct architectural peer (added 2026-05-10, revised PM)

**Initial read (May 10 AM) was wrong.** Aegis is not 2 downstream consent agents — it is a **3-agent A2A perioperative system**:
- **Aegis Supervisor**: 6 MCP tools (`normalize_fhir`, `fetch_patient_from_fhir`, `assess_current_patient`, `compute_risk_scores`, `fetch_guideline`, `format_aegis_report`). Computes RCRI, STOP-BANG, Apfel, ASA. Issues PROCEED / OPTIMIZE / ESCALATE / POSTPONE with guideline citations.
- **Aegis Consent EN**: Grade-8 patient consent, surgeon checklist, anaesthesia-specific section, optimisation action table, postponement letter.
- **Aegis Consent HI**: Hindi-localised twin with bilingual clinical doc; AIDAA 2024 / ISA / AIIMS hooks.

This matches our 2-agent A2A pipeline. Same niche, same architecture, same recommendation framework, same FHIR R4, overlapping score set.

**Why it's a serious risk:**
- A judge browsing perioperative will see Aegis 3 cards + ours 2 cards + SOAR 1 card. Aegis is the most-visible perioperative entry.
- Aegis owns sub-niches we don't claim: bilingual patient communication, Indian regulatory hook, plain-language consent, postponement letters.
- Aegis's multi-agent architecture neutralises our "multi-agent across clinical phases" defensibility — they have 3 agents in the perioperative pipeline, we have 2.
- Aegis's `verify_pa_letter`-equivalent isn't named, but their format_aegis_report likely includes an audit-trail equivalent.

**Why we still beat them on the leaderboard if we execute the video right:**
- **Score depth**: 11 cited from primary literature vs their 4. This is the single biggest delta.
- **Multimodal PDF op-note parsing**: not in their stack.
- **Primary-literature citations** (Lee TH Circulation 1999 etc.) vs their generic "guideline citations". Stronger Feasibility signal.
- **Preop + postop** vs their preop + consent. Different breadth — we cover a longer clinical phase span.
- **Verification + confidence + provenance tool** — they don't claim this as a discrete tool.
- **22+ skills** vs their ~16 across 3 agents.

**Mitigations (executable in the last 24 hours):**
1. **Card wording — concrete and numbered.** Replace "deepest perioperative specialist" with "11 validated scores from primary literature, preop + postop coverage, multimodal PDF op-note parsing". Compete on countable claims, not adjectives.
2. **Video opener (first 30 s) must visibly show ≥6 scores being computed** (not narrated — on screen). Aegis claims 4, so this is the easy asymmetry to land in a judge's first impression.
3. **Multimodal sequence (around the 90 s mark)**: PDF op-note → extracted finding → integrated into FHIR. Aegis has no equivalent.
4. **Preop → Postop handoff (around the 2 min mark)**: show the second agent firing. Aegis stops at consent; we go further down the clinical phase.
5. **DevPost text**: "preoperative + postoperative" — never just "perioperative" alone, since that word is now ambiguous between us and Aegis.
6. **Do NOT add bilingual consent at T-1**: scope creep, can't win on this axis in 24 hours, and trying would distract from execution.

### Risk 7: We haven't been judged on PO platform yet
Stage One requires platform integration. We've verified the live A2A endpoints work end-to-end via HAPI smoke test, but **we have not yet validated on Prompt Opinion's actual chat surface**. If something breaks in PO-specific request shapes, we fail Stage One.

**Mitigation**: per `PROMPT_OPINION_TUTORIAL_TRANSCRIPT.md`, do the External Agents → Consult with another agent flow with a synthetic patient before relying on the smoke test alone.

## 8. Sleeper threats — agents that could appear in the last 8 days

The hackathon is open until May 11. New submissions land daily. Sleeper threats:

1. **Late-stage polished prior-auth agents** — well-funded teams may submit polished work in the last 48 hours. AuthBridge / AuthClear style depth + a great video could displace mid-tier contenders.
2. **Major hospital systems** — if Cleveland Clinic, Mayo, Mass General, or Kaiser submits in their org's name, that carries credibility weight a hackathon judge may favor.
3. **Combined teams** — two strong solo entries deciding to merge their codebases.
4. **A perioperative competitor with intraop coverage** — if someone ships a real intraop module that closes SOAR's gap or extends ours, that's a serious threat.
5. ✅ **Materialised 2026-05-10 (high severity)**: Aegis Perioperative Copilot — 3-agent A2A system with Supervisor computing scores + bilingual consent. Direct architectural peer in our niche. Composite 12, tied with us. See Risk 7-bis.
6. ✅ **Materialised 2026-05-10 (low-medium severity)**: Homeward — post-surgical recovery + pharmacogenomic agent. Narrow peer to PostOp Intelligence.
7. ✅ **Materialised 2026-05-10 (medium severity, name-collision risk)**: Surgical Pre-habilitation Optimizer (byuri) — single-skill agent but the niche framing is exact head-to-head with PreOp Intelligence. Risk is judge keyword-browsing confusion, not feature parity.
8. ✅ **Materialised 2026-05-10 (medium severity, Impact narrative)**: Recovery Coach (Om Shukla) — postop competitor with a strong lived-experience story ("surgeon promised 15-20 days, last dressing was day 67"). Beats us on Impact narrative within postop; we beat them on clinical depth.

**Mitigation**: lock the video and submission text by Day 5 of 8. Don't iterate beyond that — refinement past day 5 is rearranging deck chairs. **Exception (2026-05-10):** marketplace-card wording update from "perioperative specialist" → "perioperative risk-assessment specialist" is a 5-minute change worth shipping before submission.

## 9. What this analysis means for the next 8 days

### Top priority — VIDEO (50% of remaining effort)
The video is our differentiation lever. We're tied or near-tied on technical merit with 4-5 other agents. The video decides whether we're 1st, 3rd, or 8th.

- Day 1-2: Record per `VIDEO_SCRIPT.md`. Use Burl Reinger as the patient.
- Day 3-4: Edit. Burn-in subtitles. Add the 4-surgery breadth montage.
- Day 5: Watch with sound off. Watch on phone screen. Ensure the verification block + ACS NSQIP are visible.

### Second priority — PROMPT OPINION VALIDATION (10%)
Test the External Agents → Consult flow per `PROMPT_OPINION_TUTORIAL_TRANSCRIPT.md`. Confirm Stage One pass. Capture screenshots for the video.

### Third priority — DEVPOST SUBMISSION TEXT (15%)
Use the positioning blurb from `COMPETITORS.md`. Lead with:
- "Deepest perioperative specialist on Prompt Opinion"
- 22+ skills, 11 cited validated scores, multimodal, ACS NSQIP-aligned
- Two-agent perioperative handoff (preop→postop)
- Verification tool with confidence + provenance

### Fourth priority — PUBLISH TO MARKETPLACE (5%)
After PO testing passes, toggle Publish in Marketplace Studio. Don't do this earlier — broken state in marketplace = first impression damage.

### What NOT to do
- ❌ Don't add new tools — 22 + verification is the optimal count
- ❌ Don't add intraop coverage — scope creep, can't beat SOAR there
- ❌ Don't engage on emotional narrative — Josanshi/TinyDx own that lane
- ❌ Don't iterate code past Day 5 — risk-reward bad

## 10. Final honest summary

PreOp Intelligence is in a competitive cluster of 5 strong agents (us, CareRelay OS, AuthBridge, AuthClear, Josanshi), with another 5-7 agents close behind. Our technical depth is at or above the cluster on every measurable axis except emotional narrative.

**Honorable mention is highly likely.** Top-3 is genuinely contestable. 1st place requires the video to be excellent and the perioperative impact framing to land — which depends almost entirely on execution in the next 8 days, not code.

**If you skip the video and submit code-only, you lose to a competitor with worse code and a better narrative.** The video isn't optional — it's the load-bearing element from here.

## 11. Late entries — what changed at T-1 (added 2026-05-10, revised PM after full marketplace dump)

Two passes were done on May 10: a morning spot check (3 names) and an afternoon full dump (~50+ entries visible, including new content). The afternoon pass overturned the morning conclusions about Aegis.

### 11.1 Aegis Perioperative Copilot system (Bhavna Gupta) — *high severity*

**Initial morning read was wrong.** Aegis is not 2 downstream consent agents — it is a 3-agent A2A perioperative system. See Risk 7-bis for full analysis.

- **Aegis Supervisor**: 6 MCP tools, computes RCRI / STOP-BANG / Apfel / ASA, PROCEED/OPTIMIZE/ESCALATE/POSTPONE recommendation, guideline citations.
- **Aegis Consent EN**: 5-skill patient consent generator.
- **Aegis Consent HI**: Hindi-localised twin with AIDAA / ISA / AIIMS regulatory hook.
- Composite 12 (AI 4 / Impact 4 / Feasibility 4). Tied with us at the top.
- Material because: this is a direct architectural peer in our niche. They match our multi-agent A2A approach, compute scores, cite guidelines, issue structured recommendations. Our defensibility narrows to score-depth, multimodal, primary-literature citations, and preop+postop breadth.

### 11.2 Adverse Event Investigator (Aditya Mittal) — *not material to us*

- Pharmacovigilance specialist. Three explicit modes: patient investigation, reasoning synthesis (Naranjo scoring, missing-data analysis), explicit MedWatch 3500 report drafting (deterministic extract → assess → check → draft chain).
- Different lane. Not perioperative, not adjacent. Honourable-mention candidate in the specialty bracket, fighting Demrisk / DaktariTB / ThyroidInterpreter for one slot.
- Composite estimate: AI 4 / Impact 3 / Feasibility 4 = 11.

### 11.3 Other notable entries from the May 10 PM dump

| Agent | Niche | Composite est. | Material to us? |
|---|---|---|---|
| **The Council** (multi-specialty peer A2A: Cardiology, Anesthesia, Endocrinology, Nephrology, Developmental Peds, coordinated by a Convener) | Multi-specialty consult | ~10 | Low — the Anesthesia peer is perioperative-adjacent but is one slice of a council, not a focused entry |
| **MamaGuard** (Michal Kurc; maternal-pediatric, 15 FHIR tools, 4-agent orchestration, 5T framework, writes RiskAssessment/CarePlan/CommunicationRequest) | Maternal | ~11 | None for us; direct threat to Josanshi |
| **DischargePlanner + DischargeReady** (Darena Health) | Discharge | — | None — Darena = Prompt Opinion platform team; these are platform reference agents, not eligible. Worth studying card layout. |
| **NutriPlan team** (Sharath Lokesh) | Nutrition (5-agent) | ~10 | None |
| **ClinAssemble** | Generalist CDS (triple-whammy, readmission scoring) | ~10 | Low |
| **Continuum Conductor** | Cross-org A2A orchestration with SHARP/audit-trail | ~10 | Low; reinforces Feasibility-criterion crowding |
| **Homeward** (Faith Ogundimu) | Post-surgical recovery + PGx | ~10 | Low-medium — narrow peer to PostOp Intelligence |
| **CodeBlue Context** | Emergency 5-agent reasoning pipeline | ~10 | None |
| **Consilium** | Multi-specialty TOPSIS-ranked HF+T2DM+CKD | ~10 | None |
| **CareOps Sentinel** (orchestrator + safety reviewer + language editor, N DIVIJ) | Healthcare-agent safety review meta-layer | ~10 | None — adjacent to verification but different scope |
| **Longevity Copilot** | Longevity / functional medicine, 19+ skills | ~10 | None |
| **Adverse Event Investigator** | Pharmacovigilance / MedWatch | 11 | None |

### 11.4 Adi (Ewelina Lesiak) — *ambiguous*

- Description shifted from "Polish POZ primary care" to "Agent do zarządzania kryzysowego w medycynie" (crisis management in medicine / emergency triage). Still lower-tier in the visible state. No action required.

### 11.5 Net impact on our position (revised evening 2026-05-10)

| Question | Before (May 3) | After morning May 10 (wrong read) | After PM May 10 (Aegis revealed) | After evening May 10 (full picture) |
|---|---|---|---|---|
| Perioperative-niche systems | 2 (us + SOAR) | 3 (us + SOAR + Aegis-as-consent) | 3 (us + SOAR + Aegis-as-peer) | **6** (us + SOAR + Aegis + Surgical Pre-hab + Recovery Coach + Homeward) |
| Aegis composite score | n/a | 11 | 12 — tied with leading cluster | 12 — unchanged |
| Top-3 probability (range) | 40-55% | 35-50% | 30-45% | **25-40%** (further downshift) |
| Honourable-mention probability | >85% | ~85% | ~80% | **~75%** (still likely) |
| Single most useful T-1 action | Lock video | Card wording update | Visible asymmetries in video | **Same — plus card must lead with concrete numbers, not category words** |

**Bottom line:** The perioperative niche went from "2 agents" on May 3 to "6 systems / 9 cards" on May 10. Aegis remains the single most serious peer threat (architectural match + score computation + bilingual). The other 3 new entries (Surgical Pre-habilitation Optimizer, Recovery Coach, Homeward) are individually weaker but collectively reduce our "broadest perioperative" framing and create marketplace-browsing noise.

Our top-3 odds drift cumulatively from ~50% (May 3) to ~30% (May 10 evening). Honourable mention drift from >85% to ~75% — still likely but not assured.

The asymmetries to make visible in the video remain:
1. **11 cited scores from primary literature** vs Aegis's 4, vs Surgical Pre-hab's "FHIR analysis" single skill (the single biggest delta)
2. **Multimodal PDF op-note parsing** (no perioperative peer claims this)
3. **Preop → postop coverage** (us alone — Aegis stops at consent, SOAR is one-surgery)
4. **Verification + confidence + provenance tool** (discrete tool, not just a claim)

If the video doesn't visibly demonstrate at least 3 of these 4 asymmetries in the first 90 seconds, the perioperative cluster vote may split in ways that push us out of the top-3 entirely.
