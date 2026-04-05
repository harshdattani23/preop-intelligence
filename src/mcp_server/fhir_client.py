"""FHIR R4 client — reads credentials from HTTP headers (SHARP-on-MCP) or local bundles."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic_patients"

LOCAL_PATIENT_MAP = {
    "patient-a": "patient_a_low_risk.json",
    "patient-b": "patient_b_medium_risk.json",
    "patient-c": "patient_c_high_risk.json",
    "patient-d": "patient_d_edge_case.json",
}

# SHARP-on-MCP header names
HEADER_FHIR_URL = "x-fhir-server-url"
HEADER_FHIR_TOKEN = "x-fhir-access-token"
HEADER_PATIENT_ID = "x-patient-id"


def get_fhir_context_from_headers() -> tuple[str | None, str | None, str | None]:
    """Extract FHIR context from HTTP request headers (SHARP-on-MCP).

    Returns (fhir_url, fhir_token, patient_id) or (None, None, None) if not available.
    """
    try:
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        fhir_url = request.headers.get(HEADER_FHIR_URL)
        fhir_token = request.headers.get(HEADER_FHIR_TOKEN)
        patient_id = request.headers.get(HEADER_PATIENT_ID)
        if fhir_url:
            logger.info("FHIR context from headers: url=%s patient=%s", fhir_url, patient_id)
        return fhir_url, fhir_token, patient_id
    except (RuntimeError, LookupError):
        return None, None, None


class FHIRClient:
    """Dual-mode FHIR client: remote server (via headers or explicit URL) or local bundles."""

    def __init__(
        self,
        base_url: str | None = None,
        fhir_token: str | None = None,
        local_bundle_path: str | None = None,
    ):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.fhir_token = fhir_token
        self._local_bundle: dict | None = None

        if local_bundle_path:
            self._load_bundle(local_bundle_path)

    @classmethod
    def from_headers(cls) -> tuple["FHIRClient", str | None]:
        """Create a FHIRClient from SHARP-on-MCP HTTP headers.

        Returns (client, patient_id). Falls back to local bundles if no headers.
        """
        fhir_url, fhir_token, patient_id = get_fhir_context_from_headers()
        if fhir_url:
            return cls(base_url=fhir_url, fhir_token=fhir_token), patient_id
        return cls(), patient_id

    def _load_bundle(self, path: str) -> None:
        with open(path) as f:
            self._local_bundle = json.load(f)

    def _load_local_patient(self, patient_id: str) -> bool:
        if self._local_bundle:
            return True
        filename = LOCAL_PATIENT_MAP.get(patient_id)
        if filename and (DATA_DIR / filename).exists():
            self._load_bundle(str(DATA_DIR / filename))
            return True
        return False

    def _get_resources_by_type(self, resource_type: str) -> list[dict]:
        if not self._local_bundle:
            return []
        entries = self._local_bundle.get("entry", [])
        return [
            e["resource"]
            for e in entries
            if e.get("resource", {}).get("resourceType") == resource_type
        ]

    def _build_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/fhir+json"}
        if self.fhir_token:
            headers["Authorization"] = f"Bearer {self.fhir_token}"
        return headers

    async def _fetch(self, url: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(3):
                try:
                    resp = await client.get(url, headers=self._build_headers())
                    resp.raise_for_status()
                    return resp.json()
                except (httpx.HTTPError, httpx.TimeoutException):
                    if attempt == 2:
                        return None

    async def _search(self, resource_type: str, params: dict[str, str]) -> list[dict]:
        if not self.base_url:
            return []
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.base_url}/{resource_type}?{query}&_count=100"
        results = []
        while url:
            data = await self._fetch(url)
            if not data:
                break
            for entry in data.get("entry", []):
                if "resource" in entry:
                    results.append(entry["resource"])
            url = None
            for link in data.get("link", []):
                if link.get("relation") == "next":
                    url = link["url"]
                    break
        return results

    async def get_patient(self, patient_id: str) -> dict | None:
        if self.base_url:
            return await self._fetch(f"{self.base_url}/Patient/{patient_id}")
        if self._load_local_patient(patient_id):
            patients = self._get_resources_by_type("Patient")
            return patients[0] if patients else None
        return None

    async def get_conditions(self, patient_id: str) -> list[dict]:
        if self.base_url:
            return await self._search("Condition", {"patient": patient_id})
        if self._load_local_patient(patient_id):
            return self._get_resources_by_type("Condition")
        return []

    async def get_medications(self, patient_id: str) -> list[dict]:
        if self.base_url:
            return await self._search("MedicationRequest", {"patient": patient_id, "status": "active"})
        if self._load_local_patient(patient_id):
            return self._get_resources_by_type("MedicationRequest")
        return []

    async def get_observations(
        self, patient_id: str, category: str | None = None, code: str | None = None
    ) -> list[dict]:
        if self.base_url:
            params: dict[str, str] = {"patient": patient_id}
            if category:
                params["category"] = category
            if code:
                params["code"] = code
            return await self._search("Observation", params)
        if self._load_local_patient(patient_id):
            obs = self._get_resources_by_type("Observation")
            if category:
                obs = [
                    o for o in obs
                    if any(
                        cat.get("coding", [{}])[0].get("code") == category
                        for cat in o.get("category", [])
                        if cat.get("coding")
                    )
                ]
            if code:
                obs = [
                    o for o in obs
                    if any(c.get("code") == code for c in o.get("code", {}).get("coding", []))
                ]
            return obs
        return []

    async def get_allergies(self, patient_id: str) -> list[dict]:
        if self.base_url:
            return await self._search("AllergyIntolerance", {"patient": patient_id})
        if self._load_local_patient(patient_id):
            return self._get_resources_by_type("AllergyIntolerance")
        return []

    async def get_procedures(self, patient_id: str) -> list[dict]:
        if self.base_url:
            return await self._search("Procedure", {"patient": patient_id})
        if self._load_local_patient(patient_id):
            return self._get_resources_by_type("Procedure")
        return []
