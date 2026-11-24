from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from backend.app.models.user import User

class UserRepository:
    """
    Data access repository for User entities.
    Encapsulates all SQLAlchemy queries for the users table.
    """
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())
