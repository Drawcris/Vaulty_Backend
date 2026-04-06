"""CRUD operacje dla użytkowników i aliasów username."""

from sqlalchemy.orm import Session

from app.models import User


class UserCRUD:
    @staticmethod
    def get_by_wallet(db: Session, wallet: str) -> User | None:
        return db.query(User).filter(User.wallet == wallet).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def search_usernames(db: Session, query: str) -> list[User]:
        return db.query(User).filter(User.username.ilike(f"%{query}%")).limit(10).all()

    @staticmethod
    def create_user(db: Session, wallet: str, username: str, encryption_public_key: str | None = None) -> User:
        user = User(wallet=wallet, username=username, encryption_public_key=encryption_public_key)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_public_key(db: Session, user: User, encryption_public_key: str) -> User:
        user.encryption_public_key = encryption_public_key
        db.commit()
        db.refresh(user)
        return user
