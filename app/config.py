"""Konfiguracja aplikacji"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost/vaultyDB"
)

# JWT
JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "your-super-secret-jwt-key-change-this-in-production"
)

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
CHALLENGE_EXPIRATION_MINUTES = int(os.getenv("CHALLENGE_EXPIRATION_MINUTES", "15"))

# File upload settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))

# IPFS settings
IPFS_API_URL = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
MOCK_IPFS = os.getenv("MOCK_IPFS", "false").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API
API_TITLE = "Vaulty Backend API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Backend dla aplikacji Vaulty - secure file sharing na blockchain"

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

