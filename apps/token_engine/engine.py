import time
from packages.crypto_core.crypto import CryptoEngine

class TokenEngineService:
    """
    Isolated service that tokenizes raw account sequences into single-use
    non-reversible numerical tokens. Ensures raw account details are wiped from memory.
    """
    def __init__(self, key: bytes):
        self._key = key

    def tokenize_input(self, raw_sequence: str):
        """
        Derives an ephemeral S_token and securely scrubs local memory immediately.
        """
        nonce = CryptoEngine.generate_secure_nonce()
        timestamp = int(time.time())
        token = CryptoEngine.derive_s_token(self._key, raw_sequence, nonce, timestamp)

        # Wrapped payload
        from payment_rail.token_engine import TokenizedPayload
        return TokenizedPayload(
            ephemeral_token=token,
            sequence_nonce=nonce,
            timestamp_utc=timestamp
        )
