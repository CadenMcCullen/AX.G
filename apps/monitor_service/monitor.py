from payment_rail.monitor import NISTGovernanceMonitor
from payment_rail.guardrail import ResponseStatus

class MonitorService:
    """
    NIST AI RMF Governance telemetry service for privacy-preserving system auditing.
    """
    def __init__(self):
        self._governance_monitor = NISTGovernanceMonitor()

    def record_transaction(self, is_valid: bool, reference_id: str):
        """
        Logs a transaction execution status using strict zero-PII logging practices.
        """
        status = ResponseStatus.SETTLEMENT_SUCCESSFUL if is_valid else ResponseStatus.RAW_CREDENTIAL_REJECTED
        self._governance_monitor.record_execution(status, reference_id)
