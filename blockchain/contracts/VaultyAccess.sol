// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VaultyAccess
 * @dev Kontrakt zarządzający uprawnieniami do plików w systemie Vaulty.
 *      Blockchain służy jako jedyne źródło prawdy (Source of Truth) o dostępie.
 */
contract VaultyAccess {
    // file_id -> owner
    mapping(uint256 => address) public fileOwners;
    // file_id -> user -> expiration_timestamp (sekundy od epoch)
    mapping(uint256 => mapping(address => uint256)) public accessExpiry;

    event FileRegistered(uint256 indexed fileId, address indexed owner, string cid);
    event AccessGranted(uint256 indexed fileId, address indexed user, uint256 expiration);
    event AccessRevoked(uint256 indexed fileId, address indexed user);

    modifier onlyOwner(uint256 fileId) {
        require(fileOwners[fileId] == msg.sender, "Tylko wlasciciel moze zarzadzac dostepem");
        _;
    }

    /**
     * @dev Rejestruje plik na blockchainie. Musi być wywołane zaraz po uploadzie na backend.
     */
    function registerFile(uint256 fileId, string memory cid) external {
        require(fileOwners[fileId] == address(0), "Plik o tym ID jest juz zarejestrowany");
        fileOwners[fileId] = msg.sender;
        emit FileRegistered(fileId, msg.sender, cid);
    }

    /**
     * @dev Nadaje dostęp do pliku konkretnemu użytkownikowi na określony czas.
     */
    function grantAccess(uint256 fileId, address user, uint256 expiration) external onlyOwner(fileId) {
        require(user != address(0), "Niepoprawny adres uzytkownika");
        accessExpiry[fileId][user] = expiration;
        emit AccessGranted(fileId, user, expiration);
    }

    /**
     * @dev Odbiera dostęp do pliku (ustawia wygaśnięcie na 0).
     */
    function revokeAccess(uint256 fileId, address user) external onlyOwner(fileId) {
        accessExpiry[fileId][user] = 0;
        emit AccessRevoked(fileId, user);
    }

    /**
     * @dev Główna funkcja sprawdzająca dostęp. Wywoływana przez Backend (view call).
     */
    function hasAccess(uint256 fileId, address user) external view returns (bool) {
        // Właściciel zawsze ma dostęp
        if (user == fileOwners[fileId]) {
            return true;
        }
        // Sprawdź czy dostęp nie wygasł (0 <= block.timestamp zawsze prawda, o ile dostęp nie został nadany)
        return accessExpiry[fileId][user] > 0 && block.timestamp <= accessExpiry[fileId][user];
    }
}
