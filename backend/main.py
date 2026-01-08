from typing import Dict, List

import json

from fastapi import Depends, HTTPException
from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, select
from sqlalchemy.orm import Session

from . import models
from .auth_routes import router as auth_router
from .database import Base
from .database import engine
from .database import get_db
from .models import User, Contact
from .schemas import ContactCreate, ContactOut, PublicUser

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

app.include_router(auth_router)


class ConnectionManager:
  """Mengelola koneksi WebSocket per-user.

  Setiap userId bisa punya beberapa koneksi (beberapa tab/browser) sekaligus.
  Pesan bisa diarahkan hanya ke pengirim dan penerima (private).
  """

  def __init__(self) -> None:
    self.connections: Dict[int, List[WebSocket]] = {}

  async def connect(self, user_id: int, websocket: WebSocket) -> None:
    await websocket.accept()
    self.connections.setdefault(user_id, []).append(websocket)

  def disconnect(self, user_id: int, websocket: WebSocket) -> None:
    conns = self.connections.get(user_id)
    if not conns:
      return
    if websocket in conns:
      conns.remove(websocket)
    if not conns:
      self.connections.pop(user_id, None)

  async def send_to_user(self, user_id: int, message: str) -> None:
    conns = list(self.connections.get(user_id, []))
    for ws in conns:
      try:
        await ws.send_text(message)
      except Exception:
        # Jika gagal kirim ke satu koneksi, putuskan saja koneksi itu
        self.disconnect(user_id, ws)


manager = ConnectionManager()


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


@app.get("/contacts", response_model=list[ContactOut])
def list_contacts(owner_id: int, db: Session = Depends(get_db)):
  stmt = (
    select(Contact, User)
    .join(User, User.id == Contact.contact_id)
    .where(Contact.owner_id == owner_id)
  )
  rows = db.execute(stmt).all()

  result: list[ContactOut] = []
  for contact_row, user_row in rows:
    result.append(
      ContactOut(
        id=contact_row.id,
        owner_id=contact_row.owner_id,
        contact=PublicUser(
          id=user_row.id,
          name=user_row.name,
          email=user_row.email,
          avatar_url=user_row.avatar_url,
        ),
      )
    )
  return result


@app.post("/contacts", response_model=ContactOut)
def add_contact(payload: ContactCreate, db: Session = Depends(get_db)):
  owner = db.get(User, payload.owner_id)
  contact_user = db.get(User, payload.contact_id)
  if owner is None or contact_user is None:
    raise HTTPException(status_code=400, detail="Owner atau contact tidak ditemukan")

  existing = db.execute(
    select(Contact).where(
      Contact.owner_id == payload.owner_id,
      Contact.contact_id == payload.contact_id,
    )
  ).scalar_one_or_none()
  if existing:
    return ContactOut(
      id=existing.id,
      owner_id=existing.owner_id,
      contact=PublicUser(
        id=contact_user.id,
        name=contact_user.name,
        email=contact_user.email,
        avatar_url=contact_user.avatar_url,
      ),
    )

  new_contact = Contact(owner_id=payload.owner_id, contact_id=payload.contact_id)
  db.add(new_contact)
  db.commit()
  db.refresh(new_contact)

  return ContactOut(
    id=new_contact.id,
    owner_id=new_contact.owner_id,
    contact=PublicUser(
      id=contact_user.id,
      name=contact_user.name,
      email=contact_user.email,
      avatar_url=contact_user.avatar_url,
    ),
  )


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, userId: int):
  """WebSocket per-user.

  Setiap koneksi terikat ke satu userId. Pesan yang diterima di sini
  diharapkan berupa JSON yang memuat senderId dan targetId, dan
  hanya akan diteruskan ke kedua user tersebut.
  """

  user_id = userId
  await manager.connect(user_id, websocket)
  try:
    while True:
      raw = await websocket.receive_text()
      try:
        payload = json.loads(raw)
      except json.JSONDecodeError:
        # Jika bukan JSON yang valid, abaikan saja
        continue

      sender_id = payload.get("senderId")
      target_id = payload.get("targetId")

      if not isinstance(sender_id, int) or not isinstance(target_id, int):
        # Pesan tidak punya informasi routing yang jelas
        continue

      # Teruskan pesan ke pengirim (untuk echo) dan penerima
      await manager.send_to_user(sender_id, raw)
      if target_id != sender_id:
        await manager.send_to_user(target_id, raw)

  except WebSocketDisconnect:
    manager.disconnect(user_id, websocket)

