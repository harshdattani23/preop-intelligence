# Competitive Landscape — Agents Assemble Hackathon

Snapshot taken 2026-05-03 from the Prompt Opinion marketplace. ~88 agents tracked. Updated 2026-05-10 with new entries surfaced one day before deadline (see "Late entries surfaced 2026-05-10" section).

## Tier list

### High tier — top-3 contenders

| Agent | Team | Why they're a threat |
|---|---|---|
| **PreOp + PostOp Intelligence** (us) | — | 22+ skills across 2 agents, 11 cited validated scores, multimodal PDF op-notes, dual MCP+A2A, perioperative niche, now with explicit verification + confidence + provenance |
| **CareRelay OS** | Samson Ojekunle | 4-agent clinical-handoff system, "#1 cause of medical errors" Impact narrative, 90s end-to-end, MCP+A2A+FHIR R4, hallucination prevention, HITL |
| **AuthBridge / AuthBridge Orchestrator** | tazWAR | 8 named MCP tools (`fetch_patient_context`, `lookup_pa_criteria`, `score_clinical_match`, `draft_pa_letter`, `draft_appeal_letter`, `verify_pa_letter`, `generate_patient_summary`, `batch_pa_check`), CMS-0057-F regulatory hook, multi-agent (orchestrator over tools) |
| **SOAR (soar-copilot)** | lohjo_ | First *direct* perioperative competitor — voice-directed surgical co-pilot for da Vinci VATS lobectomy. Covers preop + intraop + postop for one specific surgery; 8 skills; live event log → SBAR; voice UX |
| **Aegis Perioperative Copilot (Supervisor + Consent ×2)** | Bhavna Gupta | **3-agent A2A perioperative system.** Supervisor (6 MCP tools: normalize_fhir, fetch_patient_from_fhir, assess_current_patient, compute_risk_scores, fetch_guideline, format_aegis_report) computes RCRI/STOP-BANG/Apfel/ASA, issues PROCEED / OPTIMIZE / ESCALATE / POSTPONE, with guideline citations. Hands off to Consent EN + Consent HI agents that emit Grade-8 reading-level bilingual consent. Direct head-to-head: same architecture, same niche, fewer scores than us but with bilingual patient communication |

### Medium-high tier — could displace top-3

| Agent | Team | Skills | Hook |
|---|---|---|---|
| **AuthClear** | — | 1 visible | Claude Sonnet 4, 5-phase workflow (Parse → Terminology → Gap Analysis → Draft → Validation), confidence-scored drafts, names TX SB 490 / AZ HB 2417 / MD HB 1174 state laws |
| **Josanshi** | Chris | 8 | Maternal health, "safety review layer before answers shown", Medicaid coverage flagging, equity disparity analysis |
| **CareTeam AI — Multi-Agent Orchestrator** | App Intelligence | 12 | Highest skill count of any competitor; full observability dashboard; risk score / risk level / confidence / escalation taxonomy; *but* leaked their full system prompt into the marketplace card |
| **Shailesh's PA Authorization Agent** | Shailesh Hawale | 1 visible | 11 MCP tools (most-tooled PA agent), CMS-0057-F compliant, HITL physician review, letter safety verification |
| **AuthPilot** | — | 4+ | Da Vinci PAS-compliant (real HL7 interop standard), Gemini 2.5 Flash, full audit trail |
| **MedBridge / Pritish** | Pritish | 7 | Hospital discharge medication reconciliation, Beers Criteria, cascade prescribing, transitions-of-care |
| **PEDS GUARD** | — | 1 visible (7 MCP tools) | Pediatric medication safety, weight-based dosing, real pharmacology depth |
| **HealthcareValleyAgent** | Mike Hibbert | 9 | Explainable, uncertainty-aware, risk review + care bundles + handoffs (overlaps CareRelay) |
| **TinyDx Diagnostic Navigator** | Pramod Misra | 1 visible | Rare pediatric disease, HPO + Orphanet integration, cites Nature 2026 (DeepRare paper) |
| (Aegis Consent EN + HI rolled into the Aegis 3-agent entry in High tier) | — | — | See high tier — Aegis is a 3-agent A2A perioperative system, not 2 standalone consent agents |

