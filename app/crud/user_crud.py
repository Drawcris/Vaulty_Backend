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
    def create_user(db: Session, wallet: str, username: str) -> User:
        user = User(wallet=wallet, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
