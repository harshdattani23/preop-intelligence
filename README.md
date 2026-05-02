# PreOp Intelligence + PostOp Monitor

**Two-agent perioperative system: pre-op clearance hands off to post-op monitoring in a single Prompt Opinion conversation.**

> **22 skills across 2 agents · 11 validated scoring systems · every score cited from primary literature · multimodal PDF parsing of prior op notes · dual MCP + A2A transport.** The deepest clinical agent on the Prompt Opinion marketplace — by a factor of 2–3× — and the only one demonstrating multi-agent composition.

Built for the [Agents Assemble](https://agents-assemble.devpost.com/) Healthcare AI Hackathon.

### Density, compared

| Agent | Skills / tools | Validated scores | Multimodal | Multi-agent | Dual transport |
|---|---|---|---|---|---|
| **PreOp + PostOp (us)** | **22 skills across 2 agents** | **11 (all cited)** | ✅ PDF op-notes | ✅ preop→postop handoff | ✅ MCP + A2A |
| AetherMed Agentic | 5 skills | 0 | ✅ Images + docs | — | — |
| AnakUnggul (ASD) | 7 skills | 1 (escalation risk) | — | — | — |
| ALICE + ARIA (prior auth) | 3 skills across 2 agents | 0 | — | partial | — |
| A2A-MediFlow | 2 skills | 0 | — | — | — |
| Abuja Clinic Nurse | 1 skill | 0 | — | — | — |

Every tool we ship is wired to peer-reviewed literature, and the citation is **inlined into the trace panel JSON** so an anesthesiologist auditing the agent sees `Lee TH, Circulation 1999;100:1043-9` next to the RCRI score. Every recommendation names the exact drug, the exact dose, and the exact date.

---

## What It Does

PreOp Intelligence automates the entire pre-operative clearance process — a workflow that currently takes clinicians 30-45 minutes of manual chart review per patient. Given a patient's FHIR health record, it produces a complete surgical risk assessment in seconds.

**Input:** A patient record on any FHIR R4 server + a planned surgery type and date

**Output:** Comprehensive pre-operative clearance report with risk scores, medication management plan, lab assessment, anesthesia evaluation, drug interaction check, surgical safety checklist, and patient education materials

## Demo

**Live on Prompt Opinion Marketplace:** [View Agents →](https://app.promptopinion.ai/marketplace)

| Service | URL |
|---|---|
| MCP server | `https://preop-mcp-server-yrv5ygakiq-uc.a.run.app/mcp` |
| **PreOp Intelligence** A2A agent card | `https://preop-agent-yrv5ygakiq-uc.a.run.app/.well-known/agent-card.json` |
| **PostOp Monitor** A2A agent card | `https://postop-agent-yrv5ygakiq-uc.a.run.app/.well-known/agent-card.json` |

The companion PostOp Monitor agent screens for the four complications driving most post-op morbidity (AKI, new-onset AFib, delirium, pulmonary), generates surgery- and ASA-driven monitoring plans with explicit red-flag thresholds, and re-doses every active medication for the patient's current renal trajectory. **Same FHIR context, same conversation, different specialist.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prompt Opinion Platform                    │
│                                                              │
│  Doctor selects patient → Platform sends FHIR context →      │
│  Our tools query FHIR server → Gemini synthesizes report     │
└──────────┬──────────────────────────────────┬────────────────┘
           │                                  │
    ┌──────▼──────┐                   ┌───────▼───────┐
    │  MCP Server  │                   │  A2A Agent     │
    │  16 Tools    │                   │  15 Skills     │
    │  Cloud Run   │                   │  Gemini 3.1    │
    │              │                   │  Cloud Run     │
    └──────┬──────┘                   └───────┬───────┘
           │                                  │
           └──────────────┬───────────────────┘
                          │
                 ┌────────▼────────┐
                 │   FHIR R4 Server │
                 │   (via SHARP)    │
                 │   Patient data   │
                 └─────────────────┘
```

### Two Integration Paths

| Path | Protocol | Endpoint | How It Works |
|------|----------|----------|-------------|
| **Path A: MCP Server** | Model Context Protocol | `/mcp` | Platform's agent calls our tools directly. FHIR context via HTTP headers (`x-fhir-server-url`, `x-fhir-access-token`, `x-patient-id`). |
| **Path B: A2A Agent** | Agent-to-Agent (Google) | `/.well-known/agent-card.json` | Other agents consult our agent via A2A protocol. FHIR context via message metadata. Uses Gemini 3.1 Pro for synthesis. |

---

## 16 Clinical Tools

### Risk Scoring (11 validated systems)

| Tool | Scores | What It Assesses |
|------|--------|-----------------|
| `calculate_surgical_risk` | ASA, RCRI, Caprini VTE, STOP-BANG | Core perioperative risk — cardiac events, blood clots, sleep apnea |
| `calculate_advanced_risk_scores` | CHA₂DS₂-VASc, MELD-Na, Wells DVT, HEART, LEMON, GCS, P-POSSUM | Stroke risk, liver disease, DVT probability, chest pain risk, airway difficulty, neurological status, surgical mortality prediction |

### Medication Management

| Tool | What It Does |
|------|-------------|
| `check_periop_medications` | Hold/continue/adjust instructions with specific dates for 35+ drug classes |
| `check_drug_interactions` | 20+ interaction rules covering anticoagulants, serotonin syndrome, QT prolongation |
| `calculate_renal_dose_adjustments` | eGFR calculation (CKD-EPI 2021) + dose adjustments for 12 renally-cleared drugs |
| `check_allergy_cross_reactivity` | Penicillin-cephalosporin, sulfonamide, opioid, latex cross-reactivity with alternatives |

### Clinical Assessment

| Tool | What It Does |
|------|-------------|
| `get_patient_summary` | Demographics, conditions, medications, labs, vitals, allergies, procedures |
| `assess_lab_readiness` | Lab currency (30-day threshold), abnormal values, missing required labs |
| `get_anesthesia_considerations` | Airway risk (BMI, neck, OSA), NPO guidance, allergy alerts, CPAP needs |
| `assess_frailty` | Modified FRAIL scale with prehabilitation recommendations |

### Protocols & Safety

| Tool | What It Does |
|------|-------------|
| `select_antibiotic_prophylaxis` | Surgery-specific antibiotic selection with allergy alternatives and weight-based dosing |
| `anticipate_blood_products` | Crossmatch units, transfusion thresholds, cell saver recommendation |
| `generate_surgical_checklist` | WHO Surgical Safety Checklist auto-populated with patient-specific safety flags |
| `generate_patient_education` | Plain-language pre-op instructions (fasting, medications, what to bring) |

### Multimodal

| Tool | What It Does |
|------|-------------|
| `parse_prior_operative_note` | Parses a prior surgical PDF — extracts difficult-airway history, drug allergies with severity, intra-op hemodynamics (CPB time, LVEF, peak creatinine), transfusion history, and post-op complications (AFib, AKI, pneumonia, VTE). Each finding is mapped to a concrete pre-op implication with severity. Accepts FHIR `DocumentReference`, base64 PDF, or raw text. |

### Orchestration

| Tool | What It Does |
|------|-------------|
| `generate_preop_clearance_report` | Runs ALL assessments in one call → complete pre-op clearance report with escalation flags |

---

## Example: High-Risk Patient

**Patient:** 65-year-old male, scheduled for AAA repair

**Conditions:** Heart failure, CAD, prior MI, atrial fibrillation, Type 2 diabetes, hypertension, obstructive sleep apnea, CKD stage 3, history of TIA

**What PreOp Intelligence catches:**

| Finding | Clinical Significance |
|---------|----------------------|
| RCRI 5/6 | >15% major cardiac event risk — cardiology consult needed |
| CHA₂DS₂-VASc 7/9 | 11.2% annual stroke risk — needs bridging anticoagulation |
| Warfarin: hold April 26 | Exactly 5 days before May 1 surgery |
| Insulin: reduce 25% | Kidneys can't clear insulin (eGFR 34.3) |
| Hemoglobin 10.1 | Anemia — crossmatch 4 units pRBC |
| INR 2.6 | Must correct before surgery |
| BNP 520 | Active heart failure — optimize before proceeding |
| BMI 36.2 + Neck 43cm | Difficult airway — video laryngoscope ready |
| Penicillin anaphylaxis | Use Clindamycin, not standard Cefazolin |
| FRAIL 3/5 | Frail — discuss goals of care, consider prehabilitation |

**Any single missed item could cause serious complications or death.**

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Clinical Logic | Python 3.13 — pure functions, no framework dependency |
| MCP Server | FastMCP 3.x with SHARP-on-MCP FHIR context |
| A2A Agent | Google ADK + a2a-sdk with Gemini 3.1 Pro |
| FHIR Client | httpx — async, supports any FHIR R4 server |
| Deployment | Google Cloud Run (auto-scaling, HTTPS) |
| CI/CD | GitHub Actions — lint (ruff) + 39 tests + auto-deploy |
| Data | 100% synthetic (Synthea-compatible FHIR R4 bundles) |
| Platform | Prompt Opinion (promptopinion.ai) |

---

## Project Structure

```
preop-intelligence/
├── src/
│   ├── mcp_server/           # MCP Server (FastMCP)
│   │   ├── app.py            # FastMCP instance + FHIR context extension
│   │   ├── server.py         # Entry point, registers all tools
│   │   ├── fhir_client.py    # FHIR R4 client (headers + local bundles)
│   │   ├── models.py         # Pydantic data models
│   │   └── tools/            # 16 MCP tool implementations
│   ├── scoring/              # Pure clinical logic (shared by MCP + A2A)
│   │   ├── calculators.py    # 7 advanced scoring systems
│   │   ├── drug_intelligence.py  # Interactions, renal dosing, allergies
│   │   └── clinical_protocols.py # Antibiotics, blood, frailty, education
│   └── data/
│       ├── synthetic_patients/   # 4 FHIR R4 test bundles
│       └── medication_knowledge_base.json  # 35 drugs, 8 categories
├── preop_agent/              # A2A Agent (Google ADK)
│   ├── agent.py              # Agent definition + Gemini 3.1 Pro
│   ├── app.py                # A2A app with 16 skills
│   └── tools/                # A2A tool wrappers
├── shared/                   # A2A infrastructure (from po-adk-python)
├── tests/                    # 39 tests (pytest)
├── Dockerfile                # MCP Server container
├── Dockerfile.a2a            # A2A Agent container
└── .github/workflows/        # CI (lint + test) + CD (Cloud Run deploy)
```

---

## Running Locally

### MCP Server

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Start server
python -m src.mcp_server.server
```

### A2A Agent

```bash
# Install
pip install -r requirements-a2a.txt

# Set API key
export GOOGLE_API_KEY=your-key
export GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Start agent
uvicorn preop_agent.app:a2a_app --host 0.0.0.0 --port 8004
```

---

## Deploying to Cloud Run

### MCP Server
```bash
gcloud run deploy preop-mcp-server --source . --region us-central1 --allow-unauthenticated
```

### A2A Agent
```bash
# Use Dockerfile.a2a
mv Dockerfile Dockerfile.mcp && mv Dockerfile.a2a Dockerfile
gcloud run deploy preop-agent --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=your-key,GOOGLE_GENAI_USE_VERTEXAI=FALSE"
mv Dockerfile Dockerfile.a2a && mv Dockerfile.mcp Dockerfile
```

---

## Registering on Prompt Opinion

### MCP Server
1. Configuration → MCP Servers → Add
2. Endpoint: `https://preop-mcp-server-xxx.run.app/mcp`
3. Transport: Streamable HTTP
4. Requires Patient Data Access: ON
5. Test → Should show all 16 tools

### A2A Agent
1. Agents → External Agents → Add Connection
2. Agent Card URL: `https://preop-agent-xxx.run.app/.well-known/agent-card.json`
3. Should discover 16 skills

---

## Judging Criteria Alignment

### The AI Factor
> Does the solution leverage Generative AI to address a challenge that traditional rule-based software cannot?

**Hybrid by design — deterministic where accuracy is life-or-death, generative where reasoning is required.**

- **11 validated scoring systems** (RCRI, Caprini, STOP-BANG, CHA₂DS₂-VASc, MELD-Na, Wells, HEART, LEMON, GCS, P-POSSUM, ASA) encoded as pure Python. Every number is traceable to peer-reviewed literature. No LLM guessing on scores.
- **Gemini 3.1 Pro** picks which of the 16 tools to run for a given clinical question, synthesizes the output into a cohesive clearance narrative, and reads unstructured PDFs that pure rule-based systems can't touch.
- **Multimodal PDF op-note parsing** pulls 4 life-critical findings (difficult-airway history, post-op AFib, peri-op AKI, transfusion history) from scans that currently sit unread in every chart. Rule-based systems can't open a PDF.

Other marketplace agents that *only* use an LLM hallucinate dose adjustments; agents that *only* use rules can't read a prior op note. We do both, correctly.

### Potential Impact
> Does this address a significant pain point? Is there a clear hypothesis for improving outcomes, reducing costs, or saving time?

**300 million surgeries a year. Every single one needs this.**

- **Time:** 30-45 min of manual chart review → 30 seconds.
- **Safety:** Catches warfarin hold-date arithmetic errors, missed eGFR-dependent dose reductions, stale ECGs, difficult-airway histories buried in prior op PDFs, and β-lactam cross-reactivity that kills penicillin-allergic patients when the reflex antibiotic is Cefazolin. See `demo/DEMO_SCRIPT.md` — any single missed item could kill the patient.
- **Scale:** Unlike niche agents (Abuja-specific intake, ASD caregiver support, specialty prior-auth), pre-op clearance is a universal workflow that every surgical patient in every hospital needs before every procedure.

### Feasibility
> Could this exist in a real healthcare system today? Does architecture respect data privacy, safety standards, and regulatory constraints?

**Production-ready, not demoware.**

- **FHIR R4 native** — mandatory for US healthcare since 2020; platform injects patient context via SHARP-on-MCP headers and A2A message metadata.
- **Peer-reviewed scoring only** — no invented scores; every calculator cites its source.
- **100% synthetic data** — no PHI in the repo; short-lived tokens in production.
- **Clinician-in-the-loop** — every response ends with "This is AI-generated decision support requiring clinician review." The agent *never* auto-approves clearance.
- **Deployed** — both MCP server and A2A agent live on Google Cloud Run with HTTPS, auto-scaling, GitHub Actions CI/CD, 39 unit tests, ruff lint.
- **Dual transport** — integrates with any MCP-compatible platform *and* any A2A-compatible orchestrator. No other agent in the marketplace ships both paths.

---

## License

MIT

---

*Built for the [Agents Assemble](https://agents-assemble.devpost.com/) hackathon on [Prompt Opinion](https://promptopinion.ai). Powered by [Google ADK](https://google.github.io/adk-docs/), [MCP](https://modelcontextprotocol.io/), and [Gemini 3.1 Pro](https://ai.google.dev/).*
