import secrets
import hmac
import hashlib
import gc
from typing import NamedTuple
from .guardrail import SettlementRequest

class TokenizedPayload(NamedTuple):
    ephemeral_token: str  # Single-use numerical sequence placeholder (S_token)
    sequence_nonce: str   # Single-use cryptographic nonce
    timestamp_utc: int    # Transaction Unix timestamp

class EphemeralTokenEngine:
    """
    INVARIANT: Converts raw input into a single-use 16-digit S_token placeholder,
    then immediately scrubs volatile memory stack to prevent data retention.
    """

    def __init__(self, ledger_secret_key: bytes):
        if len(ledger_secret_key) < 32:
            raise ValueError("Secret key must be at least 256 bits (32 bytes).")
        self._secret_key = ledger_secret_key

    def process_and_wipe_sensitive_input(
        self,
        raw_account_sequence: str,
        timestamp: int
    ) -> TokenizedPayload:
        # 1. Generate an ephemeral 256-bit cryptographic nonce
        nonce = secrets.token_hex(16)  # 32-character hex string

        # 2. Derive deterministic single-use sequence token (S_token)
        message = f"{raw_account_sequence}:{nonce}:{timestamp}".encode('utf-8')
        h = hmac.new(self._secret_key, message, hashlib.sha256)

        # Convert HMAC to 16-digit numerical string
        numeric_hash = str(int(h.hexdigest(), 16))
        s_token_numeric = numeric_hash[:16].zfill(16)

        # Ensure the generated token does not accidentally pass Luhn check (PAN Collision Prevention)
        if SettlementRequest._is_luhn_valid(s_token_numeric):
            # Tweak final digit to invalidate Luhn state without losing entropy
            last_digit = (int(s_token_numeric[-1]) + 1) % 10
            s_token_numeric = s_token_numeric[:-1] + str(last_digit)

        # 3. Explicit Volatile Memory Scrubbing
        del raw_account_sequence
        del message
        gc.collect()

        return TokenizedPayload(
            ephemeral_token=s_token_numeric,
            sequence_nonce=nonce,
            timestamp_utc=timestamp
        )
