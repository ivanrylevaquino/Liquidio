from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.schemas.user import UserRead
from backend.app.services.auth_service import AuthService
from backend.app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user via username and password.
    Returns short-lived JWT token and user profile metadata.
    Logs authentication event (success/failed) in the append-only activity_logs table.
    """
    client_ip = request.client.host if request.client else None
    return AuthService.authenticate(
        db=db,
        username=login_data.username,
        password=login_data.password,
        ip_address=client_ip
    )

@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve authenticated user profile.
    Protected by JWT bearer token dependency.
    """
    return current_user