### Medium tier — narrow specialty plays

| Agent | Niche |
|---|---|
| **DaktariTB Specialist** (Jamii Health) | TB/HIV in Kenya, rifampicin↔ART pharmacology, Kenya MOH notifications |
| **CascadeBreaker** | Prescribing cascade detection (geriatrics) |
| **PsyBridge** (Olek AI) | Psychology↔primary care via PHQ-9/GAD-7, FHIR normalization |
| **Care Gap Agent** (Soham) | Preventive care + chronic disease, with guideline citations |
| **ScriptFlow** (Deepti Bahel) | Pharmacy PA with 5T framework (Talk/Table/Template/Transaction/Task), tier scoring, ASCVD-qualifying GLP-1 step-therapy override |
| **ED Triage Intel** | ED triage with ESI scoring |
| **ThyroidInterpreter** | Endocrinology longitudinal + SBAR |
| **Anamnesis Clinical Agent** | 6 skills, generalist clinical |
| **Adverse Event Investigator** (Aditya Mittal) | Pharmacovigilance — investigates suspected ADEs from FHIR records, Naranjo causality scoring, drafts FDA MedWatch 3500 reports. 3 explicit modes (investigate / reason / draft) with a deterministic extract→assess→check→draft chain. Different lane from us; not a perioperative threat |
| **Surgical Pre-habilitation Optimizer** (byuri) | **Direct preop lane.** "Analyzes patient FHIR data to identify surgical risks and generates personalized pre-operative optimization plans." Single skill, light surface. Niche-name collision — a judge browsing by keywords ("surgical", "pre-operative") sees this card alongside PreOp Intelligence. Lower depth than us; risk is name confusion, not technical depth |
| **Recovery Coach** (Om Shukla) | **Direct postop lane.** Day-by-day post-surgical recovery plans with regional/cultural meal context (Indian / vegetarian / non-veg). Strong personal-story narrative ("surgeon promised 15-20 days, last dressing was day 67"). Compete with our PostOp Intelligence on Impact narrative — they have a lived-experience story, we have score breadth |
| **Homeward** (Faith Ogundimu) | Post-surgical recovery + pharmacogenomic agent. CPIC + ClinVar evidence, GREEN/AMBER/RED escalation, FHIR MedicationRequest/Communication drafting. Narrower than PostOp Intelligence but better PGx coverage. Niche peer to our postop agent |

### Lower tier — narrow or single-skill

ALICE/ARIA (Spooki, prior auth + appeals — 2 skills total), AuthArmor, AuthorizationAgent (Priyam), CarePath AI (Priyam), Authorization Readiness Review, PriorAI (Sajesh), Prior Auth AI Agent (Sai Prasanth), PriorAuth Pilot (Sivaji), Discharge Companion, MedBrief, MedGuard, MediCare Connect, Coverage Companion, Curaiva AI + HealthConnect Coordinator, CareBridge Agent + External (HarmonyForge), Clinical Order Assistant + Clinical Promise Keeper (PromiseKeeper), Clinical Synthesiser (Formulari) + Hardware Sentinel + Agent B, Clinical Synthesizer (Memusi Robi), Sentinel AI + Abuja Clinic Nurse (David Mike), Spoon Agent + Art Agent (Sama Rizvi), Diagora Orchestrator, MediFlow Clinical AI (Ukasha), my_helper (Soufiane), Diagnostic Auditor (Krish), Demrisk, Bharat multilingual, Duckteer, RenalGuard, RX Guard, SafeGuard + SafeGuard AI (Akhmad), Scheduling Agent (Priyam), **Adi** (Ewelina Lesiak — description shifted 2026-05-10 from "Polish POZ primary care" to "crisis management in medicine" / emergency triage; verify before relying on prior categorization), AnakUnggul (ASD), Biomechanical Wear & Tear Monitor, ReferralReady, TransitionBridge AI, A2A-MediFlow (ChandraSekar) + PatientHealthContextAgent, IPE Connect, LagosSmartTriageOrchestrator, SláinteCare Triage Assistant + Legacy Records Archivist + General Clinical Assistant (CyberDog), Medical_Mutabazi, Dr. Trial (TrialBridge), Sample agents (Po Python Sample, Zodiac Sign Agent).

