import time
from packages.ledger_types.types import ImmutableBlock

class LedgerNodeService:
    """
    Settlement engine executing transactional commits onto the private permissioned blockchain ledger.
    """
    def __init__(self):
        self.chain: list[ImmutableBlock] = []
        self._initialize_genesis_block()

    def _initialize_genesis_block(self):
        """
        Creates the static immutable starting point of the settlement ledger.
        """
        genesis = ImmutableBlock(
            index=0,
            prev_hash="0" * 64,
            s_token="0000000000000000",
            amount=0,
            timestamp_utc=1700000000,
            block_hash="GENESIS_HASH_STABLE"
        )
        self.chain.append(genesis)

    def commit_block(self, s_token: str, amount: int) -> ImmutableBlock:
        """
        Appends a new verified transaction block to the immutable chain.
        """
        prev_block = self.chain[-1]
        new_index = prev_block.index + 1
        timestamp = int(time.time())

        block_hash = ImmutableBlock.calculate_hash(
            new_index,
            prev_block.block_hash,
            s_token,
            amount,
            timestamp
        )

        new_block = ImmutableBlock(
            index=new_index,
            prev_hash=prev_block.block_hash,
            s_token=s_token,
            amount=amount,
            timestamp_utc=timestamp,
            block_hash=block_hash
        )
        self.chain.append(new_block)
        return new_block
