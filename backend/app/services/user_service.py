from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.core.security import hash_password

class UserService:
    """
    Business logic service for user management.
    Enforces business rules:
    - Min 8 chars password
    - Cannot deactivate self
    - Cannot deactivate the last active user
    - Audit log for user creation and deactivation
    """
    @staticmethod
    def create_user(
        db: Session,
        user_in: UserCreate,
        acting_user: User,
        client_ip: str | None = None
    ) -> User:
        # Check for existing username
        existing = UserRepository.get_by_username(db, user_in.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_in.username}' is already registered."
            )

        if len(user_in.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long."
            )

        # Hash password securely with bcrypt
        pwd_hash = hash_password(user_in.password)

        new_user = User(
            username=user_in.username,
            password_hash=pwd_hash,
            full_name=user_in.full_name,
            role="USER",
            email=user_in.email,
            is_active=True
        )
        created = UserRepository.create(db, new_user)

        # Append-only audit log (sensitive password excluded)
        ActivityLogRepository.insert(
            db=db,
            action_type="USER_CREATE",
            entity_name="users",
            entity_id=created.id,
            user_id=acting_user.id,
            details={
                "username": created.username,
                "full_name": created.full_name,
                "email": created.email,
            },
            ip_address=client_ip
        )

        return created

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return UserRepository.get_all(db, skip=skip, limit=limit)

    @staticmethod
    def deactivate_user(
        db: Session,
        target_user_id: int,
        acting_user: User,
        client_ip: str | None = None
    ) -> User:
        # Guard 1: Cannot deactivate yourself
        if acting_user.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account."
            )

        target_user = UserRepository.get_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {target_user_id} not found."
            )

        if not target_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{target_user.username}' is already deactivated."
            )

        # Guard 2: Cannot deactivate the last active user
        active_count = UserRepository.count_active(db)
        if active_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active user in the system."
            )

        deactivated = UserRepository.deactivate(db, target_user)

        # Append-only audit log
        ActivityLogRepository.insert(
            db=db,
            action_type="USER_DEACTIVATE",
            entity_name="users",
            entity_id=deactivated.id,
            user_id=acting_user.id,
            details={
                "target_username": deactivated.username,
                "target_user_id": deactivated.id,
            },
            ip_address=client_ip
        )

        return deactivated
