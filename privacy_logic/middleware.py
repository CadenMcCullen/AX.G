from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "SETTLEMENT_SUCCESSFUL"
    VALIDATION_ERROR = "INVALID_SEQUENCE_FORMAT"
    LEDGER_REJECT = "SEQUENCE_ALREADY_PROCESSED"

class SettlementRequest(BaseModel):
    token: str = Field(..., pattern=r"^\d{16}$", description="16-digit numerical sequence token")
    nonce: str = Field(..., min_length=32, max_length=32)
    amount_units: int = Field(..., gt=0, description="Transaction magnitude in integer units")

    @field_validator('token')
    @classmethod
    def validate_non_pii(cls, v: str) -> str:
        # Guarantee token is not a raw card number (LUHN check fail required for non-PAN token)
        if cls._is_luhn_valid(v):
            raise ValueError("Raw PAN detected. Security invariant violated. Request purged.")
        return v

    @staticmethod
    def _is_luhn_valid(n: str) -> bool:
        try:
            r = [int(ch) for ch in n][::-1]
            return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0
        except ValueError:
            return False

class NeutralSystemResponse(BaseModel):
    status: ResponseStatus
    execution_reference: str
    message: str = Field(
        default="Operation processed under neutral utility specification.",
        description="Non-adversarial, factual register guarantee."
    )

class GuardrailMiddleware:
    """
    Ensures that system failures return objective technical codes rather than
    confrontational, accusatory, or subjective narrative commentary.
    """

    @staticmethod
    def Filter_Output(result_status: ResponseStatus, ref_id: str) -> NeutralSystemResponse:
        return NeutralSystemResponse(
            status=result_status,
            execution_reference=ref_id
        )
