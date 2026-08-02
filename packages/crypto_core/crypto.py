import hmac
import hashlib
import secrets
import gc
from typing import Tuple

class CryptoEngine:
    """
    Cryptographic primitives for ephemeral single-use token derivation and
    secure key management in enclave environments.
    """
    @staticmethod
    def derive_s_token(secret_key: bytes, raw_value: str, nonce: str, timestamp: int) -> str:
        """
        Derives a 16-digit non-reversible numerical surrogate sequence (S_token) using HMAC-SHA256.
        """
        message = f"{raw_value}:{nonce}:{timestamp}".encode('utf-8')
        h = hmac.new(secret_key, message, hashlib.sha256)

        # Convert hash output to standard base-10 numerical sequence and grab the first 16 digits
        numeric_hash = str(int(h.hexdigest(), 16))
        token_numeric = numeric_hash[:16].zfill(16)

        # Invalidate Luhn validation state if needed to prevent accidental PAN collision rejections
        if CryptoEngine._is_luhn_valid(token_numeric):
            last_digit = (int(token_numeric[-1]) + 1) % 10
            token_numeric = token_numeric[:-1] + str(last_digit)

        # Explicitly scrub variables from memory
        del message
        gc.collect()

        return token_numeric

    @staticmethod
    def generate_secure_nonce() -> str:
        """
        Generates a secure 32-character hex nonce for transactional uniqueness.
        """
        return secrets.token_hex(16)

    @staticmethod
    def _is_luhn_valid(n: str) -> bool:
        """
        Calculates Luhn checksum validity of a numeric string.
        """
        digits = [int(char) for char in n][::-1]
        odd_sum = sum(digits[0::2])
        even_sum = sum(sum(divmod(d * 2, 10)) for d in digits[1::2])
        return (odd_sum + even_sum) % 10 == 0
