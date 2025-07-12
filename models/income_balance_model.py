from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Generator, Any

from sqlalchemy import (
    Float,
    String,
    Column,
    Integer,
    DateTime,
    BigInteger,
    Text,
    func,
    ForeignKey,
)
from sqlalchemy.orm import Session, relationship

from config.database_config import SessionLocal
from helper import DateUtils
from helper.logger_utils import RotatingLogger
from models.base_model import BaseModel


def force_log(message):
    """Write logs with hourly rotation"""
    RotatingLogger.log(message, "IncomeService")


class CurrencyEnum(Enum):
    KHR = "៛"
    USD = "$"

    @classmethod
    def from_symbol(cls, symbol: str) -> Optional[str]:
        for member in cls:
            if member.value == symbol:
                return member.name
        return None


class IncomeBalance(BaseModel):
    __tablename__ = "income_balance"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    currency = Column(String(16), nullable=False)
    original_amount = Column(Float, nullable=False)
    income_date = Column(DateTime, default=lambda: DateUtils.now, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    # New shift reference
    shift_id = Column(Integer, ForeignKey('shifts.id'), nullable=True)
    shift = relationship("Shift", back_populates="income_records")


    trx_id = Column(String(50), nullable=True)


class IncomeService:
    def __init__(self):
        self._session_factory = SessionLocal

    @contextmanager
    def _get_db(self) -> Generator[Session, Any, Any]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    async def _ensure_active_shift(self, chat_id: int) -> int:
        """Ensure there's an active shift for the chat, create one if needed"""
        force_log(f"_ensure_active_shift called for chat_id: {chat_id}")
        try:
            from models.shift_model import ShiftService
            
            shift_service = ShiftService()
            current_shift = await shift_service.get_current_shift(chat_id)
            
            if current_shift:
                force_log(f"Found existing shift {current_shift.id} for chat {chat_id}")
                return current_shift.id
            else:
                # No active shift found, create a new one
                force_log(f"No active shift found, creating new one for chat {chat_id}")
                new_shift = await shift_service.create_shift(chat_id)
                force_log(f"Created new shift {new_shift.id} for chat {chat_id}")
                return new_shift.id
        except Exception as e:
            force_log(f"ERROR in _ensure_active_shift: {e}")
            raise e


    async def update_shift(self, income_id: int, shift: int):
        with self._get_db() as db:
            income = db.query(IncomeBalance).filter(IncomeBalance.id == income_id)
            if income.first():
                income.update({"shift": shift, "shift_closed": True})
                db.commit()
                return income.first()
            return None

    async def get_last_shift_id(self, chat_id: int) -> type[IncomeBalance] | None:
        with self._get_db() as db:
            last_income = (
                db.query(IncomeBalance)
                .filter(IncomeBalance.chat_id == chat_id)
                .order_by(IncomeBalance.id.desc())
                .first()
            )
            return last_income

    async def insert_income(
            self,
            chat_id: int,
            amount: float,
            currency: str,
            original_amount: float,
            message_id: int,
            message: str,
            trx_id: str | None,
            shift_id: int = None,
            enable_shift: bool = False
    ) -> IncomeBalance:
        force_log(f"insert_income called: chat_id={chat_id}, amount={amount}, currency={currency}, shift_id={shift_id}")
        try:
            from_symbol = CurrencyEnum.from_symbol(currency)
            currency_code = from_symbol if from_symbol else currency
            current_date = DateUtils.now()

            # Ensure shift exists - auto-create if needed
            if shift_id is None:
                if enable_shift:
                    force_log(f"No shift_id provided, ensuring active shift for chat {chat_id}")
                    shift_id = await self._ensure_active_shift(chat_id)
                    force_log(f"Using shift_id: {shift_id}")
                else:
                    force_log(f"Shifts disabled for chat {chat_id}, setting shift_id to None")
                    shift_id = None

            with self._get_db() as db:
                try:
                    force_log(f"Creating IncomeBalance record with shift_id={shift_id}")
                    new_income = IncomeBalance(
                        chat_id=chat_id,
                        amount=amount,
                        currency=currency_code,
                        income_date=current_date,
                        original_amount=original_amount,
                        message_id=message_id,
                        message=message,
                        trx_id=trx_id,
                        shift_id=shift_id,
                    )

                    db.add(new_income)
                    db.commit()
                    db.refresh(new_income)
                    force_log(f"Successfully saved IncomeBalance record with id={new_income.id}")
                    return new_income

                except Exception as e:
                    force_log(f"ERROR in database operation: {e}")
                    db.rollback()
                    raise e
        except Exception as e:
            force_log(f"ERROR in insert_income: {e}")
            raise e

    async def get_income(self, income_id: int) -> Optional[IncomeBalance]:
        with self._get_db() as db:
            return db.query(IncomeBalance).filter(IncomeBalance.id == income_id).first()

    async def get_income_by_chat_id(self, chat_id: int) -> list[type[IncomeBalance]]:
        with self._get_db() as db:
            return (
                db.query(IncomeBalance).filter(IncomeBalance.chat_id == chat_id).all()
            )

    async def get_income_by_chat_and_message_id(self, chat_id: int, message_id: int) -> bool:
        force_log(f"Searching for existing income with chat_id: {chat_id} and message_id: {message_id}")
        with self._get_db() as db:
            result = db.query(IncomeBalance).filter(
                IncomeBalance.chat_id == chat_id,
                IncomeBalance.message_id == message_id
            ).first()
            found = result is not None
            force_log(f"Chat ID {chat_id} + Message ID {message_id} duplicate check: {'FOUND' if found else 'NOT FOUND'}")
            return found

    async def get_income_by_trx_id(self, trx_id: str | None, chat_id: int) -> bool:
        if trx_id is None:
            force_log(f"Transaction ID is None, returning False")
            return False
        force_log(f"Searching for existing income with trx_id: {trx_id} and chat_id: {chat_id}")
        with self._get_db() as db:
            result = db.query(IncomeBalance).filter(
                IncomeBalance.trx_id == trx_id, 
                IncomeBalance.chat_id == chat_id
            ).first()
            found = result is not None
            force_log(f"Transaction ID {trx_id} duplicate check for chat {chat_id}: {'FOUND' if found else 'NOT FOUND'}")
            return found

    async def check_duplicate_transaction(self, chat_id: int, trx_id: str | None, message_id: int) -> bool:
        """
        Check for duplicate transaction using combination of chat_id, trx_id, and message_id
        - If trx_id exists: check (chat_id, trx_id, message_id)
        - If trx_id is null: check (chat_id, message_id)
        Returns True if duplicate found, False if unique
        """
        force_log(f"Checking duplicate with chat_id: {chat_id}, trx_id: {trx_id}, message_id: {message_id}")
        
        with self._get_db() as db:
            if trx_id:
                # Check combination of chat_id, trx_id, and message_id
                duplicate = db.query(IncomeBalance).filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.trx_id == trx_id,
                    IncomeBalance.message_id == message_id
                ).first()
                
                if duplicate:
                    force_log(f"Duplicate found by combination: chat_id={chat_id}, trx_id={trx_id}, message_id={message_id}")
                    return True
            else:
                # If trx_id is null, check combination of chat_id and message_id
                duplicate = db.query(IncomeBalance).filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.message_id == message_id
                ).first()
                
                if duplicate:
                    force_log(f"Duplicate found by combination: chat_id={chat_id}, message_id={message_id} (trx_id is null)")
                    return True
            
            force_log(f"No duplicate found for chat_id={chat_id}, trx_id={trx_id}, message_id={message_id}")
            return False

    async def get_last_yesterday_message(
            self, date: datetime
    ) -> Optional[IncomeBalance]:
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(func.date(IncomeBalance.income_date) == date.date())
                .order_by(IncomeBalance.id.desc())
                .first()
            )

    async def get_income_by_date_and_chat_id(
            self, chat_id: int, start_date: datetime, end_date: datetime
    ) -> list[type[IncomeBalance]]:
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= start_date,
                    IncomeBalance.income_date < end_date,
                )
                .all()
            )

    async def get_income_by_shift_id(self, shift_id: int) -> list[type[IncomeBalance]]:
        """Get all income records for a specific shift"""
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(IncomeBalance.shift_id == shift_id)
                .all()
            )


    async def get_income_summary_by_date_range(
            self, chat_id: int, start_date: str, end_date: str
    ) -> dict:
        """
        Get income summary statistics for a date range
        Returns a dictionary with total, count, and breakdown by currency
        """
        # Convert string dates to datetime objects
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        # Add one day to end_date to include the entire end day
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        # Get all income records in the date range
        with self._get_db() as db:
            incomes = (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= start_datetime,
                    IncomeBalance.income_date < end_datetime
                )
                .all()
            )

        # Prepare the summary structure
        summary = {
            "total_amount": 0.0,
            "count": len(incomes),
            "by_currency": {}
        }

        # Calculate totals
        for income in incomes:
            currency = income.currency
            amount = income.amount

            # Initialize currency entry if it doesn't exist
            if currency not in summary["by_currency"]:
                summary["by_currency"][currency] = {
                    "total": 0.0,
                    "count": 0
                }

            # Add to totals
            summary["by_currency"][currency]["total"] += amount
            summary["by_currency"][currency]["count"] += 1
            summary["total_amount"] += amount

        return summary

    async def get_today_income(self, chat_id: int) -> list[type[IncomeBalance]]:
        """Get all income records for today"""
        today = DateUtils.today()
        tomorrow = today + timedelta(days=1)
        
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= today,
                    IncomeBalance.income_date < tomorrow
                )
                .all()
            )

    async def get_weekly_income(self, chat_id: int) -> list[type[IncomeBalance]]:
        """Get all income records for this week"""
        today = DateUtils.today()
        week_start = today - timedelta(days=today.weekday())
        
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= week_start
                )
                .all()
            )

    async def get_monthly_income(self, chat_id: int) -> list[type[IncomeBalance]]:
        """Get all income records for this month"""
        today = DateUtils.today()
        month_start = today.replace(day=1)
        
        with self._get_db() as db:
            return (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.chat_id == chat_id,
                    IncomeBalance.income_date >= month_start
                )
                .all()
            )
