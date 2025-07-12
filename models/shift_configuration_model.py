import json
from contextlib import contextmanager
from typing import Optional, Generator, Any, List

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    BigInteger,
    String,
    Text,
)
from sqlalchemy.orm import Session

from config.database_config import SessionLocal
from models.base_model import BaseModel


class ShiftConfiguration(BaseModel):
    __tablename__ = "shift_configurations"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False, unique=True)
    
    # Auto close configuration
    auto_close_enabled = Column(Boolean, nullable=False, default=False)
    auto_close_times = Column(Text, nullable=True)  # JSON array of times (e.g., ["08:00", "16:00", "23:59"])
    
    # Shift naming/numbering preferences
    shift_name_prefix = Column(String(50), nullable=True, default="Shift")
    reset_numbering_daily = Column(Boolean, nullable=False, default=True)
    
    # Timezone for this chat (optional)
    timezone = Column(String(50), nullable=True, default="Asia/Phnom_Penh")
    
    def get_auto_close_times_list(self) -> List[str]:
        """Get auto close times as a list of time strings"""
        if not self.auto_close_times:
            return []
        try:
            return json.loads(self.auto_close_times)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_auto_close_times_list(self, times: List[str]) -> None:
        """Set auto close times from a list of time strings"""
        if times:
            self.auto_close_times = json.dumps(times)
        else:
            self.auto_close_times = None


class ShiftConfigurationService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def get_configuration(self, chat_id: int) -> Optional[ShiftConfiguration]:
        """Get shift configuration for a chat"""
        with self._get_db() as db:
            return db.query(ShiftConfiguration).filter(
                ShiftConfiguration.chat_id == chat_id
            ).first()

    async def get_or_create_configuration(self, chat_id: int) -> ShiftConfiguration:
        """Get configuration or create default one if not exists"""
        with self._get_db() as db:
            config = db.query(ShiftConfiguration).filter(
                ShiftConfiguration.chat_id == chat_id
            ).first()
            
            if not config:
                config = ShiftConfiguration(
                    chat_id=chat_id,
                    auto_close_enabled=False,
                    auto_close_times=None,
                    shift_name_prefix="Shift",
                    reset_numbering_daily=True,
                    timezone="Asia/Phnom_Penh"
                )
                db.add(config)
                db.commit()
                db.refresh(config)
            
            return config

    async def update_auto_close_settings(
        self, 
        chat_id: int, 
        enabled: bool, 
        auto_close_times: Optional[List[str]] = None
    ) -> ShiftConfiguration:
        """Update auto close settings for a chat"""
        with self._get_db() as db:
            config = await self.get_or_create_configuration(chat_id)
            
            # Refresh the object in this session
            config = db.merge(config)
            
            config.auto_close_enabled = enabled
            
            # Set multiple auto close times
            if auto_close_times:
                # Validate time formats and set the times
                validated_times = []
                for time_str in auto_close_times:
                    # Validate time format (HH:MM or HH:MM:SS)
                    try:
                        time_parts = time_str.split(":")
                        if len(time_parts) == 2:
                            time_parts.append("00")  # Add seconds if not provided
                        elif len(time_parts) != 3:
                            continue  # Skip invalid format
                        
                        # Validate ranges
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2])
                        
                        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                            validated_times.append(f"{hour:02d}:{minute:02d}:{second:02d}")
                    except (ValueError, IndexError):
                        continue  # Skip invalid times
                
                config.set_auto_close_times_list(validated_times)
            else:
                config.set_auto_close_times_list([])
            
            db.commit()
            db.refresh(config)
            return config

    async def update_shift_preferences(
        self,
        chat_id: int,
        shift_name_prefix: Optional[str] = None,
        reset_numbering_daily: Optional[bool] = None,
        timezone: Optional[str] = None
    ) -> ShiftConfiguration:
        """Update shift naming and numbering preferences"""
        with self._get_db() as db:
            config = await self.get_or_create_configuration(chat_id)
            
            # Refresh the object in this session
            config = db.merge(config)
            
            if shift_name_prefix is not None:
                config.shift_name_prefix = shift_name_prefix
            if reset_numbering_daily is not None:
                config.reset_numbering_daily = reset_numbering_daily
            if timezone is not None:
                config.timezone = timezone
                
            db.commit()
            db.refresh(config)
            return config

    async def get_chats_with_auto_close_enabled(self) -> list[ShiftConfiguration]:
        """Get all chats that have auto close enabled"""
        with self._get_db() as db:
            return db.query(ShiftConfiguration).filter(
                ShiftConfiguration.auto_close_enabled == True
            ).all()