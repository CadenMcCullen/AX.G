from pydantic import BaseModel, Field, field_validator
from enum import Enum

class GuardrailResponseStatus(str, Enum):
    SUCCESS = "SETTLEMENT_SUCCESSFUL"
    VALIDATION_ERROR = "INVALID_SEQUENCE_FORMAT"
    REJECTED = "SECURITY_INVARIANT_VIOLATED"

class GuardrailRequestValidator(BaseModel):
    token: str = Field(..., pattern=r"^\d{16}$", description="16-digit single-use surrogate sequence")
    nonce: str = Field(..., min_length=32, max_length=32, description="32-char security hex nonce")
    amount_units: int = Field(..., gt=0, description="Amount in integer micro-units")

    @field_validator('token')
    def enforce_zero_pan_storage(cls, v: str) -> str:
        """
        Enforce absolute security boundary: if the token matches a valid Luhn sequence
        (typical of a raw credit card PAN), block it immediately to prevent PII ingress.
        """
        if cls.is_luhn_valid(v):
            raise ValueError("Raw PAN detected. Safety invariant violated. Payload rejected.")
        return v

    @staticmethod
    def is_luhn_valid(n: str) -> bool:
        """
        Calculates Luhn checksum validity of a numeric string.
        """
        digits = [int(char) for char in n][::-1]
        odd_sum = sum(digits[0::2])
        even_sum = sum(sum(divmod(d * 2, 10)) for d in digits[1::2])
        return (odd_sum + even_sum) % 10 == 0

class NonAdversarialResponse(BaseModel):
    status: GuardrailResponseStatus
    reference: str
    message: str = "System utility operation processed successfully under non-adversarial guidelines."
