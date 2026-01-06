from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import hash_password
from .auth import verify_password
from .auth import create_access_token
from .database import get_db
from .models import User
from .schemas import AuthResponse
from .schemas import LoginRequest
from .schemas import PublicUser
from .schemas import RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
  existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
  if existing is not None:
    raise HTTPException(status_code=400, detail="Email sudah terdaftar")

  user = User(
    name=payload.name,
    email=payload.email,
    password_hash=hash_password(payload.password),
  )
  db.add(user)
  db.commit()
  db.refresh(user)

  token = create_access_token({"sub": str(user.id), "email": user.email})

  return AuthResponse(
    ok=True,
    user=PublicUser(id=user.id, name=user.name, email=user.email),
    access_token=token,
  )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
  user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
  if user is None:
    raise HTTPException(status_code=401, detail="Email atau password salah")

  if not verify_password(payload.password, user.password_hash):
    raise HTTPException(status_code=401, detail="Email atau password salah")

  token = create_access_token({"sub": str(user.id), "email": user.email})

  return AuthResponse(
    ok=True,
    user=PublicUser(id=user.id, name=user.name, email=user.email),
    access_token=token,
  )
