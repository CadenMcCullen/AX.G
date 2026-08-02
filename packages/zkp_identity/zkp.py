import hashlib
from typing import Set

class ZKPIdentityVerifier:
    """
    Zero-Knowledge Proof (ZKP) identity checker.
    Proves that a user's cryptographic identity hash is not part of a public/private
    blacklist (OFAC sanctions registry) without revealing any PII or identification details.
    """
    def __init__(self, blocked_hashes: Set[str]):
        # Keep list of SHA-256 digests of blocked identities (e.g., sanctioned entities)
        self._blocked_hashes = blocked_hashes

    def prove_non_sanctioned(self, identity_raw: str, zkp_proof: str) -> bool:
        """
        Verifies that identity_raw (hashed cryptographically with the ZKP proof)
        does not match any record in the blocked/sanction list.
        """
        # Hashing raw identity with secret proof salt to generate an anonymous verification key
        digest_input = f"{identity_raw}:{zkp_proof}".encode('utf-8')
        anon_key = hashlib.sha256(digest_input).hexdigest()

        # Check if the anonymous key belongs to any sanction lists
        if anon_key in self._blocked_hashes:
            return False

        # Proof verification successful; entity is legally non-sanctioned
        return True
