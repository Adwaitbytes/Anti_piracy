// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ContentRegistry {
    struct Content {
        string contentId;
        string contentHash;
        address owner;
        uint256 timestamp;
        string metadata;
        bool exists;
    }
    
    mapping(string => Content) public contents;
    mapping(address => string[]) public ownerContents;
    
    event ContentRegistered(
        string contentId,
        string contentHash,
        address owner,
        uint256 timestamp
    );
    
    event ContentVerified(
        string contentId,
        string contentHash,
        bool verified
    );
    
    function registerContent(
        string memory contentId,
        string memory contentHash,
        string memory metadata
    ) public {
        require(!contents[contentId].exists, "Content ID already exists");
        
        Content memory newContent = Content({
            contentId: contentId,
            contentHash: contentHash,
            owner: msg.sender,
            timestamp: block.timestamp,
            metadata: metadata,
            exists: true
        });
        
        contents[contentId] = newContent;
        ownerContents[msg.sender].push(contentId);
        
        emit ContentRegistered(
            contentId,
            contentHash,
            msg.sender,
            block.timestamp
        );
    }
    
    function verifyContent(
        string memory contentId,
        string memory contentHash
    ) public view returns (bool) {
        require(contents[contentId].exists, "Content not found");
        return keccak256(abi.encodePacked(contents[contentId].contentHash)) == 
               keccak256(abi.encodePacked(contentHash));
    }
    
    function getContent(string memory contentId)
        public
        view
        returns (
            string memory,
            string memory,
            address,
            uint256,
            string memory
        )
    {
        require(contents[contentId].exists, "Content not found");
        Content memory content = contents[contentId];
        return (
            content.contentId,
            content.contentHash,
            content.owner,
            content.timestamp,
            content.metadata
        );
    }
    
    function getOwnerContents(address owner)
        public
        view
        returns (string[] memory)
    {
        return ownerContents[owner];
    }
}
