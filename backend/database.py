import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def _env(name: str, default: str | None = None) -> str:
  value = os.getenv(name, default)
  if value is None or value == "":
    raise RuntimeError(f"Missing environment variable: {name}")
  return value


def _env_optional(name: str, default: str = "") -> str:
  value = os.getenv(name)
  if value is None:
    return default
  return value


DB_HOST = _env("DB_HOST", "localhost")
DB_PORT = _env("DB_PORT", "3306")
DB_USER = _env("DB_USER", "root")
DB_PASSWORD = _env_optional("DB_PASSWORD", "")
DB_NAME = _env("DB_NAME")

SQLALCHEMY_DATABASE_URL = (
  f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

engine = create_engine(
  SQLALCHEMY_DATABASE_URL,
  pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
