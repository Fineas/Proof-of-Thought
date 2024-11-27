#!/opt/homebrew/bin/python3.10

# Copyright (c) 2024 Fineas Silaghi <https://github.com/Fineas>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# author: FeDEX

import json
import random
import argparse
from tabulate import tabulate

from enum import Enum
from agent import Agent
from block import Block
from utils import load_eval_prompt

"""
Constants
"""
DEBUG = True
EVAL_PROMPT = load_eval_prompt("eval_prompt.txt")

"""
Globals
"""
blockchain = None

"""
Enums
"""
class Role(Enum):
    WORKER = 'worker' # answer proposer
    MINER = 'miner'   # answer evaluator

"""
Methods
"""
def assign_roles(agents, num_miners):
    # Assign roles based on stake
    agents_sorted = sorted(agents, key=lambda x: x.stake, reverse=True)
    miners = agents_sorted[:num_miners]
    workers = agents_sorted[num_miners:]

    for agent in miners:
        agent.role = Role.MINER
    for agent in workers:
        agent.role = Role.WORKER

    return miners, workers

def assign_roles(agents, num_miners):
    # Randomly select 'num_miners' agents to be miners
    miners = random.sample(agents, num_miners)
    workers = [agent for agent in agents if agent not in miners]
    
    for agent in miners:
        agent.role = Role.MINER
    for agent in workers:
        agent.role = Role.WORKER

    return miners, workers

def debate_and_vote(miners, miner_evaluations):
    votes = {}
    for miner in miners:
        preferred_miner_id = miner.select_preferred_evaluation(miner_evaluations)
        votes[preferred_miner_id] = votes.get(preferred_miner_id, 0) + 1

    # Check if any miner has majority votes
    for miner_id, vote_count in votes.items():
        if vote_count > len(miners) / 2:
            return True, miner_id  # Consensus reached
    return False, None  # No consensus

def consensus(miners, transactions, agent_dict, max_rounds=2):
    round_number = 1
    while round_number < max_rounds:
        # Each miner evaluates proposals
        miner_evaluations = {}
        for miner in miners:
            evals = miner.evaluate_proposals(transactions, agent_dict, EVAL_PROMPT)
            miner_evaluations[miner.id] = evals

        # Debate and voting
        consensus_reached, winning_miner_id = debate_and_vote(miners, miner_evaluations)
        if consensus_reached:
            # Winning miner creates the block
            winning_miner = next((m for m in miners if m.id == winning_miner_id), None)
            block = create_block(winning_miner, transactions, miner_evaluations[winning_miner.id], agent_dict, round_number)
            return block 
        else:
            round_number += 1

    # If no consensus, return None
    return None

def create_block(winning_miner, transactions, evaluations, agent_dict, round_number):
    previous_hash = blockchain[-1].compute_hash() if blockchain else '0' * 64
    signature = winning_miner.sign_data(previous_hash)
    block = Block(previous_hash, transactions, winning_miner.id, signature, round_number)
    # Update stakes based on evaluations
    update_stakes(evaluations, winning_miner, agent_dict, round_number)
    blockchain.append(block)
    return block

def update_stakes(evaluations, miner, agent_dict, round_number):
    for proposer_id, score in evaluations.items():
        proposer = agent_dict[proposer_id]
        if proposer.role == Role.WORKER:
            proposer.stake += score  # Reward based on evaluation score
    # Miner gets reward based on the difficulty (round_number)
    miner.stake += round_number

def display_agents(agents_dict):
    i = 1
    table = []
    headers = ["No", "Agent ID", "Stake", "Role", "Malicious"]
    for agent_id, agent in agents_dict.items():
        table.append([i, agent_id, agent.stake, agent.role, "True" if agent.is_malicious else "False"])
        i += 1
    print(" Agents:")
    print(tabulate(table, headers, tablefmt="grid"))
    print("")


def simulate(arg_agn, arg_min, arg_mal):
    num_agents = arg_agn     # Number of agents
    num_miners = arg_min     # Number of miners
    num_malicious = arg_mal  # Number of malicious agents
    agents = []

    # Initialize agents
    for i in range(num_agents):
        if i < num_malicious:
            agent = Agent(is_malicious=True)
        else:
            agent = Agent(is_malicious=False)
        agents.append(agent)

    agent_dict = {agent.id: agent for agent in agents}

    # Initialize blockchain
    global blockchain
    blockchain = []

    # Define the Task
    task = "Solve the following math problem: What is 12 multiplied by 15?"

    '''
    role assignment, 
    proposal statement, 
    evaluation,
    and decision-making.
    '''

    # Assign Roles
    miners, workers = assign_roles(agents, num_miners)

    # == DEBUG == 
    display_agents(agent_dict)

    # Generate proposals
    transactions = []
    for worker in workers:
        tx = worker.generate_proposal(task)
        if tx:
            transactions.append(tx)
        
    # Run the Consensus
    block = consensus(miners, transactions, agent_dict)
    if block:
        print("Consensus achieved. Block added to the blockchain.")
        print(f"Winning miner: {block.miner_id}")
        print(f"Block hash: {block.compute_hash()}")
        print("Final answer selected:")
        # Assuming the highest scored answer is selected
        highest_score = -1
        selected_answer = None
        for tx in block.transactions:
            print('>>',tx.answer)
            proposer = agent_dict[tx.proposer_id]
            score = proposer.stake
            if score > highest_score:
                highest_score = score
                selected_answer = tx.answer
        print(selected_answer)
    else:
        print("Consensus not achieved within the maximum rounds.")

def init():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('-a', '--agents', type=int, nargs='?', const=6, default=6, help='Number of agents')
    p.add_argument('-w', '--workers', type=int, nargs='?', const=3, default=3, help='Number of workers')
    p.add_argument('-m', '--malicious', type=int, nargs='?', const=2, default=2, help='Number of malicious agents')
    return p.parse_args()

if __name__ == "__main__":
    
    args = init()
    (arg_a, arg_w, arg_m) = (args.agents, args.workers, args.malicious)
    # print(f"Number of agents: {arg_a}")
    # print(f"Number of workers: {arg_w}")
    # print(f"Number of malicious agents: {arg_m}")

    simulate(arg_a, arg_w, arg_m)