### Likely Stage One failures (don't compete for prizes)

- **DevGuard** (Ankit Sen & Vivek Garari) — CI/CD security, not a healthcare agent
- **David Agent Survey** (David Pratama) — placeholder ("This is about david agent survey")
- **Doctoral student "Po Agent"** (Dr. Bettina Soós) — placeholder
- **Guideline Agent** (122) — placeholder
- **KBC Agent Test, Master_Test_001** (Shivam) — test submissions; Master_Test_001's description leaks the system prompt
- **MindCare AI** — student stress assessment, out of clinical scope

## Pattern counts (commodity → distinctive)

| Pattern | Count of agents | Status |
|---|---|---|
| Prior auth / appeals | **7+** (ALICE+ARIA, AuthArmor, AuthBridge×2, AuthClear, AuthPilot, Auth Authorization Agent, PriorAI, Prior Auth AI Agent, PriorAuth Pilot, Shailesh's PA, ScriptFlow) | Saturated — vote-splitting |
| Multi-agent teams | **11+** (Spooki, tazWAR, HarmonyForge, Samson Ojekunle, App Intelligence, PromiseKeeper, Formulari, Curaiva, ChandraSekar, Priyam Shah ×4, CyberDog ×3, Sama Rizvi ×2, David Mike ×2, Deepti Bahel ×2, Akhmad Khudri ×2, Olek AI A2A) | Commodity |
| Anti-hallucination / verification claims | **6+** (AuthBridge `verify_pa_letter`, AuthClear Validation phase, CareRelay, Josanshi, Formulari "never invents", CareTeam, ourselves now) | Becoming table stakes |
| Confidence / uncertainty scoring | **3+** (AuthClear, Sai Prasanth approval-likelihood, HealthcareValleyAgent uncertainty-aware, ourselves now) | Distinctive |
| Multimodal | **3-4** (AetherMed images+docs, ourselves PDF op-notes, CyberDog Slainte Scan, possibly others) | Rarer |
| Cited validated clinical scores | **3+** (us 11, Care Gap Agent guideline cites, Demrisk regression, ED Triage ESI) | Rare in volume |
| Regulatory / standard hook | **4+** (AuthBridge CMS-0057-F, AuthClear state laws, AuthPilot Da Vinci PAS, Shailesh CMS-0057-F; ours: ACS NSQIP + SCIP after this update) | Distinctive |
| Medication safety / drug interactions | **8+** (A2A-MediFlow, CascadeBreaker, MedBridge×2, MedGuard, Medication Safety Agent×2, MediCare Connect, RX Guard, RenalGuard) | Crowded commodity |
| Trial matching | 3+ (Dr. Trial, Medical_Mutabazi, others) | Saturated |
| Perioperative / surgical workflow | **6 systems / 9 cards** (us 2 cards, SOAR 1, Aegis 3, Surgical Pre-hab 1, Recovery Coach 1, Homeward 1) | Material vote-split risk — went from "uncontested" (May 3) to "6-system cluster" (May 10). Preop sub-niche: us + Aegis + SOAR + Pre-hab. Postop sub-niche: us + Homeward + Recovery Coach |
| Patient-facing plain-language output | **2-3** (Aegis Grade-8 consent, Josanshi parent-friendly, possibly DaktariTB) | Distinctive — we don't claim this |
| Non-English / bilingual clinical | **3+** (Aegis Hindi, DaktariTB Swahili context, Bharat multilingual, Adi Polish) | Equity-narrative differentiator we don't claim |
| Pharmacovigilance / ADE reporting | **1** (Adverse Event Investigator — MedWatch 3500) | Uncrowded niche; not our lane |

## Top-competitor differentiation (per agent)

### vs. CareRelay OS

CareRelay covers handoffs broadly with 4 agents — preop→OR→PACU→ward→discharge are all handoffs. Our defense:
- **Clinical depth, not workflow coverage** — we ship named validated scores (RCRI, ACS-NSQIP, Mallampati, STOP-BANG, ASA, Caprini VTE, CHA₂DS₂-VASc, MELD, Wells, HEART, LEMON, GCS, P-POSSUM)
- **Multimodal PDF op-note parsing** — they don't claim it
- **Cited primary literature inline** — they don't claim it
- **22 skills vs 4-agent system with ~3-5 skills each** — comparable surface, deeper per-skill content

### vs. AuthBridge

AuthBridge is the technical peer in another niche (prior auth). Our defense:
- **We're not in prior auth** — judges who weight specialty diversity will pick one agent per niche
- **22 skills vs 8 tools** — broader surface
- **Multimodal + cited primary literature** — they don't claim either
- **They have `verify_pa_letter`; we now have `verify_clinical_output_a2a`** — gap closed

### vs. SOAR (most direct lane)

SOAR is the *only* other true perioperative agent. Different positioning:
- **SOAR**: depth on ONE surgery (VATS lobectomy), covers preop + intraop + postop, voice UX
- **Us**: breadth across ALL adult surgeries, covers preop + postop (no intraop), text+PDF UX

Honest framing: we are the **broadest** perioperative risk-assessment specialist; they are the **deepest** for one procedure. Don't claim "only perioperative agent" anymore.

### vs. AuthClear

AuthClear's regulatory specificity (TX SB 490, AZ HB 2417, MD HB 1174) is sharp. Our parallel: **ACS NSQIP risk-adjusted reporting + SCIP perioperative quality measures + CMS BPCI-Advanced surgical episode-based payment programs**. Now baked into our agent description and verification tool output.

### vs. Aegis Perioperative Copilot (the most direct head-to-head, late entry)

**Initial impression (May 10 morning) corrected by full marketplace dump (May 10 afternoon):** Aegis is not 2 consent agents — it is a **3-agent A2A perioperative system** with its own Supervisor that computes risk scores. The Supervisor uses 6 MCP tools (`normalize_fhir`, `fetch_patient_from_fhir`, `assess_current_patient`, `compute_risk_scores`, `fetch_guideline`, `format_aegis_report`) and emits a PROCEED / OPTIMIZE / ESCALATE / POSTPONE recommendation with guideline citations. Then it hands off to Consent EN + Consent HI agents. Three marketplace cards by one author for a coherent A2A pipeline.

This is the single most direct competitor we have. Same niche, same architecture (multi-agent A2A), same FHIR R4, same validated scores, same recommendation framework.

**What they have that we don't:**
- Bilingual (Hindi + English) patient-facing consent
- Indian regulatory hooks (AIDAA 2024 / ISA / AIIMS)
- Postponement letters + optimisation action table — concrete patient artefacts
- Grade-8 reading-level patient communication framing
- 3 marketplace cards = 3× judge-browsing surface area for one author

**What we have that they don't:**
- **More cited validated scores.** They claim 4 (RCRI, STOP-BANG, Apfel, ASA). We claim 11 cited from primary literature (Lee TH Circulation 1999, Caprini, Wells, HEART, LEMON, GCS, P-POSSUM, MELD, CHA₂DS₂-VASc, Mallampati, plus those 4).
- **Multimodal PDF op-note parsing.** They make no multimodal claim.
- **Primary literature citations.** They say "evidence-based guideline citations" — weaker. We cite specific papers.
- **Separate postop agent (PostOp Intelligence).** Their perioperative = preop + consent. Ours = preop + postop. Different breadth.
- **Verification + confidence + provenance tool.** Not visible in their stack.
- **22+ skills across our 2-agent system** vs their roughly 16 skills across 3 agents (6 Supervisor + ~5 EN + ~5 HI).

**Honest threat tier:** **High.** Co-leader of the perioperative niche with us. They beat us on patient-facing impact and bilingual angle; we beat them on technical depth and breadth. A judge choosing one perioperative agent for top-3 will weigh:
- Score depth + multimodal → us
- Patient-facing + equity narrative + bilingual → them
- Multi-agent architecture → both equal
- Regulatory hooks → both equal (ACS NSQIP / SCIP / BPCI for us; AIDAA / ISA / AIIMS for them)

**Defense playbook (executable in the last 24 hours):**
1. **Card wording:** lead with "11 validated scores from primary literature" and "preop + postop coverage". Counter their "perioperative" framing with concrete numbers.
2. **Video must show the asymmetries visibly:**
   - Score breadth — show ≥6 scores being computed on screen, not just 1-2
   - Multimodal — show the PDF op-note → extracted finding pipeline
   - Postop handoff — show the preop→postop A2A handoff (their stack stops at consent)
3. **DevPost text must say "preoperative + postoperative" not just "perioperative"** — disambiguates from Aegis.
4. **Do NOT try to add bilingual or patient-facing consent at T-1** — scope creep, can't beat them there in 24 hours.

### vs. Josanshi (specialty twin)

Same structural pattern (narrow specialty + multi-skill + impact narrative). Different domain. They beat us on equity narrative; we beat them on:
- Clinical depth (validated scores from primary literature)
- Multimodal PDF parsing
- Multi-agent across phases (preop→postop, not just one workflow)

## Strategic implications

### What's no longer unique to us

- ❌ "Only multi-agent submission" — 11+ teams ship multi-agent
- ❌ "Only verification step" — 6+ teams claim it
- ❌ "Only FHIR R4 + MCP + A2A stack" — most top contenders use it
- ❌ "Only perioperative agent" — SOAR + Aegis (×2 entries) exist in this lane
- ❌ "Only with cited clinical sources" — 2-3 others cite guidelines
- ❌ "Only perioperative-adjacent consent / patient-comms" — Aegis EN + HI own this

### What's still defensible

- ✅ **Deepest perioperative *risk computation*** — SOAR is one surgery; Aegis only formats output from an assumed assessment; we compute the assessment for all adult surgeries
- ✅ **Most named validated clinical scores** — 11 cited from primary literature (Lee TH Circulation 1999 etc.)
- ✅ **Multimodal PDF op-note parsing** for clinical documents — only AetherMed is multimodal but they're generalist
- ✅ **Multi-agent across clinical phases** (preop→postop, distinct phases of same patient) — most multi-agent peers are sequential workflows in one phase
- ✅ **Highest skill count** — 22+ vs CareTeam's 12, AuthBridge's ~10, Aegis ×2 = 10, others mostly 1-9

### Late entries surfaced 2026-05-10 (1 day before deadline)

The May 10 dumps (morning + afternoon + evening) collectively revealed substantially more new entries than the May 3 snapshot. The full picture:

**High-tier perioperative threats (changes our ranking math):**
1. **Aegis Perioperative Copilot system** (Bhavna Gupta) — 3 agents: Supervisor (6 MCP tools, computes RCRI/STOP-BANG/Apfel/ASA, PROCEED/OPTIMIZE/ESCALATE/POSTPONE recommendation) + Consent EN + Consent HI. Direct architectural peer in our niche. See "vs. Aegis Perioperative Copilot" diff section.

**Direct-lane perioperative competitors (changes the cluster size):**
2. **Surgical Pre-habilitation Optimizer** (byuri) — single-skill but the niche framing is *exact* head-to-head with PreOp Intelligence. Low technical depth; risk is **name/keyword collision** when judges browse, not feature parity.
3. **Recovery Coach** (Om Shukla) — postoperative recovery agent with day-by-day plans + cultural meal context + strong personal-story narrative ("surgeon promised 15-20 days, last dressing was day 67"). Direct lane competitor to PostOp Intelligence on Impact narrative.
4. **Homeward** (Faith Ogundimu) — post-surgical + pharmacogenomic recovery. Narrower but well-architected. Niche peer to PostOp Intelligence.

**Other notable systems (different niches, mostly not threats to us):**
5. **The Council** — multi-specialty A2A peer system: Cardiology, Anesthesia, Endocrinology, Nephrology, Developmental Pediatrics, Obstetrics, Oncology, Psychiatry, coordinated by a Convener. The Anesthesia peer is perioperative-adjacent but is one of many slices in a council. Composite ~10. Low threat.
6. **MamaGuard** (Michal Kurc) — maternal-pediatric multi-agent (15 FHIR tools, 4 agents, writes RiskAssessment/CarePlan/CommunicationRequest). Direct threat to Josanshi.
7. **Prenatal Visit Prep + On-Call OB Triage** (JonathanSolvesProblems) — high-risk OB pair with 5 MaternalGuard MCP tools, Spanish-language disposition summaries. Direct threat to Josanshi.
8. **DischargePlanner + DischargeReady + RxSafe** (Darena Health) — **Darena = Prompt Opinion platform team.** Reference/showcase agents, likely ineligible. Set the bar for polish.
9. **NutriPlan team** (Sharath Lokesh) — 6-agent A2A nutrition pipeline (FHIR Parser → Clinical Analysis → Preference → Meal Planning → Drug-Nutrient Safety, with Orchestrator). Another well-architected multi-agent system. Composite ~10.
10. **PriorAI** (Sajesh) — substantially more polished than the May 3 snapshot suggested. 6 skills, multi-payer (Anthem/UHC/Cigna), Da Vinci PAS, hallucination verification, approval likelihood scoring, CMS-0057-F urgency detection. Should be moved up within the prior-auth pack — possible top-3 PA contender alongside AuthBridge and AuthClear.
11. **PriorAuth Preflight - Lumbar MRI** (Sanjit Saji) — denial-prevention preflight specifically for outpatient lumbar MRI. 4 explicit outcomes including a red-flag fast-track for cauda equina / malignancy. Tightly scoped.
12. **ClinAssemble** — comprehensive CDS with triple-whammy detection + cardiovascular + readmission scoring.
13. **Continuum Conductor** (Manoj) — cross-org A2A orchestrator with SHARP audit trail. Strong Feasibility play.
14. **Red Team MD** (JossueAmador) — adversarial diagnostic review / premature-closure detection. Different angle.
15. **Steward AI** — antibiotic stewardship with IDSA guidelines, FHIR Task creation.
16. **Sepsis Sentinel** — sepsis risk + safety audit pipeline. Surgical sepsis overlap but agent is general.
17. **Veredictos Retina Orchestrator** — multimodal AI routing for ophthalmology with FHIR + AuditEvent + Provenance writes. One of the few other multimodal agents.
18. **Women's Health Clinical Agent** (Gbemisola Oyeniyi) — 11-skill women's-health CDS.
19. **CodeBlue Context** — emergency 5-agent reasoning (Triage/Guardian/Pathologist/Resident/Attending).
20. **Consilium** — multi-specialty TOPSIS-ranked HF+T2DM+CKD orchestrator.
21. **Longevity Copilot** — longevity / functional medicine with 19+ skills.
22. **PediRounds** — pediatric morning-rounds 3-agent system.
23. **MamaGuard / Prenatal Visit Prep / On-Call OB Triage** — three independent maternal entries, all threats to Josanshi.

**Adverse Event Investigator** (Aditya Mittal) — pharmacovigilance / MedWatch 3500. Different lane.

**Ambiguous:**
- **Adi** (Ewelina Lesiak) — description rescoped from Polish POZ primary care to "crisis management in medicine".

### Final positioning

> "The deepest perioperative **risk-assessment** specialist on the marketplace — broadest coverage of adult surgical risk computation, 11 validated clinical scores cited from primary literature, multimodal PDF op-note parsing, and explicit verification + confidence trail aligned with ACS NSQIP and SCIP perioperative quality measures."

Note the precise framing: **risk-assessment** specialist. After Aegis Consent landed, "perioperative specialist" alone is ambiguous — Aegis owns the consent half of perioperative. We own the *computation* half, which is the harder problem and the one that requires cited literature, FHIR R4 parsing, and multimodal extraction. Wording in the marketplace card and video opener must reflect this distinction.

Drop anything claiming "only X" or "uncontested" — those framings will not survive a judge clicking through the marketplace.
