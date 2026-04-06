from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import get_routers

app = FastAPI(
    title="Vaulty Backend API",
    description="Backend dla aplikacji Vaulty - secure file sharing na blockchain",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:3000",
        "http://127.0.0.1:4200",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Encrypted-CEK"]
)

# Rejestruj wszystkie routery
for router in get_routers():
    app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Vaulty Backend API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth/challenge, /auth/verify",
            "docs": "/docs"
        }
    }
