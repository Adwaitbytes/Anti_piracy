from web3 import Web3
from dotenv import load_dotenv
import os
import json

def test_contract_connection():
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    contract_address = os.getenv('CONTRACT_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')
    web3_provider = os.getenv('WEB3_PROVIDER_URL')
    
    print(f"Testing connection to EDU Chain Testnet...")
    print(f"Contract Address: {contract_address}")
    print(f"Web3 Provider: {web3_provider}")
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(web3_provider))
    
    # Check connection
    if not w3.is_connected():
        print("[FAIL] Failed to connect to the network!")
        return
    
    print("[OK] Successfully connected to the network!")
    print(f"Current block number: {w3.eth.block_number}")
    
    # Load contract ABI
    abi_path = "secure_stream/blockchain/contracts/ContentRegistry.abi"
    with open(abi_path, 'r') as f:
        contract_abi = json.load(f)
    
    # Initialize contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    try:
        # Try to call a view function
        result = contract.functions.getContent("test").call()
        print("[FAIL] Unexpected success: getContent should fail for non-existent ID")
    except Exception as e:
        if "Content not found" in str(e):
            print("[OK] Contract is responding correctly!")
        else:
            print(f"[FAIL] Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_contract_connection()
