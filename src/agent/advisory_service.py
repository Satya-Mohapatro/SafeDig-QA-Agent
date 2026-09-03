import os
import json
import socket
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.domain.document import Document
from src.domain.reconciliation import ReconciliationResult
from src.domain.evidence import EvidencePackage
from src.domain.policy import PolicyResult
from src.domain.enums import ReconciliationOutcome, Severity
from src.agent.models import AdvisorySummary
from src.config.settings import settings
from src.config.logging import logger

class LLMAdvisoryService:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout_sec: Optional[float] = None
    ):
        self.endpoint = endpoint or settings.llm_endpoint
        self.model = model or settings.llm_model
        self.timeout_sec = timeout_sec or settings.llm_timeout_sec
        self.enabled = settings.enable_llm_advisory

    def _is_endpoint_reachable(self) -> bool:
        try:
            parsed = urllib.parse.urlparse(self.endpoint)
            host = parsed.hostname or "localhost"
            port = parsed.port or (11434 if "11434" in self.endpoint else 80)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)  # Fast 200ms probe
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def generate_advisory(
        self,
        document: Optional[Document],
        reconciliation: ReconciliationResult,
        evidence_pkg: Optional[EvidencePackage],
        policy_result: PolicyResult
    ) -> AdvisorySummary:
        doc_id = document.document_id if document else reconciliation.document_id
        
        # 1. If LLM is disabled by configuration, immediately use deterministic generator
        if not self.enabled:
            return self._generate_deterministic_advisory(doc_id, document, reconciliation, evidence_pkg, policy_result)
            
        # 2. Fast probe: check if local server is listening before sending payload
        if not self._is_endpoint_reachable():
            return self._generate_deterministic_advisory(doc_id, document, reconciliation, evidence_pkg, policy_result)
            
        # 3. Attempt local LLM call (e.g. Ollama / vLLM API)
        try:
            prompt = self._build_advisory_prompt(doc_id, document, reconciliation, evidence_pkg, policy_result)
            response_json = self._call_local_llm_api(prompt)
            if response_json and isinstance(response_json, dict):
                return AdvisorySummary(
                    document_id=doc_id,
                    summary=response_json.get("summary", "Automated LLM summary generated."),
                    contradictions_detected=response_json.get("contradictions_detected", []),
                    recommended_evidence_ids=response_json.get("recommended_evidence_ids", []),
                    reviewer_guidance=response_json.get("reviewer_guidance", "Review highlighted evidence before signoff."),
                    model_name=self.model,
                    is_fallback=False,
                    confidence_assessment=response_json.get("confidence_assessment", "Model Evaluation 1.0"),
                    generated_at=datetime.utcnow().isoformat()
                )
        except Exception as e:
            logger.info(f"Local LLM inference call error ({e}). Using deterministic advisory fallback.")
            
        # 4. Fallback gracefully to deterministic structured reasoning (100% resilient)
        return self._generate_deterministic_advisory(doc_id, document, reconciliation, evidence_pkg, policy_result)

    def _build_advisory_prompt(
        self,
        doc_id: str,
        document: Optional[Document],
        reconciliation: ReconciliationResult,
        evidence_pkg: Optional[EvidencePackage],
        policy_result: PolicyResult
    ) -> str:
        ev_items = []
        if evidence_pkg:
            for it in evidence_pkg.items:
                ev_items.append({"id": it.evidence_id, "type": it.evidence_type, "desc": it.description})
                
        payload = {
            "document_id": doc_id,
            "filename": document.filename if document else "N/A",
            "reconciliation_outcome": reconciliation.outcome.value,
            "upstream_claim": reconciliation.claimed_warning.raw_warning_text if reconciliation.claimed_warning else None,
            "independent_findings_count": len(reconciliation.detected_candidates),
            "policy_decision": policy_result.decision.value,
            "policy_reason": policy_result.reason,
            "evidence_items": ev_items
        }
        
        system_instruction = (
            "You are an advisory QA assistant for underground utility map validation. "
            "Your role is ONLY to summarize deterministic findings, highlight contradictions, and recommend specific evidence IDs for human review. "
            "You CANNOT authorize release, override policy, or alter severity. Return JSON only with fields: "
            "summary (str), contradictions_detected (list of str), recommended_evidence_ids (list of str), reviewer_guidance (str)."
        )
        
        return f"{system_instruction}\n\nInput Case Data:\n{json.dumps(payload, indent=2)}"

    def _call_local_llm_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        url = f"{self.endpoint.rstrip('/')}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
            body = resp.read().decode("utf-8")
            res_obj = json.loads(body)
            response_text = res_obj.get("response", "")
            return json.loads(response_text)

    def _generate_deterministic_advisory(
        self,
        doc_id: str,
        document: Optional[Document],
        reconciliation: ReconciliationResult,
        evidence_pkg: Optional[EvidencePackage],
        policy_result: PolicyResult
    ) -> AdvisorySummary:
        outcome = reconciliation.outcome
        contradictions: List[str] = []
        rec_ev_ids: List[str] = []
        
        if evidence_pkg:
            rec_ev_ids = [it.evidence_id for it in evidence_pkg.items if it.evidence_type in ["SPATIAL_INTERSECTION", "MAP_CROP"]]
            if not rec_ev_ids and evidence_pkg.items:
                rec_ev_ids = [evidence_pkg.items[0].evidence_id]

        finding_name = (
            reconciliation.detected_candidates[0].business_warning_text
            if reconciliation.detected_candidates
            else "unspecified hazard"
        )

        if outcome == ReconciliationOutcome.MISSED_WARNING:
            count = len(reconciliation.detected_candidates)
            summary = f"CRITICAL HAZARD DETECTED: Upstream system reported clean, but independent scan discovered {count} hazard(s) ({finding_name})."
            contradictions.append(f"Upstream reported NO WARNING vs Independent scan detected '{finding_name}'")
            guidance = "Verify spatial intersection against digsite boundary and confirm asset existence on drawing before releasing."
            
        elif outcome == ReconciliationOutcome.POSSIBLE_FALSE_POSITIVE:
            claim_text = reconciliation.claimed_warning.raw_warning_text if reconciliation.claimed_warning else "Unknown Claim"
            summary = f"POTENTIAL FALSE ALARM: Upstream claimed '{claim_text}', but independent QA found no intersecting vector or raster assets."
            contradictions.append(f"Upstream claimed '{claim_text}' with no corroborating physical assets in the AOI.")
            guidance = "Inspect original PDF drawing to confirm whether plant is genuinely absent or if a non-standard symbology was used."
            
        elif outcome == ReconciliationOutcome.MATCH:
            summary = f"CONFIRMED HAZARD MATCH: Both upstream claim and independent scan identified {finding_name}."
            guidance = "Corroborate buffer tolerance and review high-voltage / high-pressure safety precautions."
            
        else:
            summary = "CONFIRMED CLEAN: Upstream and independent verification confirm no conflicting hazards in the AOI."
            guidance = "All deterministic safety checks passed."

        return AdvisorySummary(
            document_id=doc_id,
            summary=summary,
            contradictions_detected=contradictions,
            recommended_evidence_ids=rec_ev_ids,
            reviewer_guidance=guidance,
            model_name="deterministic_rule_assistant",
            is_fallback=True,
            confidence_assessment="Deterministic Rule-Based Confidence 1.0",
            generated_at=datetime.utcnow().isoformat()
        )

advisory_service = LLMAdvisoryService()
