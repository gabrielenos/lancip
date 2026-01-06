from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
  name: str
  email: str
  password: str = Field(..., max_length=72)


class LoginRequest(BaseModel):
  email: str
  password: str = Field(..., max_length=72)


class PublicUser(BaseModel):
  id: int
  name: str
  email: str


class AuthResponse(BaseModel):
  ok: bool
  user: PublicUser
  access_token: str