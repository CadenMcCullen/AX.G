import json
from payment_rail.monitor import NISTGovernanceMonitor


def test_nist_governance_monitor_logging(capsys):
    monitor = NISTGovernanceMonitor()

    # Log a valid execution
    monitor.Log_Execution(request_valid=True, ref_id="ref_aaa")
    captured = capsys.readouterr()

    assert "[NIST_RMF_MEASURE]:" in captured.out
    json_part = captured.out.split("[NIST_RMF_MEASURE]:")[1].strip()
    data = json.loads(json_part)

    assert data["ref_id"] == "ref_aaa"
    assert data["valid"] is True
    assert data["total_processed"] == 1
    assert data["failure_rate"] == 0.0

    # Log an invalid execution
    monitor.Log_Execution(request_valid=False, ref_id="ref_bbb")
    captured = capsys.readouterr()

    json_part = captured.out.split("[NIST_RMF_MEASURE]:")[1].strip()
    data = json.loads(json_part)

    assert data["ref_id"] == "ref_bbb"
    assert data["valid"] is False
    assert data["total_processed"] == 2
    assert data["failure_rate"] == 0.5
