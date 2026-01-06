from fastapi import Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models
from .auth_routes import router as auth_router
from .database import Base
from .database import engine
from .database import get_db

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
  Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
  return {"status": "ok"}


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
  row = db.execute(text("SELECT 1 AS ok")).mappings().first()
  return {"db": "ok", "result": dict(row) if row else None}


@app.get("/stats")
def get_stats():
  # Endpoint sederhana untuk dashboard
  # Nanti bisa diganti hitung beneran dari database
  return {
    "revenue": 24500,
    "activity": 1200,
    "satisfaction": 98,
  }
