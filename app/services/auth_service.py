"""Service do Web3 autentykacji i weryfikacji podpisów"""

import secrets
import jwt
import os
from datetime import datetime, timedelta
from eth_account import Account
from eth_account.messages import encode_defunct


class Web3AuthService:
    """Service do obsługi autentykacji Web3 / MetaMask"""

    # Przechowywanie challenges w pamięci (w production użyć Redis lub bazy danych)
    _challenges = {}

    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24

    @staticmethod
    def generate_challenge(wallet: str) -> str:
        """Generuje random challenge do podpisania"""
        challenge = f"Vaulty Login Challenge: {secrets.token_hex(32)}"
        # Przechowaj challenge powiązany z wallet'em
        Web3AuthService._challenges[wallet] = {
            "challenge": challenge,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=15)
        }
        return challenge

    @staticmethod
    def verify_challenge_exists(wallet: str) -> bool:
        """Sprawdza czy challenge istnieje i nie wygasł"""
        if wallet not in Web3AuthService._challenges:
            return False

        challenge_data = Web3AuthService._challenges[wallet]
        if datetime.utcnow() > challenge_data["expires_at"]:
            # Challenge wygasł
            del Web3AuthService._challenges[wallet]
            return False

        return True

    @staticmethod
    def get_challenge(wallet: str) -> str:
        """Pobiera challenge dla wallet'a"""
        if wallet in Web3AuthService._challenges:
            return Web3AuthService._challenges[wallet]["challenge"]
        return None

    @staticmethod
    def clear_challenge(wallet: str):
        """Usuwa challenge po wykorzystaniu"""
        if wallet in Web3AuthService._challenges:
            del Web3AuthService._challenges[wallet]

    def verify_signature(self, wallet: str, signature: str) -> bool:
        """Weryfikuje podpis Ethereum"""
        try:
            # Pobierz challenge
            challenge = self.get_challenge(wallet)
            if not challenge:
                return False

            # Sprawdź czy challenge nie wygasł
            if not self.verify_challenge_exists(wallet):
                return False

            # Utwórz message w formacie Ethereum
            message = encode_defunct(text=challenge)

            # Konwertuj signature jeśli jest stringiem
            if isinstance(signature, str):
                # Usuń prefix 0x jeśli istnieje i konwertuj z hex
                sig_str = signature[2:] if signature.startswith("0x") else signature
                try:
                    signature_bytes = bytes.fromhex(sig_str)
                except ValueError:
                    return False
            else:
                signature_bytes = signature

            # Recover address z podpisu
            recovered_address = Account.recover_message(message, signature=signature_bytes)

            # Porównaj recovered address z wallet'em (bez względu na case)
            return recovered_address.lower() == wallet.lower()

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Signature verification error: {e}")
            return False

    def create_jwt_token(self, wallet: str) -> str:
        """Tworzy JWT token"""
        payload = {
            "wallet": wallet,
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def verify_jwt_token(self, token: str) -> dict:
        """Weryfikuje JWT token i zwraca payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token wygasł")
        except jwt.InvalidTokenError:
            raise Exception("Nieważny token")


# Singleton instance
auth_service = Web3AuthService()

