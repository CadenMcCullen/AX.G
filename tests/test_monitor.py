import json
from payment_rail.monitor import NISTGovernanceMonitor
from payment_rail.guardrail import ResponseStatus

def test_nist_governance_monitor_logging(capsys):
    monitor = NISTGovernanceMonitor()

    # Log a valid execution
    monitor.record_execution(ResponseStatus.SETTLEMENT_SUCCESSFUL, ref_id="ref_aaa")
    captured = capsys.readouterr()

    assert "[NIST_RMF_TELEMETRY]:" in captured.out
    json_part = captured.out.split("[NIST_RMF_TELEMETRY]:")[1].strip()
    data = json.loads(json_part)

    assert data["ref_id"] == "ref_aaa"
    assert data["status"] == "SETTLEMENT_SUCCESSFUL"
    assert data["total_processed"] == 1
    assert data["success_rate"] == "100.00%"

    # Log an invalid execution
    monitor.record_execution(ResponseStatus.RAW_CREDENTIAL_REJECTED, ref_id="ref_bbb")
    captured = capsys.readouterr()

    json_part = captured.out.split("[NIST_RMF_TELEMETRY]:")[1].strip()
    data = json.loads(json_part)

    assert data["ref_id"] == "ref_bbb"
    assert data["status"] == "RAW_CREDENTIAL_REJECTED"
    assert data["total_processed"] == 2
    assert data["success_rate"] == "50.00%"
