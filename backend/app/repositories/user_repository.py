from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List
from backend.app.models.user import User

class UserRepository:
    """
    Data access repository for User entities.
    Encapsulates all SQLAlchemy queries for the users table.
    Usernames are case-insensitive unique.
    """
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        stmt = select(User).where(func.lower(User.username) == username.lower().strip())
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(User).order_by(User.id).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def count_active(db: Session) -> int:
        """Count active users in the system."""
        stmt = select(func.count(User.id)).where(User.is_active == True)
        return db.execute(stmt).scalar() or 0

    @staticmethod
    def deactivate(db: Session, user: User) -> User:
        """Set user is_active to False."""
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, password_hash: str) -> User:
        """Update user password hash."""
        user.password_hash = password_hash
        db.commit()
        db.refresh(user)
        return user
