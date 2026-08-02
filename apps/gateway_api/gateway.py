from packages.crypto_core.crypto import CryptoEngine
from packages.guardrail_middleware.guardrails import GuardrailRequestValidator, GuardrailResponseStatus, NonAdversarialResponse
from apps.token_engine.engine import TokenEngineService
from apps.ledger_node.node import LedgerNodeService
from apps.monitor_service.monitor import MonitorService

class GatewayApiService:
    """
    Public entrypoint for payment processing. Coordinates request validation,
    tokenization, private ledger settlement, and NIST telemetry logging.
    """
    def __init__(self, ledger_key: bytes, sanctions_registry=None):
        self.token_service = TokenEngineService(ledger_key)
        self.ledger_service = LedgerNodeService()
        self.monitor_service = MonitorService()
        self.sanctions_registry = sanctions_registry or set()

    def process_transaction(self, raw_account_sequence: str, amount_units: int) -> NonAdversarialResponse:
        """
        Processes a secure end-to-end payment transaction by decoupling raw accounts
        from execution using ephemeral single-use tokens.
        """
        # Step 1: Tokenize the raw sequence on the edge
        payload = self.token_service.tokenize_input(raw_account_sequence)

        # Step 2: Validate the payload against Guardrail Middleware (reject Luhn-valid PANs)
        try:
            validator = GuardrailRequestValidator(
                token=payload.ephemeral_token,
                nonce=payload.sequence_nonce,
                amount_units=amount_units
            )
        except Exception as e:
            # Telemetry tracking for security violations
            self.monitor_service.record_transaction(is_valid=False, reference_id="FAILED_VALIDATION")
            return NonAdversarialResponse(
                status=GuardrailResponseStatus.REJECTED,
                reference="REJECTED",
                message=f"Request blocked by guardrails: {str(e)}"
            )

        # Step 3: Commit the validated transaction to the Private Immutable Ledger
        block = self.ledger_service.commit_block(validator.token, validator.amount_units)

        # Step 4: Track success telemetry
        self.monitor_service.record_transaction(is_valid=True, reference_id=block.block_hash)

        return NonAdversarialResponse(
            status=GuardrailResponseStatus.SUCCESS,
            reference=block.block_hash,
            message="Transaction successfully tokenized and settled on the private ledger."
        )
