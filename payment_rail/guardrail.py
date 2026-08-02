from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "SETTLEMENT_SUCCESSFUL"
    VALIDATION_ERROR = "INVALID_SEQUENCE_FORMAT"
    LEDGER_REJECT = "SEQUENCE_ALREADY_PROCESSED"

class SettlementRequest(BaseModel):
    token: str = Field(..., pattern=r"^\d{16}$", description="16-digit numerical sequence")
    nonce: str = Field(..., min_length=32, max_length=32)
    amount_units: int = Field(..., gt=0)

    @field_validator('token')
    def validate_non_pii(cls, v: str) -> str:
        if cls._is_luhn_valid(v):
            raise ValueError("Raw PAN detected. Security invariant violated. Request purged.")
        return v

    @staticmethod
    def _is_luhn_valid(n: str) -> bool:
        r = [int(ch) for ch in n][::-1]
        return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0

class NeutralSystemResponse(BaseModel):
    status: ResponseStatus
    execution_reference: str
    message: str = "Operation processed under neutral utility specification."
