import json
import os
import logging
from web3 import Web3
from datetime import datetime

logger = logging.getLogger(__name__)


class BlockchainService:
    """
    Service do weryfikacji uprawnień dostępu do plików na blockchainie.

    ARCHITEKTURA:
      Blockchain = SOURCE OF TRUTH (kto ma dostęp i na jak długo).
    """

    def __init__(self):
        # Lokalny węzeł Hardhat (Etap 2)
        # TODO: W przyszłości pobierać z pliku .env
        self.rpc_url = "http://127.0.0.1:8545"
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # Ścieżki do plików kontraktu
        # Ścieżka bazowa: c:\Magisterka\Vaulty\Backend
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.deployment_file = os.path.join(self.base_dir, "blockchain", "deployment.json")
        self.abi_file = os.path.join(self.base_dir, "blockchain", "artifacts", "contracts", "VaultyAccess.sol", "VaultyAccess.json")

        self.contract = None
        self._load_contract()

    def _load_contract(self):
        """Ładuje adres kontraktu i ABI z plików wdrożenia."""
        try:
            if not os.path.exists(self.deployment_file):
                logger.warning(f"[Blockchain] Nie znaleziono pliku wdrożenia: {self.deployment_file}")
                return

            if not os.path.exists(self.abi_file):
                logger.warning(f"[Blockchain] Nie znaleziono pliku ABI: {self.abi_file}")
                return

            with open(self.deployment_file, "r") as f:
                deploy_data = json.load(f)

            with open(self.abi_file, "r") as f:
                artifact_data = json.load(f)

            self.contract = self.w3.eth.contract(
                address=deploy_data["address"],
                abi=artifact_data["abi"]
            )
            logger.info(f"[Blockchain] Połączono z kontraktem pod adresem: {deploy_data['address']}")

        except Exception as e:
            logger.error(f"[Blockchain] Błąd podczas ładowania kontraktu: {e}")

    def has_access(self, wallet: str, file_id: int, db=None) -> bool:
        """
        Sprawdza dostęp na blockchainie.
        Jeśli kontrakt nie jest dostępny, wraca do SQL cache (fallback).
        """
        if self.contract and self.w3.is_connected():
            try:
                # Adresy w web3.py muszą być checksummed
                checksum_wallet = Web3.to_checksum_address(wallet)
                logger.info(f"[Blockchain] Checking access for file_id={file_id}, wallet={checksum_wallet}")
                
                # Wywołanie view call: hasAccess(uint256, address)
                result = self.contract.functions.hasAccess(file_id, checksum_wallet).call()
                logger.info(f"[Blockchain] Result from contract: {result}")
                
                if result:
                    return True
                
                # Jeśli False, sprawdź czy to nie błąd synchronizacji danych (np. plik nie zarejestrowany)
                # W Etapie 2 blockchain jest SOURCE OF TRUTH.
                
            except Exception as e:
                logger.error(f"[Blockchain] Błąd podczas hasAccess call: {e}")
                # Kontynuuj do fallbacka

        # --- FALLBACK: tymczasowy fallback do SQL cache ---
        if db is not None:
            try:
                from app.crud.access_crud import AccessCRUD
                result = AccessCRUD.check_user_access(db, file_id, wallet)
                logger.info(f"[FALLBACK] SQL cache check for wallet={wallet} file={file_id} → {result}")
                return result
            except Exception as e:
                logger.error(f"[Blockchain Fallback] Error checking access: {e}")
                return False

        return False

    def grant_access(self, owner_wallet: str, target_wallet: str, file_id: int, expiry: datetime | None = None) -> bool:
        """
        W modelu Etapu 2, grant_access jest wykonywane przez FRONTEND (MetaMask).
        Backend tylko odnotowuje ten fakt w logach (opcjonalnie).
        """
        logger.info(f"[Blockchain] grant_access on-chain manual action expected for file {file_id}")
        return True

    def revoke_access(self, owner_wallet: str, target_wallet: str, file_id: int) -> bool:
        """
        W modelu Etapu 2, revoke_access jest wykonywane przez FRONTEND (MetaMask).
        """
        logger.info(f"[Blockchain] revoke_access on-chain manual action expected for file {file_id}")
        return True


# Singleton
blockchain_service = BlockchainService()
