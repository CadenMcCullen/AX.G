import pytest
from payment_rail.ledger import PrivateLedgerEngine, LedgerBlock
from payment_rail.guardrail import SettlementRequest

def test_ledger_initialization_with_genesis():
    ledger = PrivateLedgerEngine()
    assert len(ledger.chain) == 1
    genesis = ledger.chain[0]
    assert genesis.block_index == 0
    assert genesis.prev_hash == "0" * 64
    assert genesis.s_token == "0000000000000000"
    assert genesis.amount_units == 0
    assert genesis.block_hash.startswith("GENESIS_BLOCK_HASH_")

def test_ledger_commit_settlement_and_deduplication():
    ledger = PrivateLedgerEngine()
    request = SettlementRequest(
        token="4111111111111112",
        nonce="b" * 32,
        amount_units=500
    )

    new_block = ledger.commit_settlement(request)

    assert len(ledger.chain) == 2
    assert new_block.block_index == 1
    assert new_block.prev_hash.startswith("GENESIS_BLOCK_HASH_")
    assert new_block.s_token == "4111111111111112"
    assert new_block.amount_units == 500
    assert new_block.block_hash is not None
    assert ledger.chain[-1] == new_block

    # Test replay attack prevention: attempting to commit the same token sequence again must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        ledger.commit_settlement(request)
    assert "already been executed" in str(exc_info.value)
