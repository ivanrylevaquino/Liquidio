from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository
from backend.app.core.security import verify_password, create_access_token
from backend.app.schemas.auth import TokenResponse
from backend.app.schemas.user import UserRead

class AuthService:
    """
    Business service encapsulating authentication, session token issuance,
    and audit logging for all authentication events.
    """
    @staticmethod
    def authenticate(
        db: Session,
        username: str,
        password: str,
        ip_address: str | None = None
    ) -> TokenResponse:
        user = UserRepository.get_by_username(db, username=username)

        # 1. Unrecognized username
        if not user:
            ActivityLogRepository.insert(
                db=db,
                action_type="LOGIN_FAILED",
                entity_name="users",
                entity_id=None,
                user_id=None,
                details={"attempted_username": username, "reason": "User not found"},
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Deactivated account
        if not user.is_active:
            ActivityLogRepository.insert(
                db=db,
                action_type="LOGIN_FAILED",
                entity_name="users",
                entity_id=user.id,
                user_id=user.id,
                details={"username": user.username, "reason": "Account deactivated"},
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # 3. Invalid password
        if not verify_password(password, user.password_hash):
            ActivityLogRepository.insert(
                db=db,
                action_type="LOGIN_FAILED",
                entity_name="users",
                entity_id=user.id,
                user_id=user.id,
                details={"username": user.username, "reason": "Invalid credentials"},
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 4. Successful authentication
        ActivityLogRepository.insert(
            db=db,
            action_type="LOGIN_SUCCESS",
            entity_name="users",
            entity_id=user.id,
            user_id=user.id,
            details={"username": user.username, "role": user.role},
            ip_address=ip_address
        )

        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
        access_token = create_access_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead.model_validate(user)
        )
