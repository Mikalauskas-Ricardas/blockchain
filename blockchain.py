import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self) -> None:
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }

        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            previous_proof = previous_block['proof']
            current_proof = block['proof']
            hash = hashlib.sha256(str(current_proof**2 - previous_proof**2).encode()).hexdigest()

            if hash[:4] != '0000':
                return False
            
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for nodes in network:
            response = requests.get(f'http://{nodes}/get_chain')
            if response.status_code == 200:
                currentNodeLength = response.json()['length']
                currentNodeChain = response.json()['length']
                if currentNodeLength > max_length and self.is_chain_valid(currentNodeChain):
                    max_length = currentNodeLength
                    longest_chain = currentNodeChain
        
        if longest_chain:
            self.chain = longest_chain
            return True
        
        return False

app = Flask(__name__)
node_address = str(uuid4()).replace('-', '')
blockchain = Blockchain()

@app.route("/mine_block", methods = ['GET'])
def mine_block():
    start_time = datetime.datetime.now()
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # blockchain.add_transaction(sender = node_address, receiver = 'Ricardas', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    end_date = datetime.datetime.now()

    response = {
        'message': 'Block has been mined! :)',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions'],
        'process_time': '{}'.format(end_date - start_time)
    }

    return jsonify(response), 200

@app.route("/get_chain", methods = ['GET'])
def get_chain():
    response = {
        'length': len(blockchain.chain),
        'chain': blockchain.chain
    }

    return jsonify(response), 200

@app.route("/is_chain_valid", methods = ['GET'])
def is_chain_valid():
    response = {
        'is_chain_valid': blockchain.is_chain_valid(blockchain.chain)
    }

    return jsonify(response), 200

@app.route("/add_transaction", methods = ['POST'])
def add_transaction():
    data = request.get_json()
    transactions_keys = ['sender', 'receiver', 'amount']
    if not all (key in data for key in transactions_keys):
        return 'Bad request', 400
    
    index = blockchain.add_transaction(sender = data["sender"], receiver = data["receiver"], amount = data["amount"])
    return jsonify({
        'message': f'Transaction added to block: #{index}'
    }), 201
 
@app.route("/connect_node", methods = ['POST'])
def connect_node():
    data = request.get_json()
    nodes = data.get('nodes')
    
    if nodes is None:
        return "No nodes to connect", 400
    
    for node in nodes:
        blockchain.add_node(node)

    return jsonify({
        'message': 'Nodes added successfully',
        'total_nodes': list(blockchain.nodes)
    }), 201

@app.route("/replace_chain", methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()

    if is_chain_valid:
        return jsonify({
            'message': 'The chain was replaced',
            'new_chain': blockchain.chain
        }), 200
    
    return jsonify({
        'Message': 'No changes',
        'actual_chain': blockchain.chain
    }), 200


app.run(host = '0.0.0.0', port = 5000)