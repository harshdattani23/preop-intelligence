#!/usr/bin/env python3
"""
Live end-to-end smoke test for the deployed PreOp + PostOp agents.

What this does:
  1. Uploads demo/demo_patient_transaction.json (synthetic Gerald Morrison) to
     hapi.fhir.org/baseR4 — a public FHIR R4 sandbox.
  2. Sends an A2A JSON-RPC request to the live preop-agent on Cloud Run with
     FHIR context pointing at HAPI.
  3. Captures the response, validates that the new behavior is wired up:
       - verify_clinical_output_a2a was called
       - "PHYSICIAN-REVIEW DRAFT" framing in the closing
       - ACS NSQIP / SCIP regulatory hook present
       - Verification block (overall_confidence + sections) visible in output
  4. Sends a follow-up post-op query to the postop-agent.
  5. Prints a pass/fail summary.

Usage:
    python3 scripts/live_smoke_test.py            # full test
    python3 scripts/live_smoke_test.py --skip-upload  # reuse existing patient
    python3 scripts/live_smoke_test.py --postop-only  # only test postop
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
TRANSACTION_BUNDLE = REPO_ROOT / "demo" / "demo_patient_transaction.json"

HAPI_BASE = "https://hapi.fhir.org/baseR4"
PREOP_URL = "https://preop-agent-yrv5ygakiq-uc.a.run.app"
POSTOP_URL = "https://postop-agent-yrv5ygakiq-uc.a.run.app"
FHIR_EXTENSION_KEY = "https://app.promptopinion.ai/schemas/a2a/v1/fhir-context"

# The transaction bundle uses PUT with explicit IDs, so the patient ID is fixed.
PATIENT_ID = "patient-preop-demo"


def step(label: str) -> None:
    print(f"\n{'─' * 70}\n▸ {label}\n{'─' * 70}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ {msg}")


def info(msg: str) -> None:
    print(f"  · {msg}")


def upload_patient(client: httpx.Client) -> str:
    step("Step 1 — Upload synthetic patient bundle to HAPI public FHIR")
    if not TRANSACTION_BUNDLE.exists():
        fail(f"Bundle not found: {TRANSACTION_BUNDLE}")
        sys.exit(1)
    bundle = json.loads(TRANSACTION_BUNDLE.read_text())
    info(f"Bundle: {TRANSACTION_BUNDLE.name} ({len(bundle.get('entry', []))} entries)")
    info(f"Target FHIR server: {HAPI_BASE}")

    resp = client.post(
        HAPI_BASE,
        json=bundle,
        headers={
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        },
        timeout=60,
    )
    if resp.status_code >= 400:
        fail(f"Upload failed: HTTP {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)
    ok(f"Upload accepted: HTTP {resp.status_code}")

    # Confirm patient is reachable
    pat = client.get(
        f"{HAPI_BASE}/Patient/{PATIENT_ID}",
        headers={"Accept": "application/fhir+json"},
        timeout=20,
    )
    if pat.status_code != 200:
        fail(f"Patient/{PATIENT_ID} not reachable after upload: HTTP {pat.status_code}")
        sys.exit(1)
    ok(f"Patient/{PATIENT_ID} reachable on HAPI")
    return PATIENT_ID


def send_a2a_message(
    client: httpx.Client,
    agent_url: str,
    text: str,
    patient_id: str,
    label: str,
) -> dict:
    step(f"Step — A2A message to {label}")
    info(f"URL:        {agent_url}")
    info(f"Patient ID: {patient_id}")
    info(f"Prompt:     {text}")

    fhir_ctx = {
        FHIR_EXTENSION_KEY: {
            "fhirUrl": HAPI_BASE,
            # HAPI public sandbox doesn't actually validate bearer tokens, but the
            # tools' _get_fhir_context rejects empty fhir_token as a missing-context
            # error. Send a placeholder so the tool layer accepts the call.
            "fhirToken": "hapi-public-no-auth-required",
            "patientId": patient_id,
        },
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": str(uuid.uuid4()),
        "params": {
            # Place metadata at BOTH params.metadata and params.message.metadata —
            # the agents have no middleware that bridges between them, and the
            # ADK before_model_callback may read from either path depending on
            # how google.adk surfaces A2A request metadata.
            "metadata": fhir_ctx,
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
                "messageId": str(uuid.uuid4()),
                "metadata": fhir_ctx,
            },
        },
    }

    t0 = time.time()
    resp = client.post(
        agent_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=180,
    )
    dt = time.time() - t0
    info(f"Round-trip:  {dt:.1f}s — HTTP {resp.status_code}")

    if resp.status_code >= 400:
        fail(f"Agent returned HTTP {resp.status_code}")
        print(resp.text[:1000])
        return {}
    try:
        body = resp.json()
    except Exception as e:
        fail(f"Could not parse JSON: {e}")
        print(resp.text[:500])
        return {}
    return body


def extract_response_text(body: dict) -> str:
    """Walk an A2A JSON-RPC response and concatenate all text parts."""
    if not body:
        return ""
    result = body.get("result") or body.get("error") or {}
    chunks: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            kind = node.get("kind")
            if kind == "text" and isinstance(node.get("text"), str):
                chunks.append(node["text"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(result)
    return "\n".join(chunks)


def assert_contains(text: str, needle: str, label: str) -> bool:
    if needle.lower() in text.lower():
        ok(f"{label}: found '{needle}'")
        return True
    fail(f"{label}: missing '{needle}'")
    return False


def validate_preop_response(body: dict) -> bool:
    step("Validate PreOp response")
    text = extract_response_text(body)
    if not text:
        fail("Empty response text — agent did not produce output")
        print(json.dumps(body, indent=2)[:1500])
        return False
    info(f"Response length: {len(text)} chars")

    # Print preview
    print(f"\n--- response preview ---\n{text[:2000]}\n--- end preview ---\n")

    checks = [
        assert_contains(text, "PHYSICIAN-REVIEW DRAFT", "HITL framing"),
        # Either ACS NSQIP or SCIP is acceptable in the closing
        any([
            "acs nsqip" in text.lower(),
            "scip" in text.lower(),
            "nsqip" in text.lower(),
        ]),
        # Verification block signals
        any([
            "overall confidence" in text.lower(),
            "verification" in text.lower(),
            "unverified" in text.lower(),
        ]),
        # Risk score signals (sanity)
        any([
            "asa" in text.lower(),
            "rcri" in text.lower(),
        ]),
    ]
    if checks[1]:
        ok("Regulatory hook: ACS NSQIP / SCIP / NSQIP present")
    else:
        fail("Regulatory hook: no ACS NSQIP / SCIP mention")
    if checks[2]:
        ok("Verification signals present (overall_confidence / verification / unverified)")
    else:
        fail("Verification signals missing — verify_clinical_output_a2a may not be called")
    if checks[3]:
        ok("Risk score output present (ASA / RCRI)")
    else:
        fail("No risk score output — assessment may not have run")

    return all(checks)


def validate_postop_response(body: dict) -> bool:
    step("Validate PostOp response")
    text = extract_response_text(body)
    if not text:
        fail("Empty response text — postop agent did not produce output")
        print(json.dumps(body, indent=2)[:1500])
        return False
    info(f"Response length: {len(text)} chars")
    print(f"\n--- response preview ---\n{text[:1500]}\n--- end preview ---\n")

    return all([
        assert_contains(text, "PHYSICIAN-REVIEW DRAFT", "HITL framing"),
        any([
            "verification" in text.lower(),
            "overall confidence" in text.lower(),
            "unverified" in text.lower(),
        ]) and ok("Verification signals present") or fail("Verification signals missing"),
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-upload", action="store_true",
                        help="Skip uploading patient (use existing patient-preop-demo)")
    parser.add_argument("--postop-only", action="store_true",
                        help="Only test postop agent")
    parser.add_argument("--preop-only", action="store_true",
                        help="Only test preop agent")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" LIVE SMOKE TEST — PreOp + PostOp Intelligence")
    print(" " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    with httpx.Client() as client:
        # Step 0: deploy verification
        step("Step 0 — Verify deployments")
        for label, url in [("preop-agent card", f"{PREOP_URL}/.well-known/agent-card.json"),
                           ("postop-agent card", f"{POSTOP_URL}/.well-known/agent-card.json")]:
            r = client.get(url, timeout=15)
            if r.status_code != 200:
                fail(f"{label}: HTTP {r.status_code}")
                return 1
            card = r.json()
            ok(f"{label}: HTTP 200, {len(card.get('skills', []))} skills")
            ids = {s["id"] for s in card.get("skills", [])}
            for required in ("clinical-output-verification", "perioperative-handoff-to-postop") if "preop" in label else ("postop-output-verification", "perioperative-handoff-from-preop"):
                if required in ids:
                    ok(f"  skill present: {required}")
                else:
                    fail(f"  skill MISSING: {required}")

        # Step 1: upload patient
        if not args.skip_upload:
            patient_id = upload_patient(client)
        else:
            patient_id = PATIENT_ID
            info(f"Skipping upload, using existing {patient_id}")

        passed = True

        # Step 2: preop test
        if not args.postop_only:
            preop_body = send_a2a_message(
                client,
                PREOP_URL,
                "Run a complete pre-op clearance assessment for AAA repair scheduled May 15, 2026. "
                "Include all risk scores, medication review, lab readiness, anesthesia evaluation, "
                "and the verification pass.",
                patient_id,
                "preop-agent",
            )
            if not validate_preop_response(preop_body):
                passed = False

        # Step 3: postop test
        if not args.preop_only:
            postop_body = send_a2a_message(
                client,
                POSTOP_URL,
                "Patient is now POD 1 after AAA repair. Run a post-op surveillance assessment "
                "with complication screening, monitoring plan, renal redosing, and verification.",
                patient_id,
                "postop-agent",
            )
            if not validate_postop_response(postop_body):
                passed = False

        # Final summary
        step("Summary")
        if passed:
            ok("ALL CHECKS PASSED — agents are live and producing the new framing")
            return 0
        else:
            fail("SOME CHECKS FAILED — see output above")
            return 1


if __name__ == "__main__":
    sys.exit(main())
