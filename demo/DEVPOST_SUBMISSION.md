# PreOp Intelligence — Devpost Submission Copy

Use this verbatim for the Devpost form fields. Tighter and more provocative
than the README; designed for skim-reading by judges (Cleveland Clinic
anesthesiologist Piyush Mathur is on the panel).

---

## Tagline (140 chars max for Devpost banner)

> Pre-op clearance and post-op monitoring in 30 seconds, not 30 minutes — with every score cited from the literature.

---

## Elevator pitch (≤200 chars, used in marketplace cards)

> Two A2A agents that read your patient's FHIR record, parse PDF op notes, and produce evidence-cited perioperative plans. 22 skills, 11 validated scores, every citation.

---

## Inspiration

300 million surgeries a year. Every single one needs pre-op clearance. The
process today is a resident on hour six of chart review trying to compute
RCRI, Caprini, and STOP-BANG by hand while remembering whether *this*
patient's penicillin allergy is "rash" or "anaphylaxis." Misses cause death:
wrong warfarin hold date → bleeding on the table; missed difficult-airway
PDF → can't intubate; reflex Cefazolin in a true PCN-anaphylaxis →
arrest before the first cut.

We built the agent that reads everything, computes everything, and shows
its work.

## What it does

Two agents that compose in a single Prompt Opinion conversation:

**PreOp Intelligence** — pulls the patient's FHIR record, computes 11
validated scores (ASA, RCRI, Caprini, STOP-BANG, CHA₂DS₂-VASc, MELD-Na,
Wells, HEART, LEMON, GCS, P-POSSUM), drug-interaction-checks the active
med list, calculates anticoagulant hold dates against the surgery date,
re-doses every drug against eGFR, screens cross-reactivity for
allergies, picks the right antibiotic prophylaxis, and parses prior
operative-note PDFs for difficult-airway history, prior anesthesia
events, transfusion needs, and post-op AKI/AFib history.

**PostOp Monitor** — handoff in the same chat. Screens for the four
complications driving most post-op morbidity (AKI, new-onset AFib,
delirium, pulmonary), generates a surgery- and ASA-driven monitoring
plan with red-flag thresholds, and re-doses every medication for the
patient's current renal trajectory.

Every numerical score in the trace ships with its primary literature
citation: RCRI is `Lee TH, Circulation 1999`; STOP-BANG is `Chung F,
Anesthesiology 2008`; KDIGO AKI staging is `Kidney Int Suppl 2012`.

## How we built it

- **Stack:** Google ADK, Gemini, A2A protocol, FastMCP, FHIR R4, deployed
  on Google Cloud Run.
- **Density:** 22 advertised skills across two agents. Pure-Python scoring
  logic in `src/scoring/` reused by both MCP server and both A2A agents.
- **Multimodal:** Operative-note PDFs are parsed into 7 structured
  finding types (airway, allergy, intra-op events, post-op complications,
  hemodynamics, transfusion, future-procedure notes). Each finding maps
  to a concrete pre-op or post-op implication.
- **Evidence:** Every scoring function is paired with its derivation paper
  in `src/scoring/citations.py`; the citation is injected into the score's
  JSON output so it lands in the Prompt Opinion trace panel.
- **Composition:** Two Cloud Run services, two agent cards, both
  registered as External Agents on the Prompt Opinion marketplace. State
  (FHIR context, surgery type, allergies, prior op note) is preserved
  across the preop → postop handoff.
- **CI/CD:** GitHub Actions deploys all three services (MCP, preop-agent,
  postop-agent) on every push to main. 52 tests, ruff clean.

## Challenges we ran into

- `a2a-sdk 1.0` released mid-build and broke `google-adk`'s import paths.
  Pinned both to the pre-1.0 line and shimmed the `In` enum.
- Synthea-generated synthetic patients have inconsistent SNOMED coding for
  the same condition (e.g., HTN can be 38341003 or 59621000); built code-set
  unions per condition class.
- Anesthesiologist-grade output requires citations; built a centralized
  registry rather than inline strings so updates are atomic.

## Accomplishments we're proud of

- Two agents with **22 skills** combined — 2-3× denser than every other
  marketplace competitor.
- **11 validated scoring systems**, all from peer-reviewed literature, all
  with citations visible in trace.
- **Multimodal PDF parsing** for prior operative notes — closes the gap
  with proprietary clinical-AI products.
- **Same-chat preop → postop handoff** — uniquely demonstrates the A2A
  composition story the marketplace was built for.
- **Live and registered** on the Prompt Opinion marketplace.

## What's next

- Cardiology and oncology workflow companions (consult prep, treatment
  selection) reusing the same FHIR + scoring + citation infrastructure.
- Streaming response for long traces (the multi-tool clearance call returns
  in seconds, but UX feedback during would help).
- HL7 SMART-on-FHIR launch context so EHRs can embed the agent directly.

---

## Built with

Google ADK · Gemini · A2A Protocol · FastMCP · FHIR R4 · Python 3.13 ·
Google Cloud Run · GitHub Actions · pytest · ruff · pypdf

## Try it out

- Repo: https://github.com/harshdattani23/preop-intelligence
- PreOp agent card: https://preop-agent-yrv5ygakiq-uc.a.run.app/.well-known/agent-card.json
- PostOp agent card: https://postop-agent-yrv5ygakiq-uc.a.run.app/.well-known/agent-card.json
- MCP server: https://preop-mcp-server-yrv5ygakiq-uc.a.run.app/mcp

---

## Judging-criteria cheat sheet (one paragraph each, for the form)

**Innovation:** We're not the first FHIR agent on this marketplace, but we
are the first to combine literature-cited validated scoring, multimodal
PDF parsing of prior operative notes, *and* multi-agent composition (preop
+ postop) in a single conversation. The PDF parser is the unique edge —
operative notes live in the chart and nobody reads them.

**Technical complexity:** 22 advertised skills across two agents, 11
clinical scoring algorithms implemented in pure Python (not LLM-generated),
FHIR R4 client, PDF parser, drug-interaction graph, renal-dose calculator,
allergy cross-reactivity table. Both MCP and A2A protocols served from the
same scoring module. CI/CD deploys three services to Cloud Run on every
push.

**Practicality:** A pre-op clearance takes a resident 30-45 minutes. We do
it in 30 seconds and don't miss the warfarin hold date, the difficult-airway
PDF history, or the penicillin → Cefazolin trap. The post-op companion
catches AKI and new-onset AFib early. This deploys today inside any
EHR with a FHIR endpoint.

**Design:** Tabular, structured, evidence-cited output. Every clinical
recommendation ends with *"AI-generated decision support requiring
clinician review."* Trace panel shows tool-by-tool reasoning so an
anesthesiologist can audit any number we surface.
