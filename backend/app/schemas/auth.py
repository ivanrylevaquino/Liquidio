from pydantic import BaseModel, Field
from backend.app.schemas.user import UserRead

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Account username")
    password: str = Field(..., min_length=1, description="Account password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
