from typing import List

from common.enums import FeatureFlags
from config import get_db_session
from helper import force_log
from models import ShiftPermission
from services.group_package_service import GroupPackageService


class ShiftPermissionService:
    """Service for managing shift close permissions"""
    
    def __init__(self):
        self.group_package_service = GroupPackageService()
    
    async def _ensure_group_package_exists(self, chat_id: int) -> bool:
        """Ensure that a group package exists for the chat"""
        package = await self.group_package_service.get_package_by_chat_id(chat_id)
        if not package:
            force_log(f"No group package found for chat {chat_id}", "WARNING")
            return False
        return True
    
    async def add_allowed_user(self, chat_id: int, username: str) -> bool:
        """Add a user to the allowed list for closing shifts"""
        force_log(f"🔥 ADD_ALLOWED_USER: Starting for chat_id={chat_id}, username={username}")
        try:
            # Remove @ from username if present
            username = username.lstrip('@').lower()
            force_log(f"🔥 ADD_ALLOWED_USER: Cleaned username={username}")
            
            with get_db_session() as db:
                # Check if permission already exists
                existing = (
                    db.query(ShiftPermission)
                    .filter(
                        ShiftPermission.chat_id == chat_id,
                        ShiftPermission.username == username
                    )
                    .first()
                )
                
                force_log(f"🔥 ADD_ALLOWED_USER: Existing permission check - found: {existing is not None}")
                
                if existing:
                    force_log(f"User @{username} already has close shift permission for chat {chat_id}")
                    return False
                
                # Add new permission
                force_log(f"🔥 ADD_ALLOWED_USER: Creating permission record")
                permission = ShiftPermission(
                    chat_id=chat_id,
                    username=username
                )
                db.add(permission)
                db.commit()
                force_log(f"🔥 ADD_ALLOWED_USER: Permission record created and committed")
                
                # Check if this is the first user - if so, enable the feature flag
                count = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .count()
                )
                force_log(f"🔥 ADD_ALLOWED_USER: Total user count for chat: {count}")
                
                if count == 1:
                    force_log(f"🔥 ADD_ALLOWED_USER: This is the first user - enabling feature flag")
                    # This is the first user, enable the feature flag
                    if await self._ensure_group_package_exists(chat_id):
                        force_log(f"🔥 ADD_ALLOWED_USER: Group package exists, setting feature flag")
                        try:
                            result = await self.group_package_service.set_feature_flag(
                                chat_id, FeatureFlags.SHIFT_PERMISSIONS.value, True
                            )
                            force_log(f"🔥 ADD_ALLOWED_USER: set_feature_flag result: {result}")
                            if result:
                                force_log(f"✅ Enabled SHIFT_PERMISSIONS feature for chat {chat_id} (first user added)")
                            else:
                                force_log(f"❌ Failed to enable SHIFT_PERMISSIONS feature for chat {chat_id}", "ERROR")
                        except Exception as e:
                            force_log(f"❌ Error enabling SHIFT_PERMISSIONS feature for chat {chat_id}: {e}", "ERROR")
                    else:
                        force_log(f"❌ No group package exists for chat {chat_id}", "ERROR")
                
                force_log(f"Added close shift permission for user @{username} in chat {chat_id}")
                return True
                
        except Exception as e:
            force_log(f"🔥❌ ADD_ALLOWED_USER: EXCEPTION - Error adding shift permission for user @{username} in chat {chat_id}: {e}", "ERROR")
            import traceback
            force_log(f"🔥❌ ADD_ALLOWED_USER: TRACEBACK - {traceback.format_exc()}", "ERROR")
            return False
    
    async def remove_allowed_user(self, chat_id: int, username: str) -> bool:
        """Remove a user from the allowed list"""
        try:
            # Remove @ from username if present
            username = username.lstrip('@').lower()
            
            with get_db_session() as db:
                permission = (
                    db.query(ShiftPermission)
                    .filter(
                        ShiftPermission.chat_id == chat_id,
                        ShiftPermission.username == username
                    )
                    .first()
                )
                
                if not permission:
                    force_log(f"User @{username} does not have close shift permission for chat {chat_id}")
                    return False
                
                db.delete(permission)
                db.commit()
                
                # Check if there are no more users - if so, disable the feature flag
                count = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .count()
                )
                
                if count == 0:
                    # No more users, disable the feature flag
                    try:
                        result = await self.group_package_service.set_feature_flag(
                            chat_id, FeatureFlags.SHIFT_PERMISSIONS.value, False
                        )
                        if result:
                            force_log(f"Disabled SHIFT_PERMISSIONS feature for chat {chat_id} (no users remaining)")
                        else:
                            force_log(f"Failed to disable SHIFT_PERMISSIONS feature for chat {chat_id} - no group package found", "ERROR")
                    except Exception as e:
                        force_log(f"Error disabling SHIFT_PERMISSIONS feature for chat {chat_id}: {e}", "ERROR")
                
                force_log(f"Removed close shift permission for user @{username} in chat {chat_id}")
                return True
                
        except Exception as e:
            force_log(f"Error removing shift permission for user @{username} in chat {chat_id}: {e}", "ERROR")
            return False
    
    async def is_user_allowed(self, chat_id: int, username: str) -> bool:
        """Check if a user is allowed to close shifts"""
        try:
            if not username:
                return False
                
            # Remove @ from username if present
            username = username.lstrip('@').lower()
            
            with get_db_session() as db:
                permission = (
                    db.query(ShiftPermission)
                    .filter(
                        ShiftPermission.chat_id == chat_id,
                        ShiftPermission.username == username
                    )
                    .first()
                )
                
                return permission is not None
                
        except Exception as e:
            force_log(f"Error checking shift permission for user @{username} in chat {chat_id}: {e}", "ERROR")
            return False
    
    async def get_allowed_users(self, chat_id: int) -> List[str]:
        """Get list of users allowed to close shifts"""
        try:
            with get_db_session() as db:
                permissions = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .all()
                )
                
                return [f"@{permission.username}" for permission in permissions]
                
        except Exception as e:
            force_log(f"Error getting allowed users for chat {chat_id}: {e}", "ERROR")
            return []
    
    async def clear_all_permissions(self, chat_id: int) -> int:
        """Clear all permissions for a chat"""
        try:
            with get_db_session() as db:
                count = (
                    db.query(ShiftPermission)
                    .filter(ShiftPermission.chat_id == chat_id)
                    .count()
                )
                
                db.query(ShiftPermission).filter(
                    ShiftPermission.chat_id == chat_id
                ).delete()
                db.commit()
                
                # Disable the feature flag since all users are removed
                if count > 0:
                    try:
                        result = await self.group_package_service.set_feature_flag(
                            chat_id, FeatureFlags.SHIFT_PERMISSIONS.value, False
                        )
                        if result:
                            force_log(f"Disabled SHIFT_PERMISSIONS feature for chat {chat_id} (all users cleared)")
                        else:
                            force_log(f"Failed to disable SHIFT_PERMISSIONS feature for chat {chat_id} - no group package found", "ERROR")
                    except Exception as e:
                        force_log(f"Error disabling SHIFT_PERMISSIONS feature for chat {chat_id}: {e}", "ERROR")
                
                force_log(f"Cleared {count} shift permissions for chat {chat_id}")
                return count
                
        except Exception as e:
            force_log(f"Error clearing permissions for chat {chat_id}: {e}", "ERROR")
            return 0