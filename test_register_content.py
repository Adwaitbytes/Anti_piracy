from web3 import Web3
from dotenv import load_dotenv
import os
import json
import hashlib

def test_register_content():
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    contract_address = os.getenv('CONTRACT_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    web3_provider = os.getenv('WEB3_PROVIDER_URL')
    
    print(f"Connecting to network...")
    w3 = Web3(Web3.HTTPProvider(web3_provider))
    
    if not w3.is_connected():
        print("[FAIL] Failed to connect to the network!")
        return
    
    # Load contract ABI
    abi_path = "secure_stream/blockchain/contracts/ContentRegistry.abi"
    with open(abi_path, 'r') as f:
        contract_abi = json.load(f)
    
    # Initialize contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    # Create account from private key
    account = w3.eth.account.from_key(private_key)
    print(f"Using account: {account.address}")
    
    # Test data
    content_id = "test_content_1"
    content_hash = hashlib.sha256(b"test content").hexdigest()
    watermark = "test_watermark_123"
    
    try:
        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Estimate gas
        gas_estimate = contract.functions.registerContent(
            content_id,
            content_hash,
            watermark
        ).estimate_gas({'from': account.address})
        
        print(f"Estimated gas needed: {gas_estimate}")
        
        # Add 10% buffer to gas estimate
        gas_limit = int(gas_estimate * 1.1)
        print(f"Using gas limit: {gas_limit}")
        
        transaction = contract.functions.registerContent(
            content_id,
            content_hash,
            watermark
        ).build_transaction({
            'chainId': int(os.getenv('NETWORK_ID', 656476)),
            'gas': gas_limit,
            'maxFeePerGas': w3.eth.gas_price,
            'maxPriorityFeePerGas': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign transaction
        signed_txn = w3.eth.account.sign_transaction(
            transaction,
            private_key
        )
        
        # Send transaction
        print("\nSending transaction to register content...")
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        print("Waiting for transaction confirmation...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt['status'] == 1:
            print("[OK] Content registered successfully!")
            print(f"Transaction hash: {tx_receipt['transactionHash'].hex()}")
            
            # Verify the content was registered
            print("\nVerifying content registration...")
            content = contract.functions.getContent(content_id).call()
            print(f"Owner: {content[0]}")
            print(f"Content Hash: {content[1]}")
            print(f"Watermark: {content[2]}")
            print(f"Timestamp: {content[3]}")
            print(f"Is Valid: {content[4]}")
        else:
            print("[FAIL] Transaction failed!")
            
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}")

if __name__ == "__main__":
    test_register_content()
