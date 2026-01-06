from datetime import datetime, timedelta
import os

import jwt
from passlib.context import CryptContext

# Ganti bcrypt dengan pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 60 * 2


def hash_password(password: str) -> str:
  return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
  return pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
  to_encode = data.copy()
  if expires_delta is None:
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  expire = datetime.utcnow() + expires_delta
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
  return encoded_jwt