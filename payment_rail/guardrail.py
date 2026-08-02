from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional

class ResponseStatus(str, Enum):
    SETTLEMENT_SUCCESSFUL = "SETTLEMENT_SUCCESSFUL"
    INVALID_SEQUENCE_FORMAT = "INVALID_SEQUENCE_FORMAT"
    RAW_CREDENTIAL_REJECTED = "RAW_CREDENTIAL_REJECTED"
    SEQUENCE_ALREADY_PROCESSED = "SEQUENCE_ALREADY_PROCESSED"
    SYSTEM_PROCESSING_ERROR = "SYSTEM_PROCESSING_ERROR"

class SettlementRequest(BaseModel):
    token: str = Field(..., pattern=r"^\d{16}$", description="16-digit numerical sequence placeholder")
    nonce: str = Field(..., min_length=32, max_length=32, description="32-char hex nonce")
    amount_units: int = Field(..., gt=0, description="Transaction magnitude in integer units (e.g., cents)")

    @field_validator('token')
    def validate_non_luhn(cls, v: str) -> str:
        """
        SECURITY INVARIANT: Raw card credentials (PANs) passing Luhn algorithm checks
        must NEVER enter the settlement layer. Tokens must be non-PAN placeholders.
        """
        if cls._is_luhn_valid(v):
            raise ValueError("Raw PAN detected. Security invariant violated. Execution halted.")
        return v

    @staticmethod
    def _is_luhn_valid(n: str) -> bool:
        r = [int(ch) for ch in n][::-1]
        return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0

class NeutralSystemResponse(BaseModel):
    status: ResponseStatus
    execution_reference: str
    block_hash: Optional[str] = None
    message: str = Field(
        default="Operation processed under neutral utility specification.",
        description="Non-adversarial, objective operational output."
    )
