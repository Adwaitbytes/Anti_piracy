import pytest
from unittest.mock import Mock, patch
from secure_stream.blockchain import ContentRegistry
from datetime import datetime
import json

@pytest.fixture
def mock_web3():
    """Create a mock Web3 instance."""
    with patch('secure_stream.blockchain.Web3') as mock:
        # Mock contract functions
        contract_mock = Mock()
        contract_mock.functions.registerContent.return_value.build_transaction.return_value = {
            'to': '0x123',
            'data': '0x456',
            'gas': 2000000,
            'gasPrice': 20000000000,
            'nonce': 0
        }
        
        # Mock transaction receipt
        receipt_mock = Mock()
        receipt_mock.status = 1
        
        # Set up Web3 mock
        mock.return_value.eth.contract.return_value = contract_mock
        mock.return_value.eth.get_transaction_count.return_value = 0
        mock.return_value.eth.wait_for_transaction_receipt.return_value = receipt_mock
        
        yield mock

@pytest.fixture
def content_registry(mock_web3):
    """Create a ContentRegistry instance with mocked Web3."""
    return ContentRegistry(
        provider_url="http://localhost:8545",
        contract_address="0x123456789",
        private_key="0x" + "a" * 64  # 32 bytes private key
    )

class TestContentRegistry:
    def test_register_content(self, content_registry):
        """Test content registration on blockchain."""
        # Test data
        content_id = "test_content_123"
        content_hash = "0xabcdef123456"
        metadata = {
            "title": "Test Content",
            "owner": "Test Owner",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Register content
        success = content_registry.register_content(
            content_id,
            content_hash,
            metadata
        )
        
        assert success is True
        
        # Verify contract interaction
        contract = content_registry.contract
        contract.functions.registerContent.assert_called_once_with(
            content_id,
            content_hash,
            json.dumps(metadata)
        )

    def test_verify_content(self, content_registry):
        """Test content verification."""
        content_id = "test_content_123"
        content_hash = "0xabcdef123456"
        
        # Mock contract response
        content_registry.contract.functions.getContentInfo.return_value.call.return_value = [
            content_hash,
            "{}",
            int(datetime.utcnow().timestamp())
        ]
        
        # Verify content
        is_authentic = content_registry.verify_content(content_id, content_hash)
        assert is_authentic is True
        
        # Test with wrong hash
        is_authentic = content_registry.verify_content(
            content_id,
            "0xwronghash"
        )
        assert is_authentic is False

    def test_get_content_history(self, content_registry):
        """Test content history retrieval."""
        content_id = "test_content_123"
        timestamp = int(datetime.utcnow().timestamp())
        
        # Mock contract response
        content_registry.contract.functions.getContentInfo.return_value.call.return_value = [
            "0xabcdef123456",
            json.dumps({
                "title": "Test Content",
                "owner": "Test Owner"
            }),
            timestamp
        ]
        
        # Get history
        history = content_registry.get_content_history(content_id)
        
        assert history["content_id"] == content_id
        assert "content_hash" in history
        assert "metadata" in history
        assert "timestamp" in history
        
        # Verify metadata parsing
        assert history["metadata"]["title"] == "Test Content"
        assert history["metadata"]["owner"] == "Test Owner"

    @pytest.mark.parametrize("error_type", [
        ValueError,
        ConnectionError,
        Exception
    ])
    def test_error_handling(self, content_registry, error_type):
        """Test error handling for various scenarios."""
        content_id = "test_content_123"
        content_hash = "0xabcdef123456"
        
        # Mock contract to raise error
        content_registry.contract.functions.getContentInfo.return_value.call.side_effect = error_type("Test error")
        
        # Test verification error handling
        is_authentic = content_registry.verify_content(content_id, content_hash)
        assert is_authentic is False
        
        # Test history error handling
        history = content_registry.get_content_history(content_id)
        assert history == {}
