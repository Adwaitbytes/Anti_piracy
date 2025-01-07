from web3 import Web3
from eth_account import Account
import json
from typing import Dict, Optional
import os

class BlockchainRegistry:
    def __init__(self):
        # Connect to local Ethereum node (replace with your node URL in production)
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        
        # Load contract ABI and address
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract_abi = self._load_contract_abi()
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        # Set up account (replace with secure key management in production)
        self.account = Account.from_key(os.getenv('PRIVATE_KEY'))
    
    def _load_contract_abi(self) -> list:
        """Load contract ABI from file."""
        abi_path = os.path.join(
            os.path.dirname(__file__),
            'contracts',
            'ContentRegistry.abi'
        )
        with open(abi_path, 'r') as f:
            return json.load(f)
    
    def register_content(
        self,
        content_id: str,
        content_hash: str,
        watermark: str
    ) -> str:
        """Register content on the blockchain."""
        # Prepare transaction
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        # Build transaction
        transaction = self.contract.functions.registerContent(
            content_id,
            content_hash,
            watermark
        ).build_transaction({
            'chainId': 1,  # Replace with your chain ID
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction,
            self.account.key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_receipt['transactionHash'].hex()
    
    def verify_content(
        self,
        content_id: str
    ) -> Optional[Dict[str, str]]:
        """Verify content ownership on the blockchain."""
        try:
            result = self.contract.functions.getContent(content_id).call()
            return {
                'owner': result[0],
                'content_hash': result[1],
                'watermark': result[2],
                'timestamp': result[3],
                'is_valid': True
            }
        except Exception:
            return None
    
    def update_content_status(
        self,
        content_id: str,
        is_valid: bool
    ) -> str:
        """Update content status (e.g., mark as pirated)."""
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        transaction = self.contract.functions.updateContentStatus(
            content_id,
            is_valid
        ).build_transaction({
            'chainId': 1,  # Replace with your chain ID
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction,
            self.account.key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt['transactionHash'].hex()
