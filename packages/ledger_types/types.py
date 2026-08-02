import hashlib
import time
from typing import NamedTuple

class ImmutableBlock(NamedTuple):
    index: int
    prev_hash: str
    s_token: str
    amount: int
    timestamp_utc: int
    block_hash: str

    @staticmethod
    def calculate_hash(index: int, prev_hash: str, s_token: str, amount: int, timestamp: int) -> str:
        """
        Calculates SHA-256 block digest ensuring cryptographical immutability of the chain.
        """
        payload = f"{index}:{prev_hash}:{s_token}:{amount}:{timestamp}".encode('utf-8')
        return hashlib.sha256(payload).hexdigest()
