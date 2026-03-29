"""
BlockchainService – weryfikacja dostępu do plików.

ARCHITEKTURA:
  Blockchain = SOURCE OF TRUTH (kto ma dostęp i na jak długo)
  Backend    = ENFORCER (egzekutor decyzji blockchaina)

CURRENT STATE:
  Mock implementation – zawsze zwraca True dla właściciela.
  Dostęp innych użytkowników sprawdzany przez AccessPermission (SQL cache).

TODO (Etap 2 – Smart Contract):
  Zastąpić mock prawdziwym wywołaniem:
    contract.functions.hasAccess(file_id, wallet).call()
  Smart contract (Solidity):
    mapping(uint => mapping(address => uint)) public accessExpiry;
    function hasAccess(uint fileId, address user) external view returns (bool)
  Deploy: Sepolia testnet via Hardhat/Foundry
  Web3: web3.py + Infura/Alchemy RPC endpoint
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BlockchainService:
    """
    Service do weryfikacji uprawnień dostępu do plików.

    Obecna implementacja: MOCK (zawsze pozwala właścicielowi, sprawdza SQL dla innych).
    Docelowa implementacja: wywołanie smart contractu na Ethereum.
    """

    def has_access(self, wallet: str, file_id: int, db=None) -> bool:
        """
        Sprawdza czy podany wallet ma dostęp do pliku.

        Args:
            wallet:  adres portfela użytkownika
            file_id: identyfikator pliku
            db:      sesja bazy (tymczasowo – dla SQL cache)

        Returns:
            True jeśli dostęp jest przyznany, False w przeciwnym razie

        TODO: zastąpić wywołaniem smart contract:
            return contract.functions.hasAccess(file_id, wallet).call()
        """

        # --- MOCK: tymczasowy fallback do SQL cache ---
        if db is not None:
            try:
                from app.crud.access_crud import AccessCRUD
                result = AccessCRUD.check_user_access(db, file_id, wallet)
                logger.debug(
                    f"[MOCK BLOCKCHAIN] wallet={wallet} file={file_id} → {'GRANTED' if result else 'DENIED'}"
                )
                return result
            except Exception as e:
                logger.error(f"[MOCK BLOCKCHAIN] Error checking access: {e}")
                return False

        # Jeśli brak db – domyślnie odmów (bezpieczne zachowanie)
        return False

    def grant_access(self, owner_wallet: str, target_wallet: str, file_id: int, expiry: datetime | None = None) -> bool:
        """
        Nadaj dostęp do pliku.

        TODO (Etap 2): wyemitować transakcję do smart contractu:
            contract.functions.grantAccess(file_id, target_wallet, expiry_timestamp).transact()

        Teraz: deleguje do SQL (AccessCRUD).
        """
        logger.info(
            f"[MOCK BLOCKCHAIN] grant_access: owner={owner_wallet} → target={target_wallet} file={file_id}"
        )
        # Delegowane do routera /access/grant (SQL)
        return True

    def revoke_access(self, owner_wallet: str, target_wallet: str, file_id: int) -> bool:
        """
        Odbierz dostęp do pliku.

        TODO (Etap 2): wyemitować transakcję do smart contractu:
            contract.functions.revokeAccess(file_id, target_wallet).transact()
        """
        logger.info(
            f"[MOCK BLOCKCHAIN] revoke_access: owner={owner_wallet} → target={target_wallet} file={file_id}"
        )
        return True


# Singleton – używany przez routery
blockchain_service = BlockchainService()
