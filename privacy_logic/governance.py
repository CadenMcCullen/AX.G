import json
import math
from typing import Dict, Any

class PipelineHaltedError(Exception):
    """Exception raised when the ledger pipeline is halted by the circuit breaker."""
    pass

class NISTGovernanceMonitor:
    """
    Implements NIST AI RMF Measure & Manage functions in the pipeline.
    Tracks technical integrity metrics while enforcing Zero-PII logging rules.
    """

    def __init__(self, failure_rate_threshold: float = 0.5, min_executions_for_threshold: int = 5):
        self.processed_count = 0
        self.validation_failures = 0
        self.is_halted = False
        self.failure_rate_threshold = failure_rate_threshold
        self.min_executions_for_threshold = min_executions_for_threshold
        self.telemetry_logs: list[Dict[str, Any]] = []

    @staticmethod
    def Calculate_Entropy(token: str) -> float:
        """
        Calculates Shannon entropy of the token string to measure randomness/entropy.
        Logs telemetry only, strictly zero-PII/PAN data exposure.
        """
        if not token:
            return 0.0
        # Character frequency distribution
        freq: Dict[str, int] = {}
        for char in token:
            freq[char] = freq.get(char, 0) + 1

        entropy = 0.0
        length = len(token)
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    def Log_Execution(self, request_valid: bool, ref_id: str, token_entropy: float = 0.0, latency_ms: float = 0.0):
        """
        Measures technical metrics (latency, token entropy, schema validation success rates).
        ZERO PII or PAN logging permitted.
        """
        if self.is_halted:
            raise PipelineHaltedError("Pipeline is currently halted by the circuit breaker.")

        self.processed_count += 1
        if not request_valid:
            self.validation_failures += 1

        failure_rate = self.validation_failures / self.processed_count

        # TELEMETRY RULE: Log only metric metadata, NEVER raw payloads or credentials
        telemetry_entry = {
            "ref_id": ref_id,
            "valid": request_valid,
            "total_processed": self.processed_count,
            "failure_rate": failure_rate,
            "token_entropy": round(token_entropy, 4),
            "latency_ms": round(latency_ms, 2)
        }
        self.telemetry_logs.append(telemetry_entry)
        self._write_sanitized_telemetry(telemetry_entry)

        # Check circuit breaker conditions based on failure rate
        if (self.processed_count >= self.min_executions_for_threshold
                and failure_rate >= self.failure_rate_threshold):
            self.Halt_Pipeline("Validation failure rate threshold exceeded.")

    def Halt_Pipeline(self, reason: str):
        """
        HALT mechanism (Manage function) to prevent processing under compromised states.
        """
        self.is_halted = True
        print(f"[NIST_RMF_MANAGE] CIRCUIT BREAKER TRIGGERED: {reason}")

    def Reset_Pipeline(self):
        """Resets the circuit breaker and metrics."""
        self.is_halted = False
        self.processed_count = 0
        self.validation_failures = 0
        self.telemetry_logs = []

    def _write_sanitized_telemetry(self, data: dict):
        # Writes directly to sanitized application metrics store
        print(f"[NIST_RMF_MEASURE]: {json.dumps(data)}")
