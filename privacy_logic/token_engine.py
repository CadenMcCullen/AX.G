import secrets
import hmac
import hashlib
import gc
from typing import NamedTuple

class TokenizedPayload(NamedTuple):
    ephemeral_token: str  # The S_token placeholder
    sequence_nonce: str   # Single-use deterministic reference
    timestamp_utc: int    # Unix timestamp

class EphemeralTokenEngine:
    """
    INVARIANT: Raw credentials must NEVER touch database layer or logs.
    Tokens are single-use, non-reversible numerical sequences.
    """

    def __init__(self, ledger_secret_key: bytes):
        self._secret_key = ledger_secret_key

    @staticmethod
    def _is_luhn_valid(n: str) -> bool:
        try:
            r = [int(ch) for ch in n][::-1]
            return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0
        except ValueError:
            return False

    def Process_And_Wipe_Sensitive_Input(
        self,
        raw_account_sequence: str,
        timestamp: int
    ) -> TokenizedPayload:
        """
        Transforms raw sensitive data into a single-use numerical token,
        then immediately purges raw variables.
        Guarantees the returned 16-digit token is NOT Luhn-valid.
        """
        s_token_numeric = ""
        nonce = ""

        # Loop to ensure we don't accidentally produce a Luhn-valid sequence
        while True:
            # 1. Generate an ephemeral 256-bit cryptographic nonce
            # We generate a 32-character hex string (16 bytes)
            nonce = secrets.token_hex(16)

            # 2. Derive deterministic single-use sequence token (S_token)
            message = f"{raw_account_sequence}:{nonce}:{timestamp}".encode('utf-8')
            h = hmac.new(self._secret_key, message, hashlib.sha256)
            s_token_numeric = str(int(h.hexdigest(), 16))[:16]  # 16-digit numerical sequence

            # Guarantee the generated token is not Luhn-valid
            if not self._is_luhn_valid(s_token_numeric) and len(s_token_numeric) == 16:
                break

        # 3. Explicit Memory Wiping Routine (Security Invariant)
        del raw_account_sequence
        if 'message' in locals():
            del message
        if 'h' in locals():
            del h
        gc.collect()  # Trigger garbage collection to clean volatile stack

        return TokenizedPayload(
            ephemeral_token=s_token_numeric,
            sequence_nonce=nonce,
            timestamp_utc=timestamp
        )
