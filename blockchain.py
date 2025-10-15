# blockchain.py
import hashlib
import json
import time
from typing import List, Dict, Optional
import os

class Block:
    def __init__(self, index: int, timestamp: float, data: Dict, previous_hash: str, hash: Optional[str] = None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = hash or self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class SimpleChain:
    def __init__(self, event_id: int):
        if not os.path.exists("ledgers"):
            os.makedirs("ledgers")
        self.chain_file = f"ledgers/blockchain_event_{event_id}.json"
        self.chain: List[Block] = self._load_chain()

    def _load_chain(self) -> List[Block]:
        if not os.path.exists(self.chain_file):
            genesis = Block(0, time.time(), {"genesis": True}, "0")
            self.chain = [genesis]
            self._save_chain()
            return self.chain
        with open(self.chain_file, 'r') as f:
            chain_data = json.load(f)
            return [Block(**block) for block in chain_data]

    def _save_chain(self):
        with open(self.chain_file, 'w') as f:
            json.dump([block.to_dict() for block in self.chain], f, indent=4)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, data: Dict) -> Block:
        index = len(self.chain)
        timestamp = time.time()
        previous_hash = self.last_block.hash
        block = Block(index, timestamp, data, previous_hash)
        self.chain.append(block)
        self._save_chain()
        return block

    def verify_ticket(self, ticket_hash: str) -> Optional[Dict]:
        for b in self.chain:
            if isinstance(b.data, dict) and b.data.get("ticket_hash") == ticket_hash:
                return b.data
        return None

