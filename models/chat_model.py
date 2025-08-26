import typing

if typing.TYPE_CHECKING:
    pass

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    BigInteger,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base_model import BaseModel


class Chat(BaseModel):
    __tablename__ = "chat_group"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
    enable_shift: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    registered_by: Mapped[str] = mapped_column(String(20), nullable=True)
    usd_threshold: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    khr_threshold: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="chats")
