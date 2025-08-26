from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from helper.logger_utils import force_log
from models import Chat
from services.chat_service import ChatService
from services.group_package_service import GroupPackageService
from services.handlers.menu_handler import MenuHandler
from services.private_bot_group_binding_service import PrivateBotGroupBindingService

# Conversation state codes for private bot
START_MENU_CODE = 2000
BIND_GROUP_CODE = 2001
BIND_GROUP_SELECTION_CODE = 2002
BIND_GROUP_SEARCH_CODE = 2003
MENU_SELECTION_CODE = 2004
REPORT_CALLBACK_CODE = 2005


class TelegramPrivateBot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.app: Application | None = None
        self.binding_service = PrivateBotGroupBindingService()
        self.chat_service = ChatService()
        self.group_package_service = GroupPackageService()
        self.menu_handler = MenuHandler()
        
        force_log("TelegramPrivateBot initialized with token", "TelegramPrivateBot")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Check if user is authorized
        allowed_users = ["HK_688", "houhokheng", "autosum_kh"]
        username = update.effective_user.username if update.effective_user else None
        
        if not username or username not in allowed_users:
            await update.message.reply_text(
                "🚫 Access denied. Please contact the administrator for access. https://t.me/HK_688"
            )
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
            [InlineKeyboardButton("📋 List Groups", callback_data="start_list")],
            [InlineKeyboardButton("🔓 Unbind Group", callback_data="start_unbind")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Welcome! This bot helps you view reports from your linked transaction groups.\n\n"
            "Choose an option:",
            reply_markup=reply_markup
        )
        return START_MENU_CODE

    async def handle_start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle start menu button selections"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_bind":
            return await self._start_bind_flow(update, context)
        elif query.data == "start_list":
            return await self._start_list_flow(update, context)
        elif query.data == "start_menu":
            return await self._start_menu_flow(update, context)
        elif query.data == "start_unbind":
            return await self._start_unbind_flow(update, context)
        elif query.data == "close_conversation":
            await query.edit_message_text("Goodbye! Use /start anytime to access the bot.")
            return ConversationHandler.END
        elif query.data.startswith("unbind_") or query.data == "cancel":
            # Delegate unbind selections to the unbind handler
            return await self.handle_unbind_selection(update, context)
        
        return ConversationHandler.END

    async def _start_bind_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the bind flow from start menu"""
        query = update.callback_query
        context.user_data["command_type"] = "bind_group"
        
        # Show search options instead of loading all groups
        keyboard = [
            [InlineKeyboardButton("Use Chat ID", callback_data="use_chat_id")],
            [InlineKeyboardButton("Use Group Name", callback_data="use_group_name")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "How would you like to search for the group to bind?",
            reply_markup=reply_markup
        )
        return BIND_GROUP_CODE

    async def _start_list_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the list flow from start menu"""
        query = update.callback_query
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)
        
        if not bound_groups:
            keyboard = [[InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "You have no bound groups.\n\n"
                "Bind groups to view transaction reports.",
                reply_markup=reply_markup
            )
            return START_MENU_CODE
        
        # Build the list message
        message_lines = [f"📋 Your bound groups ({len(bound_groups)} total):"]
        message_lines.append("")
        
        for i, group in enumerate(bound_groups, 1):
            group_name = group.group_name or "Unnamed Group"
            group_id = group.chat_id
            
            # Get package info
            try:
                group_package = await self.group_package_service.get_package_by_chat_id(group.chat_id)
                package_name = group_package.package.value if group_package else "Unknown"
            except Exception:
                package_name = "Unknown"
            
            message_lines.append(f"{i}. **{group_name}**")
            message_lines.append(f"   • ID: `{group_id}`")
            message_lines.append(f"   • Package: {package_name}")
            message_lines.append("")
        
        keyboard = [
            [InlineKeyboardButton("🔓 Unbind Group", callback_data="start_unbind")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "\n".join(message_lines),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return START_MENU_CODE

    async def _start_menu_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the menu flow from start menu"""
        query = update.callback_query
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)
        
        if not bound_groups:
            keyboard = [
                [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "No groups are bound to this chat. Bind groups first.",
                reply_markup=reply_markup
            )
            return START_MENU_CODE
        
        # Store bound groups in context
        context.user_data["bound_groups"] = bound_groups
        
        if len(bound_groups) == 1:
            # Single group - show menu directly
            group = bound_groups[0]
            context.user_data["selected_group"] = group
            return await self._show_report_menu(update, group)
        else:
            # Multiple groups - let user select
            keyboard = []
            for group in bound_groups:
                keyboard.append([InlineKeyboardButton(
                    f"{group.group_name or 'Unnamed'} (ID: {group.chat_id})",
                    callback_data=f"select_{group.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select a group to view reports:",
                reply_markup=reply_markup
            )
            return MENU_SELECTION_CODE

    async def _start_unbind_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the unbind flow from start menu"""
        query = update.callback_query
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)
        
        if not bound_groups:
            keyboard = [
                [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "No groups are currently bound.",
                reply_markup=reply_markup
            )
            return START_MENU_CODE
        
        keyboard = []
        for group in bound_groups:
            keyboard.append([InlineKeyboardButton(
                f"Unbind {group.group_name or 'Unnamed'} (ID: {group.chat_id})",
                callback_data=f"unbind_{group.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Select a group to unbind:",
            reply_markup=reply_markup
        )
        return START_MENU_CODE


    async def handle_bind_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle search method selection for binding"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Binding cancelled.")
            return ConversationHandler.END
        
        if query.data == "use_chat_id":
            context.user_data["selection_type"] = "chat_id"
            await query.edit_message_text(
                "Please provide the chat ID or group name to search. You can search by exact chat ID or partial group name (up to 5 results will be shown)."
            )
            return BIND_GROUP_SEARCH_CODE
            
        elif query.data == "use_group_name":
            context.user_data["selection_type"] = "group_name"
            await query.edit_message_text(
                "Please provide the group name to search. You can enter partial group name (up to 5 results will be shown)."
            )
            return BIND_GROUP_SEARCH_CODE
        
        return ConversationHandler.END

    async def handle_bind_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group search input for binding"""
        try:
            search_term = update.message.text.strip()
            force_log(f"Searching for groups with term: {search_term}", "TelegramPrivateBot")
            
            # Search for chats using the chat service search method
            matching_chats = await self.chat_service.search_chats_by_chat_id_or_name(search_term, 5)
            
            if not matching_chats:
                await update.message.reply_text("No groups found matching your search.")
                return ConversationHandler.END
            
            if len(matching_chats) == 1:
                # If only one result, proceed directly with binding
                chat = matching_chats[0]
                return await self._bind_group_directly(update, context, chat)
            
            # Multiple results - show selection buttons
            keyboard = []
            for chat in matching_chats:
                button_text = f"{chat.group_name or 'Unnamed'} (ID: {chat.chat_id})"
                callback_data = f"bind_{chat.chat_id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Add cancel button
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Found {len(matching_chats)} matching groups. Please select one to bind:",
                reply_markup=reply_markup
            )
            
            return BIND_GROUP_SELECTION_CODE
            
        except Exception as e:
            force_log(f"Error in handle_bind_search: {e}", "TelegramPrivateBot")
            await update.message.reply_text("Error searching for groups.")
            return ConversationHandler.END

    async def handle_group_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group selection for binding"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Binding cancelled.")
            return ConversationHandler.END
        
        if query.data.startswith("bind_"):
            chat_id = int(query.data.split("_")[1])
            private_chat_id = update.effective_chat.id
            
            try:
                # Get group info first
                group = await self.chat_service.get_chat_by_chat_id(chat_id)
                if not group:
                    await query.edit_message_text("Selected group not found.")
                    return ConversationHandler.END
                
                # Bind the group (use the database id for binding)
                self.binding_service.bind_group(private_chat_id, group.id)
                
                group_name = group.group_name or f"Group {group.chat_id}"
                
                await query.edit_message_text(
                    f"Successfully bound to {group_name}!\n\n"
                    "You can now use /menu to view reports from this group."
                )
                
            except Exception as e:
                await query.edit_message_text(f"Error binding group: {str(e)}")
        
        return ConversationHandler.END

    async def _bind_group_directly(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat):
        """Bind a group directly when only one result is found"""
        try:
            private_chat_id = update.effective_chat.id
            
            # Bind the group
            self.binding_service.bind_group(private_chat_id, chat.id)
            
            group_name = chat.group_name or f"Group {chat.chat_id}"
            
            await update.message.reply_text(
                f"Successfully bound to {group_name}!\n\n"
                "You can now use /menu to view reports from this group."
            )
            
        except Exception as e:
            await update.message.reply_text(f"Error binding group: {str(e)}")
        
        return ConversationHandler.END


    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        private_chat_id = update.effective_chat.id
        bound_groups = self.binding_service.get_bound_groups(private_chat_id)
        
        if not bound_groups:
            await update.message.reply_text(
                "No groups are bound to this chat. Use /bind to link groups first."
            )
            return ConversationHandler.END
        
        # Store bound groups in context
        context.user_data["bound_groups"] = bound_groups
        
        if len(bound_groups) == 1:
            # Single group - show menu directly
            group = bound_groups[0]
            context.user_data["selected_group"] = group
            return await self._show_report_menu(update, group)
        else:
            # Multiple groups - let user select
            keyboard = []
            for group in bound_groups:
                keyboard.append([InlineKeyboardButton(
                    f"{group.group_name or 'Unnamed'} (ID: {group.chat_id})",
                    callback_data=f"select_{group.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Select a group to view reports:",
                reply_markup=reply_markup
            )
            return MENU_SELECTION_CODE

    async def _show_report_menu(self, update: Update, group: Chat):
        """Show report menu for a specific group"""
        # Get group package to determine available options
        group_package = await self.group_package_service.get_package_by_chat_id(group.chat_id)
        package_type = group_package.package if group_package else None
        
        keyboard = []

        if package_type and package_type.value == 'BUSINESS':
            keyboard.append([InlineKeyboardButton("តាមវេន", callback_data="shift_summary")])

        # Daily option - different callback based on package
        if package_type and package_type.value in ['TRIAL', 'STANDARD', 'BUSINESS']:
            keyboard.append([InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary")])
        else:
            # For FREE and BASIC packages, use current_date_summary
            keyboard.append([InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="current_date_summary")])
        
        # Package-based options
        if package_type and package_type.value in ['STANDARD', 'BUSINESS']:
            keyboard.append([InlineKeyboardButton("ប្រចាំសប្តាហ៍", callback_data="weekly_summary")])
            keyboard.append([InlineKeyboardButton("ប្រចាំខែ", callback_data="monthly_summary")])

        keyboard.append([InlineKeyboardButton("បិទ", callback_data="close_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        group_name = group.group_name or f"Group {group.chat_id}"
        text = f"Reports for {group_name}:\nPackage: {package_type.value if package_type else 'Unknown'}\n\nSelect report type:"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        
        return REPORT_CALLBACK_CODE

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group selection from menu"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Menu cancelled.")
            return ConversationHandler.END
        elif query.data == "close_conversation":
            await query.edit_message_text("Goodbye! Use /start anytime to access the bot.")
            return ConversationHandler.END
        
        bound_groups = context.user_data.get("bound_groups", [])
        
        if query.data.startswith("select_"):
            group_id = int(query.data.split("_")[1])
            group = next((g for g in bound_groups if g.id == group_id), None)
            
            if group:
                context.user_data["selected_group"] = group
                return await self._show_report_menu(update, group)
        
        return MENU_SELECTION_CODE

    async def handle_report_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle report generation callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "close_menu":
            await query.edit_message_text("Menu closed.")
            return ConversationHandler.END
        
        # Get the callback data to determine report type
        callback_data = query.data
        private_chat_id = update.effective_chat.id
        
        # Store necessary data for the menu handler
        # Single group report
        selected_group = context.user_data.get("selected_group")
        if selected_group:
            context.user_data["admin_chat_id"] = selected_group.chat_id
        
        # Create a pseudo-update object to interface with the menu handler
        class PseudoCallbackQuery:
            def __init__(self, original_query, callback_data):
                self.data = callback_data
                self.message = original_query.message
                self.from_user = original_query.from_user
                self.chat_instance = original_query.chat_instance
                self.id = original_query.id
                self._original_query = original_query
                
            async def answer(self, text=None, show_alert=False, url=None, cache_time=None):
                return await self._original_query.answer(text, show_alert, url, cache_time)
                
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                return await self._original_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

        class PseudoUpdate:
            def __init__(self, callback_query, callback_data):
                self.callback_query = PseudoCallbackQuery(callback_query, callback_data)
                self.effective_chat = callback_query.message.chat
                self.effective_user = callback_query.from_user

        # Create pseudo-update and call menu handler
        pseudo_update = PseudoUpdate(query, callback_data)
        
        try:
            result = await self.menu_handler.menu_callback_query_handler(pseudo_update, context)  # type: ignore
            # If the menu handler returns ConversationHandler.END, end our conversation too
            if result == ConversationHandler.END:
                return ConversationHandler.END
            # If it returns a callback query code (1008), continue in report callback state
            elif result == 1008:  # CALLBACK_QUERY_CODE from menu handler
                return REPORT_CALLBACK_CODE
            else:
                # For any other return value, continue in report callback state
                return REPORT_CALLBACK_CODE
        except Exception as e:
            await query.edit_message_text(f"Error generating report: {str(e)}")
            return ConversationHandler.END

    async def handle_unbind_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unbind selection from start menu"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            keyboard = [
                [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
                [InlineKeyboardButton("📋 List Groups", callback_data="start_list")],
                [InlineKeyboardButton("🔓 Unbind Group", callback_data="start_unbind")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Welcome! This bot helps you view reports from your linked transaction groups.\n\n"
                "Choose an option:",
                reply_markup=reply_markup
            )
            return START_MENU_CODE
        
        if query.data == "close_conversation":
            await query.edit_message_text("Goodbye! Use /start anytime to access the bot.")
            return ConversationHandler.END
        
        if query.data.startswith("unbind_"):
            group_id = int(query.data.split("_")[1])
            private_chat_id = update.effective_chat.id
            
            try:
                # Get bound groups to find the group info by database ID
                bound_groups = self.binding_service.get_bound_groups(private_chat_id)
                group = next((g for g in bound_groups if g.id == group_id), None)
                
                if not group:
                    await query.edit_message_text("Selected group not found.")
                    return ConversationHandler.END
                
                # Unbind the group
                self.binding_service.unbind_group(private_chat_id, group_id)
                
                group_name = group.group_name or f"Group {group.chat_id}"
                
                keyboard = [
                    [InlineKeyboardButton("🔗 Bind Group", callback_data="start_bind")],
                    [InlineKeyboardButton("📋 List Groups", callback_data="start_list")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="close_conversation")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"Successfully unbound from {group_name}!",
                    reply_markup=reply_markup
                )
                return START_MENU_CODE
                
            except Exception as e:
                await query.edit_message_text(f"Error unbinding group: {str(e)}")
                return ConversationHandler.END
        
        return START_MENU_CODE


    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel command"""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END

    async def send_message(self, chat_id: int, message: str) -> bool:
        """Send a message to a specific chat"""
        force_log(f"Private bot send_message called for chat_id: {chat_id}")
        try:
            if self.app and self.app.bot:
                force_log(f"Attempting to send message to private chat {chat_id}")
                await self.app.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
                force_log(f"Successfully sent message to private chat {chat_id}")
                return True
            else:
                force_log("Private bot application not initialized", "ERROR")
                return False
        except Exception as e:
            force_log(f"Error sending message to private chat {chat_id}: {e}", "ERROR")
            return False

    def setup(self):
        """Set up the bot handlers"""
        self.app = ApplicationBuilder().token(self.bot_token).build()

        # Main conversation handler that starts with /start
        main_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                START_MENU_CODE: [CallbackQueryHandler(self.handle_start_menu)],
                BIND_GROUP_CODE: [CallbackQueryHandler(self.handle_bind_selection)],
                BIND_GROUP_SEARCH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bind_search)],
                BIND_GROUP_SELECTION_CODE: [CallbackQueryHandler(self.handle_group_selection)],
                MENU_SELECTION_CODE: [CallbackQueryHandler(self.handle_menu_selection)],
                REPORT_CALLBACK_CODE: [CallbackQueryHandler(self.handle_report_callback)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
        )

        # Menu command handler (standalone)
        menu_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", self.menu_command)],
            states={
                MENU_SELECTION_CODE: [CallbackQueryHandler(self.handle_menu_selection)],
                REPORT_CALLBACK_CODE: [CallbackQueryHandler(self.handle_report_callback)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_chat=True,
            per_user=True,
        )

        # Add handlers
        self.app.add_handler(main_handler)
        self.app.add_handler(menu_handler)

        force_log("TelegramPrivateBot handlers set up", "TelegramPrivateBot")

    async def start_polling(self):
        """Start the bot polling"""
        if not self.app:
            self.setup()

        assert self.app is not None
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()  # type: ignore
        force_log("TelegramPrivateBot started polling", "TelegramPrivateBot")