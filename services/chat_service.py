from config import get_db_session
from helper.logger_utils import force_log
from models import Chat
from models import User, IncomeBalance
from .group_package_service import GroupPackageService
from .income_balance_service import IncomeService
from .shift_service import ShiftService


class ChatService:
    def __init__(self):
        self.income_service = IncomeService()
        self.shift_service = ShiftService()
        self.group_package_service = GroupPackageService()

    @staticmethod
    async def register_chat_id(chat_id, group_name, user: User | None, registered_by: str | None = None):
        with get_db_session() as session:
            try:
                new_chat = Chat(
                    chat_id=chat_id,
                    group_name=group_name,
                    user_id=user.id if user else None,
                    registered_by=registered_by,
                )
                session.add(new_chat)
                session.commit()
                return True, f"Chat ID {chat_id} registered successfully."
            except Exception as e:
                session.rollback()
                force_log(f"Error registering chat ID: {e}")
                return False, f"Error registering chat ID: {e}"
            finally:
                session.close()

    async def update_chat_enable_shift(self, chat_id: int, enable_shift: bool):
        with get_db_session() as session:
            try:
                # Create a shift first if enabling shift
                if enable_shift:
                    try:
                        # Only create shift if none exists
                        current_shift = await self.shift_service.get_current_shift(
                            chat_id
                        )
                        if not current_shift:
                            await self.shift_service.create_shift(chat_id)

                    except Exception as shift_error:
                        force_log(f"Error creating shift: {shift_error}")
                        raise shift_error

                # Update the chat setting after shift creation succeeds
                session.query(Chat).filter_by(chat_id=chat_id).update(
                    {"enable_shift": enable_shift}
                )
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                force_log(f"Error updating chat enable_shift: {e}")
                return False
            finally:
                session.close()

    @staticmethod
    async def update_chat_status(chat_id: int, status: bool):
        with get_db_session() as session:
            try:
                session.query(Chat).filter_by(chat_id=chat_id).update(
                    {"is_active": status}
                )
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                force_log(f"Error updating chat status: {e}")
                return False
            finally:
                session.close()

    @staticmethod
    async def update_chat_user_id(chat_id: int, user_id: int):
        with get_db_session() as session:
            try:
                session.query(Chat).filter_by(chat_id=chat_id).update(
                    {"user_id": user_id}
                )
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                force_log(f"Error updating chat user_id: {e}")
                return False
            finally:
                session.close()

    @staticmethod
    async def get_chat_by_chat_id(chat_id: int) -> Chat | None:
        with get_db_session() as session:
            try:
                chat = (
                    session.query(Chat)
                    .filter_by(chat_id=chat_id)
                    .first()
                )
                return chat
            except Exception as e:
                force_log(f"Error fetching chat by chat ID: {e}")
                return None
            finally:
                session.close()

    @staticmethod
    async def get_chat_thresholds(chat_id: int) -> dict | None:
        """Get USD and KHR thresholds for a chat"""
        with get_db_session() as session:
            try:
                chat = (
                    session.query(Chat.usd_threshold, Chat.khr_threshold)
                    .filter_by(chat_id=chat_id)
                    .first()
                )
                if chat:
                    return {
                        "usd_threshold": float(chat.usd_threshold) if chat.usd_threshold is not None else None,
                        "khr_threshold": float(chat.khr_threshold) if chat.khr_threshold is not None else None
                    }
                return None
            except Exception as e:
                force_log(f"Error fetching chat thresholds: {e}")
                return None
            finally:
                session.close()


    @staticmethod
    async def search_chats_by_chat_id_or_name(search_term: str, limit: int = 5) -> list[Chat]:
        """Search chats by chat_id or group_name, return up to 'limit' results"""
        with get_db_session() as session:
            try:
                # Try to convert search_term to int for chat_id search
                try:
                    chat_id_search = int(search_term)
                    # Search by exact chat_id match first
                    exact_match = (
                        session.query(Chat)
                        # .options(joinedload(Chat.user))
                        .filter_by(chat_id=chat_id_search)
                        .first()
                    )
                    if exact_match:
                        return [exact_match]
                except ValueError:
                    # Not a valid integer, skip chat_id search
                    pass
                
                # Search by group_name (partial match, case insensitive)
                results = (
                    session.query(Chat)
                    # .options(joinedload(Chat.user))
                    .filter(Chat.group_name.ilike(f"%{search_term}%"))
                    .limit(limit)
                    .all()
                )
                return results
            except Exception as e:
                force_log(f"Error searching chats: {e}")
                return []
            finally:
                session.close()

    @staticmethod
    async def get_all_active_chat_ids():
        with get_db_session() as session:
            try:
                chats = session.query(Chat.chat_id).filter_by(is_active=True).all()
                return [int(c[0]) for c in chats]
            except Exception as e:
                force_log(f"Error fetching chat IDs: {e}")
                return []
            finally:
                session.close()

    @staticmethod
    async def get_all_active_chat_ids_excluding_free():
        """Get all active chat IDs excluding those with FREE packages"""
        from models.group_package_model import GroupPackage
        from common.enums import ServicePackage
        
        with get_db_session() as session:
            try:
                # Join Chat with GroupPackage and filter out FREE package
                chats = (
                    session.query(Chat.chat_id)
                    .join(GroupPackage, Chat.id == GroupPackage.chat_group_id)
                    .filter(Chat.is_active == True)
                    .filter(GroupPackage.package != ServicePackage.FREE)
                    .all()
                )
                return [int(c[0]) for c in chats]
            except Exception as e:
                force_log(f"Error fetching non-free chat IDs: {e}")
                return []
            finally:
                session.close()

    @staticmethod
    async def get_active_chat_ids_by_registered_by(registered_by: str | None):
        """Get active chat IDs excluding FREE packages, filtered by registered_by field.
        
        Args:
            registered_by: Phone number to filter by, or None to get chats with NULL registered_by
        """
        from models.group_package_model import GroupPackage
        from common.enums import ServicePackage
        
        with get_db_session() as session:
            try:
                query = (
                    session.query(Chat.chat_id)
                    .join(GroupPackage, Chat.id == GroupPackage.chat_group_id)
                    .filter(Chat.is_active == True)
                    .filter(GroupPackage.package != ServicePackage.FREE)
                )
                
                if registered_by is None:
                    # Get chats with NULL or empty registered_by (for main client)
                    query = query.filter(
                        (Chat.registered_by.is_(None)) | (Chat.registered_by == '')
                    )
                else:
                    # Get chats with specific registered_by phone number
                    query = query.filter(Chat.registered_by == registered_by)
                
                chats = query.all()
                return [int(c[0]) for c in chats]
            except Exception as e:
                force_log(f"Error fetching chat IDs by registered_by='{registered_by}': {e}")
                return []
            finally:
                session.close()

    @staticmethod
    async def chat_exists(chat_id: int) -> bool:
        """
        Check if a chat with the given chat_id exists.
        Much more efficient than fetching all chat IDs and checking if it's in the list.
        """
        with get_db_session() as session:
            try:
                exists = (
                    session.query(Chat).filter_by(chat_id=chat_id).first() is not None
                )
                return bool(exists)
            except Exception as e:
                force_log(f"Error checking if chat exists: {e}")
                return False
            finally:
                session.close()

    async def is_shift_enabled(self, chat_id: int) -> bool:
        try:
            chat = await self.get_chat_by_chat_id(chat_id)
            return chat.enable_shift if chat else False
        except Exception as e:
            force_log(f"Error checking shift enabled: {e}")
            return False

    @staticmethod
    async def update_chat_threshold(chat_id: int, threshold_type: str, value: float) -> bool:
        """Update threshold value (USD or KHR) for a chat"""
        with get_db_session() as session:
            try:
                update_data = {}
                if threshold_type.lower() == "usd":
                    update_data["usd_threshold"] = value
                elif threshold_type.lower() == "khr":
                    update_data["khr_threshold"] = value
                else:
                    force_log(f"Invalid threshold type: {threshold_type}")
                    return False
                
                result = (
                    session.query(Chat)
                    .filter_by(chat_id=chat_id)
                    .update(update_data)
                )
                
                session.commit()
                if result > 0:
                    force_log(f"Successfully updated {threshold_type} threshold to {value} for chat {chat_id}")
                    return True
                else:
                    force_log(f"No chat found with chat_id {chat_id}")
                    return False
            except Exception as e:
                session.rollback()
                force_log(f"Error updating {threshold_type} threshold: {e}")
                return False
            finally:
                session.close()

    @staticmethod
    async def migrate_chat_id(old_chat_id: int, new_chat_id: int) -> bool:
        """Migrate chat_id from old to new (for group migrations)"""
        with get_db_session() as session:
            try:
                chat_result = (
                    session.query(Chat)
                    .filter_by(chat_id=old_chat_id)
                    .update({"chat_id": new_chat_id})
                )

                income_result = (
                    session.query(IncomeBalance)
                    .filter_by(chat_id=old_chat_id)
                    .update({"chat_id": new_chat_id})
                )

                session.commit()
                if chat_result > 0 or income_result > 0:
                    force_log(
                        f"Successfully migrated chat_id from {old_chat_id} to {new_chat_id}"
                    )
                    force_log(
                        f"Updated {chat_result} chat records and {income_result} income_balance records"
                    )
                    return True
                else:
                    force_log(f"No records found with chat_id {old_chat_id}")
                    return False
            except Exception as e:
                session.rollback()
                force_log(f"Error migrating chat_id: {e}")
                return False
            finally:
                session.close()
