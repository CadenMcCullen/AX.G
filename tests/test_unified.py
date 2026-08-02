import pytest
import secrets
from pydantic import ValidationError
from payment_rail_core import CompletePaymentRailSystem, ResponseStatus, SettlementRequest

def test_unified_system_flow():
    system_master_key = secrets.token_bytes(32)
    payment_rail = CompletePaymentRailSystem(master_key=system_master_key)

    # Test Case 1: Valid sequence
    tx1_response = payment_rail.process_transaction(raw_input_sequence="987654321012345", amount_units=4999)
    assert tx1_response.status == ResponseStatus.SETTLEMENT_SUCCESSFUL
    assert tx1_response.execution_reference.startswith("REF-")
    assert tx1_response.block_hash is not None

    # Test Case 2: Ingress PAN through the whole pipeline gets securely tokenized & successfully settled
    tx2_response = payment_rail.process_transaction(raw_input_sequence="4532015112830366", amount_units=1500)
    assert tx2_response.status == ResponseStatus.SETTLEMENT_SUCCESSFUL
    assert tx2_response.block_hash is not None

    # Test Case 3: Submitting raw Luhn-valid PAN directly to settlement schema is blocked as expected
    with pytest.raises(ValidationError):
        SettlementRequest(
            token="4532015112830366",
            nonce="c" * 32,
            amount_units=1500
        )
