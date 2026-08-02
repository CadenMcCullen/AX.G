import pytest
from pydantic import ValidationError
from payment_rail.guardrail import SettlementRequest, ResponseStatus, NeutralSystemResponse

def test_settlement_request_validation_success():
    # 16-digit non-Luhn-valid sequence is accepted (surrogate token)
    request = SettlementRequest(
        token="4111111111111112",
        nonce="a" * 32,
        amount_units=100
    )
    assert request.token == "4111111111111112"
    assert request.nonce == "a" * 32
    assert request.amount_units == 100

def test_settlement_request_validation_fails_on_luhn_valid_pan():
    # 16-digit Luhn-valid sequence is rejected as a PAN
    with pytest.raises(ValidationError) as exc_info:
        SettlementRequest(
            token="4111111111111111",
            nonce="a" * 32,
            amount_units=100
        )
    assert "Raw PAN detected" in str(exc_info.value)

def test_settlement_request_validation_fails_on_invalid_token_pattern():
    # Non-digit or wrong length should be rejected
    with pytest.raises(ValidationError):
        SettlementRequest(token="1234", nonce="a" * 32, amount_units=100)

    with pytest.raises(ValidationError):
        SettlementRequest(token="a" * 16, nonce="a" * 32, amount_units=100)

def test_neutral_system_response():
    resp = NeutralSystemResponse(
        status=ResponseStatus.SUCCESS,
        execution_reference="ref_123"
    )
    assert resp.status == ResponseStatus.SUCCESS
    assert resp.execution_reference == "ref_123"
    assert "neutral utility specification" in resp.message
