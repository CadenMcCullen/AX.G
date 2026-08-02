import pytest
import time
from pydantic import ValidationError

from privacy_logic.token_engine import EphemeralTokenEngine, TokenizedPayload
from privacy_logic.middleware import (
    SettlementRequest,
    ResponseStatus,
    NeutralSystemResponse,
    GuardrailMiddleware
)
from privacy_logic.ledger import PrivateLedgerEngine, DuplicateTokenError, LedgerBlock
from privacy_logic.governance import NISTGovernanceMonitor, PipelineHaltedError

# ----------------------------------------------------------------------
# 1. EphemeralTokenEngine Tests
# ----------------------------------------------------------------------

def test_token_engine_generation():
    key = b"super_secret_ledger_key_12345"
    engine = EphemeralTokenEngine(key)
    raw_account = "1234-5678-9012-3456"
    timestamp = int(time.time())

    payload = engine.Process_And_Wipe_Sensitive_Input(raw_account, timestamp)

    assert isinstance(payload, TokenizedPayload)
    assert len(payload.ephemeral_token) == 16
    assert payload.ephemeral_token.isdigit()
    assert len(payload.sequence_nonce) == 32  # 16 bytes secrets.token_hex is 32 chars
    assert payload.timestamp_utc == timestamp

    # Verify token is NOT Luhn-valid (Crucial invariant for non-PAN tokens)
    assert not EphemeralTokenEngine._is_luhn_valid(payload.ephemeral_token)


# ----------------------------------------------------------------------
# 2. GuardrailMiddleware Tests
# ----------------------------------------------------------------------

def test_settlement_request_validation():
    # Luhn-invalid 16 digit sequence
    # Let's use a sequence that is not Luhn-valid, like "49927398717" padded to 16 digits
    # "1111111111111111" has sum of digits: reverse: 1, 1, ...
    # Let's find one:
    # Let's test "1234567890123456"
    # Luhn sum:
    # 6, (5*2=10->1), 4, (3*2=6), 2, (1*2=2), 0, (9*2=18->9), 8, (7*2=14->5), 6, (5*2=10->1), 4, (3*2=6), 2, (1*2=2)
    # Sum = 6 + 1 + 4 + 6 + 2 + 2 + 0 + 9 + 8 + 5 + 6 + 1 + 4 + 6 + 2 + 2 = 64. 64 % 10 = 4 != 0 (Luhn invalid)
    token = "1234567890123456"
    assert not SettlementRequest._is_luhn_valid(token)

    nonce = "a" * 32
    amount = 5000

    req = SettlementRequest(token=token, nonce=nonce, amount_units=amount)
    assert req.token == token
    assert req.nonce == nonce
    assert req.amount_units == amount

def test_settlement_request_invalid_format():
    # Token is not 16 digits
    with pytest.raises(ValidationError):
        SettlementRequest(token="12345", nonce="a"*32, amount_units=100)

    # Nonce is too short
    with pytest.raises(ValidationError):
        SettlementRequest(token="1234567890123456", nonce="abc", amount_units=100)

    # Amount is zero/negative
    with pytest.raises(ValidationError):
        SettlementRequest(token="1234567890123456", nonce="a"*32, amount_units=0)

def test_settlement_request_rejects_luhn_valid_pan():
    # Let's construct a Luhn-valid 16-digit sequence: "49927398716" is valid.
    # Let's find a standard 16 digit valid Luhn string, e.g., "49927398716" padded
    # "0000000000000000" is Luhn-valid.
    # Let's check: "1234567890123452"
    # Reverse digits and double every second:
    # 2, (5*2=10->1), 4, (3*2=6), 2, (1*2=2), 0, (9*2=18->9), 8, (7*2=14->5), 6, (5*2=10->1), 4, (3*2=6), 2, (1*2=2)
    # Sum: 2+1+4+6+2+2+0+9+8+5+6+1+4+6+2+2 = 60. 60 % 10 == 0. Valid!
    luhn_valid_token = "1234567890123452"
    assert SettlementRequest._is_luhn_valid(luhn_valid_token)

    with pytest.raises(ValidationError) as excinfo:
        SettlementRequest(token=luhn_valid_token, nonce="a"*32, amount_units=100)

    assert "Raw PAN detected. Security invariant violated." in str(excinfo.value)

