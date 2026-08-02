import pytest
from apps.gateway_api.gateway import GatewayApiService
from packages.zkp_identity.zkp import ZKPIdentityVerifier
from packages.guardrail_middleware.guardrails import GuardrailResponseStatus

def test_gateway_api_service_end_to_end():
    # 32 bytes key for encryption
    ledger_key = b"my_prod_secret_ledger_key_value_32_bytes!"

    # Simple registry of blocked identity hashes
    blocked = {"sanctioned_entity_hash_1234567890"}
    zkp_verifier = ZKPIdentityVerifier(blocked_hashes=blocked)

    gateway = GatewayApiService(ledger_key=ledger_key)

    # Ingress transaction with a non-PAN sequence (valid)
    resp = gateway.process_transaction(raw_account_sequence="987654321012345", amount_units=1000)
    assert resp.status == GuardrailResponseStatus.SUCCESS
    assert resp.reference.startswith("REF-") or len(resp.reference) == 64

    # Sanctions check using ZKP verifier
    # Proves a non-sanctioned user passes
    assert zkp_verifier.prove_non_sanctioned("user_id_999", "secret_salt_abc") is True
    # Proves a sanctioned user hash is detected
    # user_id_banned + salt_123 produces sanctioned_entity_hash_1234567890
    import hashlib
    # Let's mock a sanctioned hash by matching the verifier logic
    digest_input = "banned_entity:proof_salt".encode('utf-8')
    banned_hash = hashlib.sha256(digest_input).hexdigest()

    zkp_verifier_with_real_hash = ZKPIdentityVerifier(blocked_hashes={banned_hash})
    assert zkp_verifier_with_real_hash.prove_non_sanctioned("banned_entity", "proof_salt") is False
