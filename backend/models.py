from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(primary_key=True, index=True)
  email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255))
  password_hash: Mapped[str] = mapped_column(String(255))
  # URL avatar user (nullable). Type hint tetap str untuk menghindari masalah Union.
  avatar_url: Mapped[str] = mapped_column(String(2048), nullable=True)


class Contact(Base):
  __tablename__ = "contacts"

  id: Mapped[int] = mapped_column(primary_key=True, index=True)

  # user pemilik daftar kontak (yang login)
  owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

  # user yang dijadikan kontak
  contact_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

  # kombinasi owner_id + contact_id harus unik
  __table_args__ = (
    UniqueConstraint("owner_id", "contact_id", name="uq_owner_contact"),
  )