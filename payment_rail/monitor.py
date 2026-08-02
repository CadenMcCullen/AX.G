import json
from .guardrail import ResponseStatus

class NISTGovernanceMonitor:
    """
    Tracks system performance and integrity metrics without capturing or logging
    customer data (PII/PAN) in compliance with NIST AI RMF 1.0 guidelines.
    """

    def __init__(self):
        self.total_processed = 0
        self.successful_settlements = 0
        self.rejected_requests = 0

    def record_execution(self, status: ResponseStatus, ref_id: str):
        self.total_processed += 1
        if status == ResponseStatus.SETTLEMENT_SUCCESSFUL:
            self.successful_settlements += 1
        else:
            self.rejected_requests += 1

        telemetry_data = {
            "ref_id": ref_id,
            "status": status.value,
            "total_processed": self.total_processed,
            "success_rate": f"{(self.successful_settlements / self.total_processed) * 100:.2f}%" if self.total_processed > 0 else "0.00%"
        }
        # ZERO PII / ZERO PAN TELEMETRY LOG
        print(f"[NIST_RMF_TELEMETRY]: {json.dumps(telemetry_data)}")
