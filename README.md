# PreOp Intelligence

**Perioperative Risk Assessment & Optimization System**

> The only AI agent on the Prompt Opinion marketplace that performs comprehensive pre-operative surgical assessments — 15 clinical tools, 11 validated scoring systems, and complete perioperative workflow automation.

Built for the [Agents Assemble](https://agents-assemble.devpost.com/) Healthcare AI Hackathon.

---

## What It Does

PreOp Intelligence automates the entire pre-operative clearance process — a workflow that currently takes clinicians 30-45 minutes of manual chart review per patient. Given a patient's FHIR health record, it produces a complete surgical risk assessment in seconds.

**Input:** A patient record on any FHIR R4 server + a planned surgery type and date

**Output:** Comprehensive pre-operative clearance report with risk scores, medication management plan, lab assessment, anesthesia evaluation, drug interaction check, surgical safety checklist, and patient education materials

## Demo

**Live on Prompt Opinion Marketplace:** [View Agent →](https://app.promptopinion.ai/marketplace)

**MCP Server Endpoint:** `https://preop-mcp-server-424758858331.us-central1.run.app/mcp`

**A2A Agent Card:** `https://preop-agent-424758858331.us-central1.run.app/.well-known/agent-card.json`

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
    │  15 Tools    │                   │  14 Skills     │
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

## 15 Clinical Tools

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
| CI/CD | GitHub Actions — lint (ruff) + 28 tests + auto-deploy |
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
│   │   └── tools/            # 15 MCP tool implementations
│   ├── scoring/              # Pure clinical logic (shared by MCP + A2A)
│   │   ├── calculators.py    # 7 advanced scoring systems
│   │   ├── drug_intelligence.py  # Interactions, renal dosing, allergies
│   │   └── clinical_protocols.py # Antibiotics, blood, frailty, education
│   └── data/
│       ├── synthetic_patients/   # 4 FHIR R4 test bundles
│       └── medication_knowledge_base.json  # 35 drugs, 8 categories
├── preop_agent/              # A2A Agent (Google ADK)
│   ├── agent.py              # Agent definition + Gemini 3.1 Pro
│   ├── app.py                # A2A app with 14 skills
│   └── tools/                # A2A tool wrappers
├── shared/                   # A2A infrastructure (from po-adk-python)
├── tests/                    # 28 tests (pytest)
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
5. Test → Should show all 15 tools

### A2A Agent
1. Agents → External Agents → Add Connection
2. Agent Card URL: `https://preop-agent-xxx.run.app/.well-known/agent-card.json`
3. Should discover 14 skills

---

## Judging Criteria Alignment

### The AI Factor
> Does the solution leverage Generative AI to address a challenge that traditional rule-based software cannot?

**Hybrid architecture:** 11 validated clinical scoring systems (deterministic, evidence-based) + Gemini 3.1 Pro synthesis (contextual clinical reasoning). The scoring is precise and auditable; the AI synthesizes findings across all assessments into a cohesive clinical narrative that a rule-based system cannot produce. The AI also decides which tools to invoke based on the clinical question — adaptive tool selection, not hard-coded workflows.

### Potential Impact
> Does this address a significant pain point? Is there a clear hypothesis for improving outcomes, reducing costs, or saving time?

**300+ million surgeries per year globally.** Each requires pre-operative assessment. Current process: 30-45 minutes of manual chart review per patient. PreOp Intelligence reduces this to 30 seconds. Catches medication conflicts (warfarin hold timing), missing labs, drug interactions, and airway risks that are commonly missed in manual reviews — directly preventing surgical complications and saving lives.

### Feasibility
> Could this exist in a real healthcare system today? Does architecture respect data privacy, safety standards, and regulatory constraints?

**Production-ready architecture:** FHIR R4 native (mandatory for US healthcare systems since 2020). Uses published, peer-reviewed scoring systems (RCRI, Caprini, STOP-BANG, CHA₂DS₂-VASc). 100% synthetic data — no PHI. All outputs are "decision support" with clinician-in-the-loop — never auto-approves clearance. SHARP-on-MCP compliant for credential handling. Deployed on Cloud Run with CI/CD, auto-scaling, and HTTPS.

---

## License

MIT

---

*Built for the [Agents Assemble](https://agents-assemble.devpost.com/) hackathon on [Prompt Opinion](https://promptopinion.ai). Powered by [Google ADK](https://google.github.io/adk-docs/), [MCP](https://modelcontextprotocol.io/), and [Gemini 3.1 Pro](https://ai.google.dev/).*
