from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at_utc: str
    user_id: str
    role: str


class CurrentUserResponse(BaseModel):
    user_id: str
    role: str
