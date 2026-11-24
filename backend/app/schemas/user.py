from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

RoleType = Literal["ADMIN", "ENCODER", "APPROVER"]

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: RoleType
    email: str | None = Field(default=None, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserRead(UserBase):
    id: int
    created_at: datetime

    # Pydantic v2 from_attributes enables reading from SQLAlchemy model instances
    model_config = ConfigDict(from_attributes=True)