def test_guardrail_middleware_neutrality():
    for status in [ResponseStatus.SUCCESS, ResponseStatus.VALIDATION_ERROR, ResponseStatus.LEDGER_REJECT]:
        ref = "REF-999"
        resp = GuardrailMiddleware.Filter_Output(status, ref)
        assert isinstance(resp, NeutralSystemResponse)
        assert resp.status == status
        assert resp.execution_reference == ref
        # Verify the wording is completely neutral and non-adversarial
        assert resp.message == "Operation processed under neutral utility specification."


# ----------------------------------------------------------------------
# 3. PrivateLedgerEngine Tests
# ----------------------------------------------------------------------

def test_private_ledger_genesis():
    ledger = PrivateLedgerEngine()
    assert len(ledger.chain) == 1
    genesis = ledger.chain[0]
    assert genesis.block_index == 0
    assert genesis.prev_hash == "0" * 64
    assert genesis.s_token == "0000000000000000"
    assert genesis.amount_units == 0
    assert genesis.block_hash == "GENESIS_BLOCK_HASH"

def test_private_ledger_settlement():
    ledger = PrivateLedgerEngine()
    token = "1234567890123456" # Luhn-invalid
    req = SettlementRequest(token=token, nonce="a"*32, amount_units=150)

    block = ledger.Commit_Settlement(req, timestamp=1800000000)
    assert len(ledger.chain) == 2
    assert block.block_index == 1
    assert block.prev_hash == "GENESIS_BLOCK_HASH"
    assert block.s_token == token
    assert block.amount_units == 150
    assert block.timestamp == 1800000000
    assert len(block.block_hash) == 64  # SHA256 hex string is 64 chars

def test_private_ledger_duplicate_rejection():
    ledger = PrivateLedgerEngine()
    token = "1234567890123456"
    req = SettlementRequest(token=token, nonce="a"*32, amount_units=150)

    # First settlement succeeds
    ledger.Commit_Settlement(req)

    # Second settlement fails due to duplicate token
    with pytest.raises(DuplicateTokenError):
        ledger.Commit_Settlement(req)


# ----------------------------------------------------------------------
# 4. NISTGovernanceMonitor Tests
# ----------------------------------------------------------------------

def test_entropy_calculation():
    # Extremely low entropy
    low_entropy = "1111111111111111"
    entropy_low = NISTGovernanceMonitor.Calculate_Entropy(low_entropy)
    assert entropy_low == 0.0

    # Higher entropy
    high_entropy = "1234567890123456"
    entropy_high = NISTGovernanceMonitor.Calculate_Entropy(high_entropy)
    assert entropy_high > 1.5

def test_governance_monitoring_and_circuit_breaker():
    monitor = NISTGovernanceMonitor(failure_rate_threshold=0.5, min_executions_for_threshold=4)

    # 1. Success execution
    monitor.Log_Execution(request_valid=True, ref_id="REF-1", token_entropy=3.12, latency_ms=12.5)
    assert monitor.processed_count == 1
    assert monitor.validation_failures == 0
    assert not monitor.is_halted

    # 2. Failure execution
    monitor.Log_Execution(request_valid=False, ref_id="REF-2", token_entropy=0.0, latency_ms=2.1)
    assert monitor.processed_count == 2
    assert monitor.validation_failures == 1
    assert not monitor.is_halted # Failure rate is 0.5, but total processed is 2 (below min_executions_for_threshold=4)

    # 3. Success execution
    monitor.Log_Execution(request_valid=True, ref_id="REF-3", token_entropy=3.0, latency_ms=10.0)
    assert monitor.processed_count == 3
    assert monitor.validation_failures == 1
    assert not monitor.is_halted

    # 4. Failure execution (4th processing, failure rate = 2/4 = 0.5, triggers circuit breaker!)
    monitor.Log_Execution(request_valid=False, ref_id="REF-4", token_entropy=0.0, latency_ms=1.5)
    assert monitor.processed_count == 4
    assert monitor.validation_failures == 2
    assert monitor.is_halted

    # Further logging should be rejected due to pipeline halt
    with pytest.raises(PipelineHaltedError):
        monitor.Log_Execution(request_valid=True, ref_id="REF-5")


