// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SecureFileStorage {
    struct FileRecord {
        string fileHash;
        address owner;
        uint256 timestamp;
        bool exists;
    }

    mapping(string => FileRecord) private files;
    mapping(address => string[]) private ownerFiles;

    event FileStored(string indexed fileHash, address indexed owner, uint256 timestamp);

    function storeFileHash(string memory _fileHash) public {
        require(!files[_fileHash].exists, "File hash already exists on blockchain");
        
        files[_fileHash] = FileRecord({
            fileHash: _fileHash,
            owner: msg.sender,
            timestamp: block.timestamp,
            exists: true
        });

        ownerFiles[msg.sender].push(_fileHash);

        emit FileStored(_fileHash, msg.sender, block.timestamp);
    }

    function verifyFileIntegrity(string memory _fileHash) public view returns (bool, address, uint256) {
        if (files[_fileHash].exists) {
            return (true, files[_fileHash].owner, files[_fileHash].timestamp);
        }
        return (false, address(0), 0);
    }

    function getOwner(string memory _fileHash) public view returns (address) {
        return files[_fileHash].owner;
    }

    function getFilesByOwner(address _owner) public view returns (string[] memory) {
        return ownerFiles[_owner];
    }
}
