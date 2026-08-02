import time
import pytest
from payment_rail.token_engine import EphemeralTokenEngine

def test_token_engine_generates_valid_16_digit_token():
    # Master key must be at least 32 bytes (256 bits)
    engine = EphemeralTokenEngine(ledger_secret_key=b"test_secret_key_123_must_be_32_bytes_long!")
    raw_sequence = "4111111111111111"
    timestamp = int(time.time())

    payload = engine.process_and_wipe_sensitive_input(raw_sequence, timestamp)

    assert len(payload.ephemeral_token) == 16
    assert payload.ephemeral_token.isdigit()
    assert len(payload.sequence_nonce) == 32
    assert payload.timestamp_utc == timestamp

def test_token_engine_key_length_validation():
    with pytest.raises(ValueError):
        EphemeralTokenEngine(ledger_secret_key=b"short_key")