# ----------------------------------------------------------------------
# 5. Integrated Pipeline Flow Tests
# ----------------------------------------------------------------------

def test_integrated_payment_pipeline_success():
    # Setup
    key = b"ledger_signing_secret_99999"
    token_engine = EphemeralTokenEngine(key)
    ledger = PrivateLedgerEngine()
    governance = NISTGovernanceMonitor()

    raw_account = "9876-5432-1098-7654"
    amount = 250
    timestamp = int(time.time())

    # --- STEP 1: Ingress & Ephemeral Tokenization ---
    payload = token_engine.Process_And_Wipe_Sensitive_Input(raw_account, timestamp)

    # Verify no credentials leaked into the payload
    assert raw_account not in payload.ephemeral_token
    assert raw_account not in payload.sequence_nonce

    # --- STEP 2: Middleware & Schema Guardrails ---
    # Construct SettlementRequest
    try:
        req = SettlementRequest(
            token=payload.ephemeral_token,
            nonce=payload.sequence_nonce,
            amount_units=amount
        )
        request_valid = True
    except ValidationError:
        request_valid = False

    assert request_valid

    # --- STEP 3: Private Ledger Settlement ---
    ref_id = f"TX-{payload.sequence_nonce[:8]}"
    start_time = time.perf_counter_ns()

    block = ledger.Commit_Settlement(req)

    end_time = time.perf_counter_ns()
    latency_ms = (end_time - start_time) / 1_000_000

    assert block.s_token == payload.ephemeral_token
    assert block.amount_units == amount

    # --- STEP 4: NIST AI RMF Logging ---
    entropy = NISTGovernanceMonitor.Calculate_Entropy(payload.ephemeral_token)
    governance.Log_Execution(
        request_valid=request_valid,
        ref_id=ref_id,
        token_entropy=entropy,
        latency_ms=latency_ms
    )

    assert governance.processed_count == 1
    assert governance.validation_failures == 0

    # Filter output to return neutral response to user
    response = GuardrailMiddleware.Filter_Output(ResponseStatus.SUCCESS, ref_id)
    assert response.status == ResponseStatus.SUCCESS
    assert response.execution_reference == ref_id
    assert "neutral utility specification" in response.message


def test_integrated_payment_pipeline_duplicate_rejection_flow():
    # Setup
    key = b"ledger_signing_secret_99999"
    token_engine = EphemeralTokenEngine(key)
    ledger = PrivateLedgerEngine()
    governance = NISTGovernanceMonitor()

    raw_account = "9876-5432-1098-7654"
    amount = 250
    timestamp = int(time.time())

    # First processing
    payload = token_engine.Process_And_Wipe_Sensitive_Input(raw_account, timestamp)
    req1 = SettlementRequest(
        token=payload.ephemeral_token,
        nonce=payload.sequence_nonce,
        amount_units=amount
    )

    # Settle first
    ref_id_1 = f"TX-{payload.sequence_nonce[:8]}"
    ledger.Commit_Settlement(req1)
    governance.Log_Execution(request_valid=True, ref_id=ref_id_1)

    # Try settling second time with the exact same request
    try:
        ledger.Commit_Settlement(req1)
        settlement_failed = False
    except DuplicateTokenError:
        settlement_failed = True

    assert settlement_failed

    # Return neutral rejection response
    response = GuardrailMiddleware.Filter_Output(ResponseStatus.LEDGER_REJECT, ref_id_1)
    assert response.status == ResponseStatus.LEDGER_REJECT
    assert "neutral utility specification" in response.message
