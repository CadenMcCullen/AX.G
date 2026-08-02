import time
from payment_rail.token_engine import EphemeralTokenEngine


def test_token_engine_generates_valid_16_digit_token():
    engine = EphemeralTokenEngine(ledger_secret_key=b"test_secret_key_123")
    raw_sequence = "4111111111111111"
    timestamp = int(time.time())

    payload = engine.Process_And_Wipe_Sensitive_Input(raw_sequence, timestamp)

    assert len(payload.ephemeral_token) == 16
    assert payload.ephemeral_token.isdigit()
    assert len(payload.sequence_nonce) == 32
    assert payload.timestamp_utc == timestamp
