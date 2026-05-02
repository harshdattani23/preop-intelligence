# Competitive Landscape — Agents Assemble Hackathon

Snapshot taken 2026-05-03 from the Prompt Opinion marketplace. ~88 agents tracked. Updates may have happened since.

## Tier list

### High tier — top-3 contenders

| Agent | Team | Why they're a threat |
|---|---|---|
| **PreOp + PostOp Intelligence** (us) | — | 22+ skills across 2 agents, 11 cited validated scores, multimodal PDF op-notes, dual MCP+A2A, perioperative niche, now with explicit verification + confidence + provenance |
| **CareRelay OS** | Samson Ojekunle | 4-agent clinical-handoff system, "#1 cause of medical errors" Impact narrative, 90s end-to-end, MCP+A2A+FHIR R4, hallucination prevention, HITL |
| **AuthBridge / AuthBridge Orchestrator** | tazWAR | 8 named MCP tools (`fetch_patient_context`, `lookup_pa_criteria`, `score_clinical_match`, `draft_pa_letter`, `draft_appeal_letter`, `verify_pa_letter`, `generate_patient_summary`, `batch_pa_check`), CMS-0057-F regulatory hook, multi-agent (orchestrator over tools) |
| **SOAR (soar-copilot)** | lohjo_ | First *direct* perioperative competitor — voice-directed surgical co-pilot for da Vinci VATS lobectomy. Covers preop + intraop + postop for one specific surgery; 8 skills; live event log → SBAR; voice UX |

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

### Lower tier — narrow or single-skill

ALICE/ARIA (Spooki, prior auth + appeals — 2 skills total), AuthArmor, AuthorizationAgent (Priyam), CarePath AI (Priyam), Authorization Readiness Review, PriorAI (Sajesh), Prior Auth AI Agent (Sai Prasanth), PriorAuth Pilot (Sivaji), Discharge Companion, MedBrief, MedGuard, MediCare Connect, Coverage Companion, Curaiva AI + HealthConnect Coordinator, CareBridge Agent + External (HarmonyForge), Clinical Order Assistant + Clinical Promise Keeper (PromiseKeeper), Clinical Synthesiser (Formulari) + Hardware Sentinel + Agent B, Clinical Synthesizer (Memusi Robi), Sentinel AI + Abuja Clinic Nurse (David Mike), Spoon Agent + Art Agent (Sama Rizvi), Diagora Orchestrator, MediFlow Clinical AI (Ukasha), my_helper (Soufiane), Diagnostic Auditor (Krish), Demrisk, Bharat multilingual, Duckteer, RenalGuard, RX Guard, SafeGuard + SafeGuard AI (Akhmad), Scheduling Agent (Priyam), Adi (Polish POZ), AnakUnggul (ASD), Biomechanical Wear & Tear Monitor, ReferralReady, TransitionBridge AI, A2A-MediFlow (ChandraSekar) + PatientHealthContextAgent, IPE Connect, LagosSmartTriageOrchestrator, SláinteCare Triage Assistant + Legacy Records Archivist + General Clinical Assistant (CyberDog), Medical_Mutabazi, Dr. Trial (TrialBridge), Sample agents (Po Python Sample, Zodiac Sign Agent).

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
- ❌ "Only perioperative agent" — SOAR exists in this lane
- ❌ "Only with cited clinical sources" — 2-3 others cite guidelines

### What's still defensible

- ✅ **Broadest perioperative coverage** — SOAR is one surgery; we span all adult surgeries
- ✅ **Most named validated clinical scores** — 11 cited from primary literature (Lee TH Circulation 1999 etc.)
- ✅ **Multimodal PDF op-note parsing** for clinical documents — only AetherMed is multimodal but they're generalist
- ✅ **Multi-agent across clinical phases** (preop→postop, distinct phases of same patient) — most multi-agent peers are sequential workflows in one phase
- ✅ **Highest skill count** — 22+ vs CareTeam's 12, AuthBridge's ~10, others mostly 1-9

### Final positioning

> "The deepest perioperative specialist on the marketplace — broadest coverage of adult surgical risk assessment, 11 validated clinical scores cited from primary literature, multimodal PDF op-note parsing, and explicit verification + confidence trail aligned with ACS NSQIP and SCIP perioperative quality measures."

Drop anything claiming "only X" or "uncontested" — those framings will not survive a judge clicking through the marketplace.
