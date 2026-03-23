"""Service do obsługi IPFS"""

import ipfshttpclient
import os
import hashlib
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

IPFS_API_URL = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
# Tryb testowy - generuj fake CID zamiast wysyłać do IPFS
MOCK_MODE = os.getenv("MOCK_IPFS", "false").lower() == "true"


class IPFSService:
    """Service do komunikacji z IPFS"""

    def __init__(self):
        """Inicjalizacja połączenia z IPFS"""
        self.client = None
        self.mock_mode = MOCK_MODE
        
        if not self.mock_mode:
            try:
                self.client = ipfshttpclient.connect(IPFS_API_URL)
            except Exception as e:
                print(f"Ostrzeżenie: Nie mogę połączyć się z IPFS: {e}")
                print(f"Zmienia się na MOCK MODE")
                self.mock_mode = True

    def _generate_fake_cid(self, data: bytes) -> str:
        """Generuj fake CID na podstawie hash'u danych (dla testów)"""
        # CID v1 format: Qm + base58(multihash)
        # Dla uproszczenia użyjemy: QmFAKE + sha256
        data_hash = hashlib.sha256(data).hexdigest()
        fake_cid = f"QmFAKE{data_hash[:52]}"  # QmFAKE + pierwsze 52 znaki hasha
        return fake_cid

    def upload_file(self, file_bytes: bytes) -> str:
        """
        Wgraj plik do IPFS (lub zwróć fake CID w mock mode)

        Args:
            file_bytes: Zawartość pliku w bajtach

        Returns:
            CID (Content Identifier) pliku

        Raises:
            Exception: Jeśli upload się nie powiedzie
        """
        if self.mock_mode:
            # Zwróć fake CID dla testów
            cid = self._generate_fake_cid(file_bytes)
            print(f"[MOCK] Plik zarejestrowany z CID: {cid}")
            return cid

        if not self.client:
            raise Exception("IPFS client is not connected")

        try:
            result = self.client.add_bytes(file_bytes)
            cid = result
            print(f"Plik wgrany do IPFS: {cid}")
            return cid
        except Exception as e:
            raise Exception(f"IPFS upload failed: {str(e)}")

    def get_file(self, cid: str) -> bytes:
        """
        Pobierz plik z IPFS

        Args:
            cid: IPFS Content Identifier

        Returns:
            Zawartość pliku w bajtach

        Raises:
            Exception: Jeśli pobieranie się nie powiedzie
        """
        if not self.client:
            raise Exception("IPFS client is not connected")

        try:
            file_bytes = self.client.cat(cid)
            return file_bytes
        except Exception as e:
            raise Exception(f"IPFS download failed: {str(e)}")

    def pin_file(self, cid: str) -> bool:
        """
        Przypnij plik w IPFS (aby nie został usunięty)

        Args:
            cid: IPFS Content Identifier

        Returns:
            True jeśli operacja się powiodła

        Raises:
            Exception: Jeśli przypinanie się nie powiedzie
        """
        if not self.client:
            raise Exception("IPFS client is not connected")

        try:
            self.client.pin.add(cid)
            print(f"Plik przypięty: {cid}")
            return True
        except Exception as e:
            raise Exception(f"IPFS pin failed: {str(e)}")


# Globalna instancja
ipfs_service = IPFSService()


