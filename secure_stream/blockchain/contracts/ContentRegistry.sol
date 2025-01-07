// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ContentRegistry {
    struct Content {
        address owner;
        string contentHash;
        string watermark;
        uint256 timestamp;
        bool isValid;
    }
    
    mapping(string => Content) private contents;
    
    event ContentRegistered(
        string contentId,
        address owner,
        string contentHash,
        uint256 timestamp
    );
    
    event ContentStatusUpdated(
        string contentId,
        bool isValid,
        uint256 timestamp
    );
    
    function registerContent(
        string memory contentId,
        string memory contentHash,
        string memory watermark
    ) public {
        require(contents[contentId].owner == address(0), "Content already registered");
        
        contents[contentId] = Content({
            owner: msg.sender,
            contentHash: contentHash,
            watermark: watermark,
            timestamp: block.timestamp,
            isValid: true
        });
        
        emit ContentRegistered(
            contentId,
            msg.sender,
            contentHash,
            block.timestamp
        );
    }
    
    function getContent(string memory contentId)
        public
        view
        returns (
            address owner,
            string memory contentHash,
            string memory watermark,
            uint256 timestamp,
            bool isValid
        )
    {
        Content memory content = contents[contentId];
        require(content.owner != address(0), "Content not found");
        
        return (
            content.owner,
            content.contentHash,
            content.watermark,
            content.timestamp,
            content.isValid
        );
    }
    
    function updateContentStatus(string memory contentId, bool isValid) public {
        require(contents[contentId].owner != address(0), "Content not found");
        require(
            msg.sender == contents[contentId].owner,
            "Only owner can update status"
        );
        
        contents[contentId].isValid = isValid;
        
        emit ContentStatusUpdated(
            contentId,
            isValid,
            block.timestamp
        );
    }
}
