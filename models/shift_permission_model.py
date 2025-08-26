from sqlalchemy import (
    Integer,
    String,
    BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base_model import BaseModel


class ShiftPermission(BaseModel):
    __tablename__ = "shift_permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Ensure unique combination of chat_id and username
    __table_args__ = (
        {"schema": None}  # Use default schema
    )