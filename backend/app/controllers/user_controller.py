from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.user import UserCreate, UserRead
from backend.app.services.user_service import UserService
from backend.app.models.user import User

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("", response_model=UserRead, status_code=201)
def create_user(
    user_in: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user account. Any authenticated active user can create users.
    Minimum password length 8 characters. Passwords never returned or logged.
    """
    client_ip = request.client.host if request.client else None
    return UserService.create_user(
        db=db,
        user_in=user_in,
        acting_user=current_user,
        client_ip=client_ip
    )

@router.get("", response_model=List[UserRead])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered users. Any authenticated user can view users."""
    return UserService.list_users(db, skip=skip, limit=limit)

@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account.
    Guards: Cannot deactivate yourself or the last active user.
    """
    client_ip = request.client.host if request.client else None
    return UserService.deactivate_user(
        db=db,
        target_user_id=user_id,
        acting_user=current_user,
        client_ip=client_ip
    )
