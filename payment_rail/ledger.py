import hashlib
import time
from typing import NamedTuple
from .guardrail import SettlementRequest

class LedgerBlock(NamedTuple):
    block_index: int
    prev_hash: str
    s_token: str
    amount_units: int
    timestamp: int
    block_hash: str

class PrivateLedgerEngine:
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

    def Commit_Settlement(self, request: SettlementRequest) -> LedgerBlock:
        prev_block = self.chain[-1]
        new_index = prev_block.block_index + 1
        current_time = int(time.time())

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
