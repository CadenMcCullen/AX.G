import hashlib
import time
from typing import NamedTuple, Optional
from privacy_logic.middleware import SettlementRequest

class DuplicateTokenError(Exception):
    """Raised when an attempt is made to settle a token that has already been processed."""
    pass

class LedgerBlock(NamedTuple):
    block_index: int
    prev_hash: str
    s_token: str
    amount_units: int
    timestamp: int
    block_hash: str

class PrivateLedgerEngine:
    """
    Append-only private ledger that settles numerical tokens (S_token)
    without ever storing persistent account credentials or PII.
    """

    def __init__(self):
        self.chain: list[LedgerBlock] = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = LedgerBlock(
            block_index=0,
            prev_hash="0" * 64,
            s_token="0000000000000000",
            amount_units=0,
            timestamp=1700000000,
            block_hash="GENESIS_BLOCK_HASH"
        )
        self.chain.append(genesis)

    def Is_Token_Processed(self, token: str) -> bool:
        """Checks if the given token has already been processed in the chain."""
        # Index 0 is the genesis block, which has the dummy token "0000000000000000"
        return any(block.s_token == token for block in self.chain[1:])

    def Commit_Settlement(self, request: SettlementRequest, timestamp: Optional[int] = None) -> LedgerBlock:
        if self.Is_Token_Processed(request.token):
            raise DuplicateTokenError("SEQUENCE_ALREADY_PROCESSED")

        prev_block = self.chain[-1]
        new_index = prev_block.block_index + 1
        current_time = timestamp if timestamp is not None else int(time.time())

        # Hash construction based purely on numerical token and block index
        payload = f"{new_index}:{prev_block.block_hash}:{request.token}:{request.amount_units}:{current_time}"
        block_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

        new_block = LedgerBlock(
            block_index=new_index,
            prev_hash=prev_block.block_hash,
            s_token=request.token,
            amount_units=request.amount_units,
            timestamp=current_time,
            block_hash=block_hash
        )

        self.chain.append(new_block)
        return new_block
