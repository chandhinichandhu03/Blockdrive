import os
import json
from web3 import Web3

class BlockchainInterface:
    def __init__(self):
        # In a real app, you'd connect to Ganache or an Infura node
        # self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        self.w3 = None
        self.is_connected = False
        
        # Simulation storage (since we might not have a running node)
        self.simulation_db = os.path.join(os.path.dirname(__file__), 'blockchain_sim.json')
        if not os.path.exists(self.simulation_db):
            with open(self.simulation_db, 'w') as f:
                json.dump({}, f)

    def _get_sim_data(self):
        with open(self.simulation_db, 'r') as f:
            return json.load(f)

    def _save_sim_data(self, data):
        with open(self.simulation_db, 'w') as f:
            json.dump(data, f)

    def store_file_hash(self, file_hash, owner_address):
        # Simulation
        data = self._get_sim_data()
        if file_hash in data:
            return False, "Hash already exists"
        
        tx_hash = hashlib.sha256(f"{file_hash}{owner_address}{os.urandom(8)}".encode()).hexdigest()
        data[file_hash] = {
            "owner": owner_address,
            "tx_hash": tx_hash,
            "timestamp": str(datetime.now())
        }
        self._save_sim_data(data)
        return True, tx_hash

    def verify_file(self, file_hash):
        data = self._get_sim_data()
        if file_hash in data:
            return True, data[file_hash]
        return False, None

# Importing datetime inside the class or top level
from datetime import datetime
import hashlib
