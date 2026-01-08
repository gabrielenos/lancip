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
  avatar_url: str | None = None


class AuthResponse(BaseModel):
  ok: bool
  user: PublicUser
  access_token: str


class ContactCreate(BaseModel):
  owner_id: int
  contact_id: int


class ContactOut(BaseModel):
  id: int
  owner_id: int
  contact: PublicUser