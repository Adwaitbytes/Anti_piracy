from web3 import Web3
from eth_account import Account
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class BlockchainRegistry:
    def __init__(self, provider_url: str, contract_address: str, private_key: str):
        """Initialize blockchain registry with Ethereum connection."""
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Load contract ABI
        contract_path = os.path.join(
            os.path.dirname(__file__),
            'contracts',
            'ContentRegistry.json'
        )
        with open(contract_path) as f:
            contract_json = json.load(f)
            self.contract_abi = contract_json['abi']
        
        # Setup contract
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=self.contract_abi
        )
        
        # Setup account
        self.account = Account.from_key(private_key)
        
    def register_content(
        self,
        content_id: str,
        content_hash: str,
        metadata: Dict
    ) -> bool:
        """Register content on blockchain."""
        try:
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Build transaction
            txn = self.contract.functions.registerContent(
                content_id,
                content_hash,
                json.dumps(metadata)
            ).build_transaction({
                'chainId': 1,  # Use appropriate chain ID
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                txn,
                private_key=self.account.key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return tx_receipt.status == 1
            
        except Exception as e:
            print(f"Failed to register content: {str(e)}")
            return False
            
    def verify_content(self, content_id: str, content_hash: str) -> bool:
        """Verify content on blockchain."""
        try:
            return self.contract.functions.verifyContent(
                content_id,
                content_hash
            ).call()
        except Exception as e:
            print(f"Failed to verify content: {str(e)}")
            return False
            
    def get_content(self, content_id: str) -> Optional[Dict]:
        """Get content details from blockchain."""
        try:
            content = self.contract.functions.getContent(content_id).call()
            return {
                'content_id': content[0],
                'content_hash': content[1],
                'owner': content[2],
                'timestamp': datetime.fromtimestamp(content[3]),
                'metadata': json.loads(content[4])
            }
        except Exception as e:
            print(f"Failed to get content: {str(e)}")
            return None
            
    def get_owner_contents(self, owner_address: str) -> List[str]:
        """Get all content IDs owned by an address."""
        try:
            return self.contract.functions.getOwnerContents(owner_address).call()
        except Exception as e:
            print(f"Failed to get owner contents: {str(e)}")
            return []
