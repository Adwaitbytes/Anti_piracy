from web3 import Web3
from eth_account import Account
import json
from typing import Dict, Any, Optional
import os
from datetime import datetime

class ContentRegistry:
    """Manages content registration and tracking on the blockchain."""
    
    # Smart contract ABI - simplified version for demo
    CONTRACT_ABI = [
        {
            "inputs": [
                {"type": "string", "name": "contentId"},
                {"type": "string", "name": "contentHash"},
                {"type": "string", "name": "metadata"}
            ],
            "name": "registerContent",
            "outputs": [{"type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"type": "string", "name": "contentId"}
            ],
            "name": "getContentInfo",
            "outputs": [
                {"type": "string", "name": "contentHash"},
                {"type": "string", "name": "metadata"},
                {"type": "uint256", "name": "timestamp"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self, provider_url: str, contract_address: str, private_key: Optional[str] = None):
        """
        Initialize the blockchain connection.
        
        Args:
            provider_url: Ethereum node URL
            contract_address: Deployed smart contract address
            private_key: Private key for signing transactions
        """
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract_address = contract_address
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=self.CONTRACT_ABI
        )
        
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()

    def register_content(self, content_id: str, content_hash: str, metadata: Dict[str, Any]) -> bool:
        """
        Register new content on the blockchain.
        
        Args:
            content_id: Unique identifier for the content
            content_hash: Hash of the content
            metadata: Additional content metadata
            
        Returns:
            Success status
        """
        try:
            # Prepare transaction
            metadata_str = json.dumps(metadata)
            
            transaction = self.contract.functions.registerContent(
                content_id,
                content_hash,
                metadata_str
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, self.account.key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.status == 1
            
        except Exception as e:
            print(f"Failed to register content: {str(e)}")
            return False

    def verify_content(self, content_id: str, content_hash: str) -> bool:
        """
        Verify content authenticity against blockchain record.
        
        Args:
            content_id: Content identifier
            content_hash: Hash to verify
            
        Returns:
            True if content is authentic
        """
        try:
            stored_hash, _, _ = self.contract.functions.getContentInfo(content_id).call()
            return stored_hash == content_hash
        except Exception as e:
            print(f"Failed to verify content: {str(e)}")
            return False

    def get_content_history(self, content_id: str) -> Dict[str, Any]:
        """
        Retrieve content registration history.
        
        Args:
            content_id: Content identifier
            
        Returns:
            Dictionary containing content history
        """
        try:
            content_hash, metadata_str, timestamp = self.contract.functions.getContentInfo(
                content_id
            ).call()
            
            return {
                'content_id': content_id,
                'content_hash': content_hash,
                'metadata': json.loads(metadata_str),
                'timestamp': datetime.fromtimestamp(timestamp).isoformat()
            }
        except Exception as e:
            print(f"Failed to get content history: {str(e)}")
            return {}
