import asyncio
from datetime import date

from sqlalchemy import func

from config import get_db_session
from helper import force_log, DateUtils
from models import Shift


class ShiftService:
    def __init__(self):
        # Lock to prevent race conditions when closing shifts
        self._close_shift_locks = {}
    async def create_shift(self, chat_id: int) -> Shift:
        """Create a new shift starting now"""
        current_time = DateUtils.now()

        with get_db_session() as db:
            # Get the highest shift number for this chat for today (not global)
            last_shift_number = (
                db.query(func.max(Shift.number))
                .filter(
                    Shift.chat_id == chat_id,
                    Shift.shift_date == current_time.date(),
                )
                .scalar()
                or 0
            )

            new_shift = Shift(
                chat_id=chat_id,
                shift_date=current_time.date(),
                number=last_shift_number + 1,
                start_time=current_time,
                is_closed=False,
            )

            db.add(new_shift)
            db.commit()
            db.refresh(new_shift)
            return new_shift

    async def get_current_shift(self, chat_id: int) -> Shift | None:
        """Get the current open shift (regardless of date)"""
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.is_closed == False)
                .order_by(Shift.start_time.desc())
                .first()
            )

    async def get_shift_by_id(self, shift_id: int) -> Shift | None:
        with get_db_session() as db:
            return db.query(Shift).filter(Shift.id == shift_id).first()

    async def close_shift(self, shift_id: int) -> Shift | None:
        """Close a shift by setting end_time and is_closed"""
        current_time = DateUtils.now()
        force_log(f"CLOSE_SHIFT: Attempting to close shift_id {shift_id} at {current_time}")

        # Get or create a lock for this specific shift_id
        if shift_id not in self._close_shift_locks:
            self._close_shift_locks[shift_id] = asyncio.Lock()
        
        lock = self._close_shift_locks[shift_id]
        
        async with lock:
            force_log(f"CLOSE_SHIFT: Acquired lock for shift_id {shift_id}")
            
            with get_db_session() as db:
                shift = db.query(Shift).filter(Shift.id == shift_id).first()
                if not shift:
                    force_log(f"CLOSE_SHIFT: Shift {shift_id} not found")
                    return None
                    
                if shift.is_closed:
                    force_log(f"CLOSE_SHIFT: Shift {shift_id} is already closed at {shift.end_time}")
                    return shift  # Return the already closed shift
                    
                # Double-check it's still open (race condition protection)
                if shift.end_time is not None:
                    force_log(f"CLOSE_SHIFT: Shift {shift_id} already has end_time {shift.end_time}, marking as closed")
                    shift.is_closed = True
                    db.commit()
                    db.refresh(shift)
                    return shift
                    
                force_log(f"CLOSE_SHIFT: Successfully closing shift {shift_id} (was open since {shift.start_time})")
                shift.end_time = current_time
                shift.is_closed = True
                db.commit()
                db.refresh(shift)
                
                # Clean up the lock after successful close to prevent memory leaks
                if shift_id in self._close_shift_locks:
                    del self._close_shift_locks[shift_id]
                
                return shift

    async def get_shifts_by_date_range(
        self, chat_id: int, start_date: date, end_date: date
    ) -> list[Shift]:
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(
                    Shift.chat_id == chat_id,
                    Shift.shift_date >= start_date,
                    Shift.shift_date <= end_date,
                )
                .order_by(Shift.shift_date, Shift.number)
                .all()
            )

    async def get_shifts_by_date(self, chat_id: int, shift_date: date) -> list[Shift]:
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id, Shift.shift_date == shift_date)
                .order_by(Shift.number)
                .all()
            )

    async def get_shifts_by_start_date(self, chat_id: int, start_date: date) -> list[Shift]:
        """Get shifts that started on a specific date (for admin bot)"""
        with get_db_session() as db:
            from sqlalchemy import func
            
            return (
                db.query(Shift)
                .filter(
                    Shift.chat_id == chat_id,
                    func.date(Shift.start_time) == start_date
                )
                .order_by(Shift.id)
                .all()
            )

    async def get_recent_closed_shifts(
        self, chat_id: int, limit: int = 1
    ) -> list[Shift]:
        with get_db_session() as db:
            return (
                db.query(Shift)
                .filter(Shift.chat_id == chat_id)
                .order_by(Shift.end_time.desc(), Shift.number.desc())
                .limit(limit)
                .all()
            )

    async def get_shift_income_summary(self, shift_id: int, chat_id: int) -> dict:
        """Get income summary for a specific shift and chat"""
        with get_db_session() as db:
            from models.income_balance_model import IncomeBalance

            # Get all income records for this shift and chat
            income_records = (
                db.query(IncomeBalance)
                .filter(
                    IncomeBalance.shift_id == shift_id, IncomeBalance.chat_id == chat_id
                )
                .all()
            )

            if not income_records:
                return {"total_amount": 0.0, "transaction_count": 0, "currencies": {}}

            total_amount = sum(record.amount for record in income_records)
            transaction_count = len(income_records)

            # Group by currency
            currencies = {}
            for record in income_records:
                currency = record.currency or "USD"
                if currency not in currencies:
                    currencies[currency] = {"amount": 0.0, "count": 0}
                currencies[currency]["amount"] += record.amount
                currencies[currency]["count"] += 1

            return {
                "total_amount": total_amount,
                "transaction_count": transaction_count,
                "currencies": currencies,
            }

    async def get_recent_dates_with_shifts(
        self, chat_id: int, days: int = 3
    ) -> list[date]:
        """Get last N dates that have shifts"""
        with get_db_session() as db:
            dates = (
                db.query(Shift.shift_date)
                .filter(Shift.chat_id == chat_id)
                .distinct()
                .order_by(Shift.shift_date.desc())
                .limit(days)
                .all()
            )

            return [d[0] for d in dates]

    async def get_recent_start_dates_with_shifts(
        self, chat_id: int, days: int = 3
    ) -> list[date]:
        """Get last N dates based on shift start dates (for admin bot)"""
        with get_db_session() as db:
            from sqlalchemy import func
            
            dates = (
                db.query(func.date(Shift.start_time))
                .filter(Shift.chat_id == chat_id)
                .distinct()
                .order_by(func.date(Shift.start_time).desc())
                .limit(days)
                .all()
            )

            return [d[0] for d in dates]

    async def get_all_start_dates_with_shifts_in_month(
        self, chat_id: int, year: int, month: int
    ) -> list[date]:
        """Get all dates with shifts in a specific month"""
        with get_db_session() as db:
            from sqlalchemy import func, and_
            from datetime import datetime
            
            # Create start and end of month
            start_of_month = datetime(year, month, 1)
            if month == 12:
                end_of_month = datetime(year + 1, 1, 1)
            else:
                end_of_month = datetime(year, month + 1, 1)
            
            dates = (
                db.query(func.date(Shift.start_time))
                .filter(
                    and_(
                        Shift.chat_id == chat_id,
                        Shift.start_time >= start_of_month,
                        Shift.start_time < end_of_month
                    )
                )
                .distinct()
                .order_by(func.date(Shift.start_time).desc())
                .all()
            )

            return [d[0] for d in dates]

    async def check_and_auto_close_shifts(self) -> list[dict]:
        """Check all open shifts and auto-close them based on configuration"""
        from models.shift_configuration_model import ShiftConfigurationService
        from datetime import datetime

        closed_shifts = []
        closed_shift_info = []
        config_service = ShiftConfigurationService()
        current_time = DateUtils.now()

        # Track which chats we've processed to update their last_job_run
        processed_chats = set()

        with get_db_session() as db:
            # Get all open shifts
            open_shifts = db.query(Shift).filter(Shift.is_closed == False).all()

            for shift in open_shifts:
                # Skip if we've already processed this chat in this run
                if shift.chat_id in processed_chats:
                    continue

                config = await config_service.get_configuration(shift.chat_id)
                if not config or not config.auto_close_enabled:
                    continue

                # Check if job already ran for this minute for this chat
                if config.last_job_run:
                    # Ensure both datetimes have the same timezone awareness
                    last_job_run = config.last_job_run
                    if last_job_run.tzinfo is None:
                        # If last_job_run is naive, make it timezone-aware
                        last_job_run = DateUtils.localize_datetime(last_job_run)

                    # If last job run is within the same minute, skip
                    if last_job_run.replace(
                        second=0, microsecond=0
                    ) >= current_time.replace(second=0, microsecond=0):
                        continue

                # Mark this chat as processed immediately to prevent duplicates
                processed_chats.add(shift.chat_id)

                # Update last_job_run immediately to prevent race conditions
                from models.shift_configuration_model import ShiftConfiguration

                db_config = (
                    db.query(ShiftConfiguration)
                    .filter(ShiftConfiguration.chat_id == shift.chat_id)
                    .first()
                )
                if db_config:
                    db_config.last_job_run = current_time
                    db.commit()

                should_close = False

                # Check time-based auto close with multiple times
                auto_close_times = config.get_auto_close_times_list()
                if auto_close_times:
                    for time_str in auto_close_times:
                        try:
                            # Parse time string (HH:MM format)
                            time_parts = time_str.split(":")
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])

                            # Convert to datetime for comparison
                            from datetime import time

                            close_time = datetime.combine(
                                current_time.date(), time(hour, minute)
                            )
                            # Make timezone aware
                            close_time = DateUtils.localize_datetime(close_time)

                            # If current time is past the auto-close time and shift started before it
                            shift_start = DateUtils.localize_datetime(shift.start_time)
                            if current_time >= close_time and shift_start < close_time:
                                should_close = True
                                break  # Exit loop once we find a matching close time
                        except (ValueError, IndexError):
                            continue  # Skip invalid time formats

                # Close the shift if needed
                if should_close:
                    shift.end_time = current_time
                    shift.is_closed = True
                    closed_shifts.append(shift)
                    # Collect info while still in session
                    closed_shift_info.append(
                        {
                            "id": shift.id,
                            "chat_id": shift.chat_id,
                            "number": shift.number,
                        }
                    )

            if closed_shifts:
                db.commit()
                for shift in closed_shifts:
                    db.refresh(shift)

                # Create new shifts for each closed shift (same as manual close behavior)
                for i, closed_shift in enumerate(closed_shifts):
                    try:
                        # Get the highest shift number for this chat for today (same logic as create_shift)
                        last_shift_number = (
                            db.query(func.max(Shift.number))
                            .filter(
                                Shift.chat_id == closed_shift.chat_id,
                                Shift.shift_date == current_time.date(),
                            )
                            .scalar()
                            or 0
                        )

                        # Create a new shift for this chat
                        new_shift = Shift(
                            chat_id=closed_shift.chat_id,
                            shift_date=current_time.date(),
                            number=last_shift_number + 1,
                            start_time=current_time,
                            is_closed=False,
                        )
                        db.add(new_shift)
                        force_log(
                            f"Auto-created new shift #{new_shift.number} for chat {closed_shift.chat_id} after closing shift #{closed_shift.number}"
                        )
                    except Exception as e:
                        force_log(
                            f"Error creating new shift after auto-close for chat {closed_shift.chat_id}: {e}",
                            "ERROR",
                        )

                # Commit the new shifts
                db.commit()

        return closed_shift_info

    async def auto_close_shift_for_chat(self, chat_id: int) -> Shift | None:
        """Auto close the current shift for a specific chat based on its configuration"""
        from models.shift_configuration_model import ShiftConfigurationService
        from datetime import datetime

        config_service = ShiftConfigurationService()
        config = await config_service.get_configuration(chat_id)

        if not config or not config.auto_close_enabled:
            return None

        current_shift = await self.get_current_shift(chat_id)
        if not current_shift:
            return None

        should_close = False
        current_time = DateUtils.now()

        # Check time-based auto close with multiple times
        auto_close_times = config.get_auto_close_times_list()
        if auto_close_times:
            for time_str in auto_close_times:
                try:
                    # Parse time string (HH:MM format)
                    time_parts = time_str.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])

                    # Convert to datetime for comparison
                    from datetime import time

                    close_time = datetime.combine(
                        current_time.date(), time(hour, minute)
                    )
                    close_time = DateUtils.localize_datetime(close_time)

                    shift_start = DateUtils.localize_datetime(current_shift.start_time)
                    if current_time >= close_time and shift_start < close_time:
                        should_close = True
                        break  # Exit loop once we find a matching close time
                except (ValueError, IndexError):
                    force_log(f"fail to parse time:{time_str}", "shift_model")
                    continue  # Skip invalid time formats

        if should_close:
            return await self.close_shift(current_shift.id)

        return None
