import json

class NISTGovernanceMonitor:
    def __init__(self):
        self.processed_count = 0
        self.validation_failures = 0

    def Log_Execution(self, request_valid: bool, ref_id: str):
        self.processed_count += 1
        if not request_valid:
            self.validation_failures += 1

        telemetry_entry = {
            "ref_id": ref_id,
            "valid": request_valid,
            "total_processed": self.processed_count,
            "failure_rate": self.validation_failures / self.processed_count if self.processed_count > 0 else 0.0
        }
        # ZERO PII / ZERO PAN LOGGING RULE ENFORCED
        print(f"[NIST_RMF_MEASURE]: {json.dumps(telemetry_entry)}")
