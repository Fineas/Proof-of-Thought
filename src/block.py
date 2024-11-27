import time
import hashlib

"""
Block Class
"""
class Block:
    def __init__(self, previous_hash, transactions, miner_id, signature, round_number):
        self.previous_hash = previous_hash
        self.transactions = transactions 
        self.miner_id = miner_id
        self.signature = signature  
        self.timestamp = time.time()
        self.round_number = round_number

    def compute_hash(self):
        block_string = f"{self.previous_hash}{[tx.answer for tx in self.transactions]}{self.miner_id}{self.timestamp}{self.round_number}"
        return hashlib.sha256(block_string.encode()).hexdigest()