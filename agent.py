#!/opt/homebrew/bin/python3.10
import uuid
import json
import ollama
import subprocess

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from transaction import Transaction

"""
Agent Class
"""
class Agent:
    def __init__(self, is_malicious=False):
        self.id = str(uuid.uuid4())
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.stake = 0
        self.role = None  # 'worker' (answer proposer) or 'miner' (answer evaluator)
        self.is_malicious = is_malicious

    def sign_data(self, data):
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return signature

    def verify_signature(self, public_key, signature, data):
        try:
            public_key.verify(
                signature,
                data.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def generate_proposal(self, task):
        if self.is_malicious:
            answer = "<Insert here Malicious Prompt>"
        else:
            answer = self.generate_statement(task)
        
        if answer == "":
            return None
        else:
            signature = self.sign_data(answer)
            return Transaction(self.id, answer, signature)

    def generate_statement(self, prompt, model_name='llama2'):
        print(f"[*] Agent {self.id} - {self.role} : {prompt}")
        try:
            # Construct the command to run Ollama
            response = ollama.chat(
                model="llama3.1:latest",  
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            content = response.get('message', {}).get('content', "")
            print("[*] LLM Response:", content)
            return content.strip()
        except Exception as e:
            print(f"Error generating text with Ollama: {e}")
            return ""

    def evaluate_proposals(self, transactions, agent_dict, evaluation_prompt):
        evaluations = {}
        for tx in transactions:
            proposer = agent_dict[tx.proposer_id]
            if not self.verify_signature(proposer.public_key, tx.signature, tx.answer):
                continue
            score = self.multi_metric_evaluation(evaluation_prompt.format(answer=tx.answer))
            evaluations[tx.proposer_id] = score
        return evaluations

    def multi_metric_evaluation(self, prompt):
        score_text = self.generate_proposal(prompt)
        try:
            score = float(score_text.strip().split()[0])
            if score < 0 or score > 10:
                score = 0.0
        except Exception:
            score = 0.0
        return score

    def select_preferred_evaluation(self, miner_evaluations):
        # For simplicity, select the evaluation with the highest average score
        avg_scores = {}
        for miner_id, evaluations in miner_evaluations.items():
            avg_score = sum(evaluations.values()) / len(evaluations) if evaluations else 0
            avg_scores[miner_id] = avg_score
        preferred_miner_id = max(avg_scores, key=avg_scores.get)
        return preferred_miner_id