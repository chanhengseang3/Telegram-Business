from calendar import monthrange
from datetime import timedelta, datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from helper import DateUtils, daily_transaction_report, weekly_transaction_report, monthly_transaction_report, \
    shift_report
from helper.logger_utils import force_log
from services import ChatService, IncomeService, ShiftService, GroupPackageService


class MenuHandler:
    def __init__(self):
        self.chat_service = ChatService()

    async def _handle_daily_summary_menu(self, chat_id: int, query):
        """Handle daily summary by showing date selection menu like normal bot"""
        try:
            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            if not chat:
                await query.edit_message_text(f"Chat {chat_id} not found.")
                return False

            today = DateUtils.now()
            keyboard = []

            # Show 3 days for non-shift chats
            for i in range(2, -1, -1):
                day = today - timedelta(days=i)
                label = day.strftime("%b %d")
                callback_value = day.strftime("%Y-%m-%d")
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            label, callback_data=f"summary_of_{callback_value}"
                        )
                    ]
                )

            keyboard.append(
                [InlineKeyboardButton("ថ្ងៃផ្សេងទៀត", callback_data="other_dates")]
            )
            keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("ឆែករបាយការណ៍ថ្ងៃ:", reply_markup=reply_markup)
            return True

        except Exception as e:
            force_log(f"Error in _handle_daily_summary_menu: {e}", "MenuHandler")
            await query.edit_message_text(f"Error showing daily menu: {str(e)}")
            return False

    async def _handle_current_date_summary(self, chat_id: int, query):
        """Handle current date summary for FREE and BASIC packages"""
        try:
            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            if not chat:
                await query.edit_message_text(f"Chat {chat_id} not found.")
                return False

            # Get current date using DateUtils
            current_date = DateUtils.now()
            
            # Use the same method as _handle_date_summary
            income_service = IncomeService()
            incomes = await income_service.get_income_by_specific_date_and_chat_id(
                chat_id=chat_id,
                target_date=current_date
            )

            if not incomes:
                message = (
                    f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {current_date.strftime('%d %b %Y')} ទេ។"
                )
            else:
                # Get username from the requesting user (who clicked the button)
                telegram_username = "Admin"
                if hasattr(query, 'from_user') and query.from_user:
                    requesting_user = query.from_user
                    if hasattr(requesting_user, 'username') and requesting_user.username:
                        telegram_username = requesting_user.username
                    elif hasattr(requesting_user, 'first_name') and requesting_user.first_name:
                        telegram_username = requesting_user.first_name
                    # If user is anonymous, username will remain "Admin"
                
                # Use daily report format for current date
                group_name = chat.group_name or f"Group {chat.chat_id}"
                message = daily_transaction_report(incomes, current_date, telegram_username, group_name)

            await query.edit_message_text(message, parse_mode='HTML')
            return True

        except Exception as e:
            force_log(f"Error in _handle_current_date_summary: {e}", "MenuHandler")
            await query.edit_message_text(f"Error generating current date summary: {str(e)}")
            return False

    async def _handle_weekly_summary_menu(self, chat_id: int, query):
        """Handle weekly summary by showing week selection menu like normal bot"""
        try:
            now = DateUtils.now()
            current_year = now.year
            current_month = now.month
            
            _, days_in_month = monthrange(current_year, current_month)

            keyboard = []
            
            # Week 1: 1-7
            week1_end = min(7, days_in_month)
            keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 1 (1-{week1_end})", callback_data=f"summary_week_{current_year}-{current_month:02d}-1")])
            
            # Week 2: 8-14
            if days_in_month >= 8:
                week2_end = min(14, days_in_month)
                keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 2 (8-{week2_end})", callback_data=f"summary_week_{current_year}-{current_month:02d}-2")])
            
            # Week 3: 15-21
            if days_in_month >= 15:
                week3_end = min(21, days_in_month)
                keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 3 (15-{week3_end})", callback_data=f"summary_week_{current_year}-{current_month:02d}-3")])
            
            # Week 4: 22-end of month
            if days_in_month >= 22:
                keyboard.append([InlineKeyboardButton(f"សប្តាហ៍ 4 (22-{days_in_month})", callback_data=f"summary_week_{current_year}-{current_month:02d}-4")])
            
            keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"📆 របាយការណ៍ប្រចាំសប្តាហ៍ - {now.strftime('%B %Y')}\n\nជ្រើសរើសសប្តាហ៍:", reply_markup=reply_markup)
            return True

        except Exception as e:
            force_log(f"Error in _handle_weekly_summary_menu: {e}", "MenuHandler")
            await query.edit_message_text(f"Error showing weekly menu: {str(e)}")
            return False

    async def _handle_monthly_summary_menu(self, chat_id: int, query):
        """Handle monthly summary by showing month selection menu like normal bot"""
        try:
            now = DateUtils.now()
            year = now.year
            keyboard = []
            
            for month in range(1, 13, 2):
                month_date_1 = datetime(year, month, 1)
                label_1 = month_date_1.strftime("%B %Y")
                callback_value_1 = month_date_1.strftime("%Y-%m")
                
                row = [InlineKeyboardButton(label_1, callback_data=f"summary_month_{callback_value_1}")]
                
                if month + 1 <= 12:
                    month_date_2 = datetime(year, month + 1, 1)
                    label_2 = month_date_2.strftime("%B %Y")
                    callback_value_2 = month_date_2.strftime("%Y-%m")
                    row.append(InlineKeyboardButton(label_2, callback_data=f"summary_month_{callback_value_2}"))
                
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("ជ្រើសរើសខែ:", reply_markup=reply_markup)
            return True

        except Exception as e:
            force_log(f"Error in _handle_monthly_summary_menu: {e}", "MenuHandler")
            await query.edit_message_text(f"Error showing monthly menu: {str(e)}")
            return False

    async def _handle_shift_summary_menu(self, chat_id: int, query):
        """Handle shift summary by showing shift selection menu like business bot"""
        try:
            keyboard = [
                [InlineKeyboardButton("ប្រចាំវេននេះ", callback_data="report_per_shift")],
                [InlineKeyboardButton("វេនផ្សេងទៀត", callback_data="other_shift_dates")],
                [InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("ជ្រើសរើសរបាយការណ៍វេន:", reply_markup=reply_markup)
            return True

        except Exception as e:
            force_log(f"Error in _handle_shift_summary_menu: {e}", "MenuHandler")
            await query.edit_message_text(f"Error showing shift menu: {str(e)}")
            return False

    async def _handle_report(self, chat_id: int, report_type: str, query):
        """Handle generating a specific report type"""
        try:
            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            if not chat:
                await query.edit_message_text(f"Chat {chat_id} not found.")
                return False

            # Get the user who clicked the button
            requesting_user = query.from_user if query else None

            if report_type == "daily":
                # Create return to menu button for daily reports
                keyboard = [[InlineKeyboardButton("ត្រឡប់", callback_data="menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                report = await self._generate_report(chat_id, "daily", requesting_user)
                await query.edit_message_text(report, reply_markup=reply_markup, parse_mode='HTML')
            elif report_type == "weekly":
                # No return button for weekly reports
                report = await self._generate_report(chat_id, "weekly", requesting_user)
                await query.edit_message_text(report, parse_mode='HTML')
            elif report_type == "monthly":
                # No return button for monthly reports
                report = await self._generate_report(chat_id, "monthly", requesting_user)
                await query.edit_message_text(report, parse_mode='HTML')

            return True
        except Exception as e:
            force_log(f"Error in _handle_report: {e}", "MenuHandler")
            await query.edit_message_text(
                f"Error generating {report_type} report: {str(e)}"
            )
            return False

    async def _handle_date_summary(self, chat_id: int, callback_data: str, query):
        """Handle date summary like normal bot"""
        try:
            date_str = callback_data.replace("summary_of_", "")
            selected_date = datetime.strptime(date_str, "%Y-%m-%d")

            income_service = IncomeService()
            incomes = await income_service.get_income_by_specific_date_and_chat_id(
                chat_id=chat_id,
                target_date=selected_date
            )

            if not incomes:
                message = (
                    f"គ្មានប្រតិបត្តិការសម្រាប់ថ្ងៃទី {selected_date.strftime('%d %b %Y')} ទេ។"
                )
            else:
                # Get username from the requesting user (who clicked the button)
                telegram_username = "Admin"
                if hasattr(query, 'from_user') and query.from_user:
                    requesting_user = query.from_user
                    if hasattr(requesting_user, 'username') and requesting_user.username:
                        telegram_username = requesting_user.username
                    elif hasattr(requesting_user, 'first_name') and requesting_user.first_name:
                        telegram_username = requesting_user.first_name
                    # If user is anonymous, username will remain "Admin"
                
                # Get chat object for group name
                chat = await self.chat_service.get_chat_by_chat_id(chat_id)
                group_name = chat.group_name or f"Group {chat.chat_id}" if chat else None
                
                # Use new daily report format
                start_date = selected_date
                end_date = selected_date + timedelta(days=1)
                message = daily_transaction_report(incomes, selected_date, telegram_username, group_name)

            await query.edit_message_text(message, parse_mode='HTML')
            return True

        except Exception as e:
            force_log(f"Error in _handle_date_summary: {e}", "MenuHandler")
            await query.edit_message_text(f"Error generating date summary: {str(e)}")
            return False

    async def _handle_shift_report(self, chat_id: int, query):
        """Handle current shift report for today"""
        try:
            # Get current shift data for today
            
            shift_service = ShiftService()
            current_date = DateUtils.now().date()
            
            # Get current or latest shift for today
            shift = await shift_service.get_current_shift(chat_id)
            
            if not shift:
                await query.edit_message_text(
                    "គ្មានវេនបើកសម្រាប់ថ្ងៃនេះទេ។",
                    parse_mode='HTML'
                )
                return ConversationHandler.END
            
            # Get shift report
            report = await shift_report(shift.id, shift.number, current_date)
            
            await query.edit_message_text(report, parse_mode='HTML')
            return True

        except Exception as e:
            force_log(f"Error in _handle_shift_report: {e}", "MenuHandler")
            await query.edit_message_text(f"Error generating shift report: {str(e)}")
            return False

    async def _handle_other_shift_dates(self, chat_id: int, query):
        """Handle other shift dates selection like business bot"""
        try:
            shift_service = ShiftService()
            recent_dates = await shift_service.get_recent_start_dates_with_shifts(chat_id, 3)
            
            if not recent_dates:
                keyboard = [
                    [InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="shift_summary")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📅 របាយការណ៍ថ្ងៃផ្សេង\n\n🔴 គ្មានទិន្នន័យសម្រាប់ថ្ងៃមុនៗ។\n\n💡 ទិន្នន័យនឹងបង្ហាញនៅទីនេះបន្ទាប់ពីមានវេនបានបិទ។",
                    reply_markup=reply_markup
                )
            else:
                keyboard = []
                for date in recent_dates:
                    date_str = date.strftime("%Y-%m-%d")
                    display_date = date.strftime("%d %b %Y")
                    keyboard.append([InlineKeyboardButton(display_date, callback_data=f"shift_date_{date_str}")])
                
                keyboard.append([InlineKeyboardButton("ថ្ងៃផ្សេងទៀត", callback_data="show_all_month_dates")])
                keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="shift_summary")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📅 របាយការណ៍ថ្ងៃផ្សេង\n\nជ្រើសរើសថ្ងៃដែលអ្នកចង់មើល:",
                    reply_markup=reply_markup
                )
            
            return True

        except Exception as e:
            force_log(f"Error in _handle_other_shift_dates: {e}", "MenuHandler")
            await query.edit_message_text(f"Error showing other shift dates: {str(e)}")
            return False

    async def _handle_shift_date_report(self, chat_id: int, date_str: str, query):
        """Handle shift report for a specific date"""
        try:
            
            shift_service = ShiftService()
            
            # Parse the date string (format: YYYY-MM-DD)
            shift_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            shift_date = shift_date_obj.date()
            
            # Get shifts for the specific date (by start date for admin bot)
            shifts = await shift_service.get_shifts_by_start_date(chat_id, shift_date)
            
            if not shifts:
                await query.edit_message_text(
                    f"គ្មានវេនសម្រាប់ថ្ងៃ {shift_date.strftime('%d-%m-%Y')} ទេ។",
                    parse_mode='HTML'
                )
                return True
            
            # Generate reports for all shifts on that date
            reports = []
            for shift in shifts:
                try:
                    report = await shift_report(shift.id, shift.number, shift_date_obj)
                    reports.append(report)
                except Exception as e:
                    force_log(f"Error generating report for shift {shift.id}: {e}", "MenuHandler")
                    reports.append(f"កំហុសក្នុងការបង្កើតរបាយការណ៍វេន {shift.number}")
            
            # Combine all reports
            if len(reports) == 1:
                final_report = reports[0]
            else:
                final_report = "".join(reports)
            
            await query.edit_message_text(final_report, parse_mode='HTML')
            return True
            
        except Exception as e:
            force_log(f"Error in _handle_shift_date_report: {e}", "MenuHandler")
            await query.edit_message_text(f"Error generating shift report: {str(e)}")
            return False

    async def _handle_show_all_month_dates(self, chat_id: int, query):
        """Show all dates with shifts in the current month"""
        try:
            from datetime import datetime
            from calendar import monthrange
            
            shift_service = ShiftService()
            now = DateUtils.now()
            current_month = now.month
            current_year = now.year
            
            # Get all dates in current month that have shifts
            all_dates_with_shifts = await shift_service.get_all_start_dates_with_shifts_in_month(
                chat_id, current_year, current_month
            )
            
            if not all_dates_with_shifts:
                keyboard = [
                    [InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="other_shift_dates")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"📅 ថ្ងៃទាំងអស់ - {now.strftime('%B %Y')}\n\n🔴 គ្មានទិន្នន័យសម្រាប់ខែនេះ។",
                    reply_markup=reply_markup
                )
            else:
                # Arrange dates in 5 columns
                keyboard = []
                row = []
                for date in all_dates_with_shifts:
                    date_str = date.strftime("%Y-%m-%d")
                    display_date = date.strftime("%d %b")  # Shorter format for columns
                    row.append(InlineKeyboardButton(display_date, callback_data=f"shift_date_{date_str}"))
                    
                    # Add row to keyboard when we have 5 buttons
                    if len(row) == 5:
                        keyboard.append(row)
                        row = []
                
                # Add remaining buttons in the last row
                if row:
                    keyboard.append(row)
                
                keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="other_shift_dates")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"📅 ថ្ងៃទាំងអស់ - {now.strftime('%B %Y')}\n\nជ្រើសរើសថ្ងៃដែលអ្នកចង់មើល:",
                    reply_markup=reply_markup
                )
            
            return True
            
        except Exception as e:
            force_log(f"Error in _handle_show_all_month_dates: {e}", "MenuHandler")
            await query.edit_message_text(f"Error showing all month dates: {str(e)}")
            return False

    @staticmethod
    async def _handle_other_dates(query):
        """Handle other dates - show current month dates"""
        try:
            now = DateUtils.now()
            current_month = now.month
            current_year = now.year
            
            # Generate date buttons for current month
            keyboard = []
            
            # Add title row
            month_name = now.strftime("%B %Y")
            
            # Add dates in rows of 7 (like calendar)
            _, last_day = monthrange(current_year, current_month)
            
            # Group dates in rows of 5 for better mobile display
            row = []
            for day in range(1, last_day + 1):
                date_str = f"{current_year}-{current_month:02d}-{day:02d}"
                row.append(InlineKeyboardButton(f"{day}", callback_data=f"summary_of_{date_str}"))
                
                if len(row) == 5 or day == last_day:
                    keyboard.append(row)
                    row = []
            
            # Add navigation row
            keyboard.append([InlineKeyboardButton("ត្រឡប់ក្រោយ", callback_data="daily_summary")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"ជ្រើសរើសថ្ងៃសម្រាប់ {month_name}:",
                reply_markup=reply_markup,
            )
            return True

        except Exception as e:
            force_log(f"Error in _handle_other_dates: {e}", "MenuHandler")
            await query.edit_message_text(f"Error: {str(e)}")
            return False

    @staticmethod
    async def _handle_week_summary(chat_id: int, callback_data: str, query):
        """Handle week summary like normal bot"""
        try:
            
            # Parse callback data: YYYY-MM-W format
            date_parts = callback_data.replace("summary_week_", "").split("-")
            year = int(date_parts[0])
            month = int(date_parts[1])
            week_number = int(date_parts[2])
            
            # Calculate start and end dates based on week number
            _, days_in_month = monthrange(year, month)
            
            if week_number == 1:
                start_day = 1
                end_day = min(7, days_in_month)
            elif week_number == 2:
                start_day = 8
                end_day = min(14, days_in_month)
            elif week_number == 3:
                start_day = 15
                end_day = min(21, days_in_month)
            elif week_number == 4:
                start_day = 22
                end_day = days_in_month
            else:
                raise ValueError(f"Invalid week number: {week_number}")
            
            start_date = datetime(year, month, start_day)
            end_date = datetime(year, month, end_day) + timedelta(days=1)  # End of day
            
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id,
                start_date=start_date,
                end_date=end_date,
            )

            if not incomes:
                period_text = f"សប្តាហ៍ {week_number} ({start_day}-{end_day} {start_date.strftime('%B %Y')})"
                message = f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។"
            else:
                # Use weekly report format
                message = weekly_transaction_report(incomes, start_date, end_date)

            await query.edit_message_text(message, parse_mode='HTML')
            return True

        except Exception as e:
            force_log(f"Error in _handle_week_summary: {e}", "MenuHandler")
            await query.edit_message_text(f"Error generating week summary: {str(e)}")
            return False

    @staticmethod
    async def _handle_month_summary(chat_id: int, callback_data: str, query):
        """Handle month summary like normal bot"""
        try:
            
            start_date = datetime.strptime(
                callback_data.replace("summary_month_", ""), "%Y-%m"
            )
            
            _, last_day = monthrange(start_date.year, start_date.month)
            end_date = start_date.replace(day=last_day) + timedelta(days=1)
            
            income_service = IncomeService()
            incomes = await income_service.get_income_by_date_and_chat_id(
                chat_id=chat_id,
                start_date=start_date,
                end_date=end_date,
            )

            if not incomes:
                period_text = start_date.strftime("%B %Y")
                message = f"គ្មានប្រតិបត្តិការសម្រាប់ {period_text} ទេ។"
            else:
                # Use monthly report format
                message = monthly_transaction_report(incomes, start_date, end_date)

            await query.edit_message_text(message, parse_mode='HTML')
            return True

        except Exception as e:
            force_log(f"Error in _handle_month_summary: {e}", "MenuHandler")
            await query.edit_message_text(f"Error generating month summary: {str(e)}")
            return False

    async def _generate_report(self, chat_id: int, report_type: str, requesting_user=None) -> str:
        """Generate report text by calling appropriate service methods"""

        income_service = IncomeService()

        # Get current time using DateUtils for consistency
        now = DateUtils.now()

        if report_type == "daily":
            start_date = now
            end_date = now + timedelta(days=1)
            title = f"ថ្ងៃទី {now.strftime('%d %b %Y')}"
        elif report_type == "weekly":
            # Get this week's Monday (start of current week)
            this_week_monday = now - timedelta(days=now.weekday())
            # Get this week's Sunday (end of current week)
            this_week_sunday = this_week_monday + timedelta(days=6)
            start_date = this_week_monday
            end_date = this_week_sunday + timedelta(days=1)  # Include Sunday
            
            # Format title like the main bot
            if this_week_monday.month != this_week_sunday.month:
                title = f"សប្តាហ៍នេះ ({this_week_monday.strftime('%d %b')} - {this_week_sunday.strftime('%d %b %Y')})"
            else:
                title = f"សប្តាហ៍នេះ ({this_week_monday.strftime('%d')} - {this_week_sunday.strftime('%d %b %Y')})"
        elif report_type == "monthly":
            # First day of current month
            start_of_month = now.replace(day=1)
            start_date = start_of_month
            end_date = now + timedelta(days=1)
            title = f"{start_of_month.strftime('%d')} - {now.strftime('%d %b %Y')}"
        else:
            return "Invalid report type"

        # Get income data using the same method as normal bot
        incomes = await income_service.get_income_by_date_and_chat_id(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
        )

        # If no data found, return no data message
        if not incomes:
            return f"គ្មានប្រតិបត្តិការសម្រាប់ {title} ទេ។"

        # For daily reports, use the new format
        if report_type == "daily":
            # Get username from the requesting user (who clicked the button)
            telegram_username = "Admin"
            if requesting_user:
                if hasattr(requesting_user, 'username') and requesting_user.username:
                    telegram_username = requesting_user.username
                elif hasattr(requesting_user, 'first_name') and requesting_user.first_name:
                    telegram_username = requesting_user.first_name
                # If user is anonymous, username will remain "Admin"
            
            # Get chat object for group name
            chat = await self.chat_service.get_chat_by_chat_id(chat_id)
            group_name = chat.group_name or f"Group {chat.chat_id}" if chat else None
            
            return daily_transaction_report(incomes, now, telegram_username, group_name)
        elif report_type == "weekly":
            # Use the new weekly format
            return weekly_transaction_report(incomes, start_date, end_date)
        elif report_type == "monthly":
            # Use the new monthly format
            return monthly_transaction_report(incomes, start_date, end_date)
        
        # For other reports, use the old format
        from helper import total_summary_report
        period_text = title
        formatted_title = f"សរុបប្រតិបត្តិការ {period_text}"
        return total_summary_report(incomes, formatted_title)

    async def menu_callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle callback queries from menu inline buttons"""
        query = update.callback_query

        try:
            # We need to answer the callback query first to stop the loading indicator
            await query.answer()

            # Get the callback data
            callback_data = query.data

            # First, check if we're handling direct admin bot actions
            if callback_data in ["close_menu"]:
                await query.edit_message_text("Menu closed.")
                return ConversationHandler.END

            # Get chat_id from context or use message chat_id as fallback
            if context and context.user_data and "admin_chat_id" in context.user_data:
                chat_id = context.user_data["admin_chat_id"]
            else:
                # No stored chat ID from admin bot menu flow
                # This might be a global callback handler case
                await query.edit_message_text(
                    "Session expired. Please run /menu again."
                )
                return ConversationHandler.END

            # Prepare callback handlers for different report types
            if callback_data == "daily_summary":
                result = await self._handle_daily_summary_menu(chat_id, query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data == "current_date_summary":
                result = await self._handle_current_date_summary(chat_id, query)
                return ConversationHandler.END if result else ConversationHandler.END  # End conversation after showing report
            elif callback_data == "weekly_summary":
                result = await self._handle_weekly_summary_menu(chat_id, query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data == "monthly_summary":
                result = await self._handle_monthly_summary_menu(chat_id, query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data == "shift_summary":
                result = await self._handle_shift_summary_menu(chat_id, query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data == "menu":
                # Return to package-based menu - recreate the menu buttons based on package
                chat = await self.chat_service.get_chat_by_chat_id(chat_id)
                if not chat:
                    await query.edit_message_text("Chat not found.")
                    return ConversationHandler.END

                # Import GroupPackageService here to avoid circular imports
                group_package_service = GroupPackageService()
                
                # Get group package to determine available options
                group_package = await group_package_service.get_package_by_chat_id(chat.chat_id)
                package_type = group_package.package if group_package else None
                
                keyboard = []

                if package_type and package_type.value == 'BUSINESS':
                    keyboard.append([InlineKeyboardButton("តាមវេន", callback_data="shift_summary")])

                # Always available options
                keyboard.append([InlineKeyboardButton("ប្រចាំថ្ងៃ", callback_data="daily_summary")])
                
                # Package-based options
                if package_type and package_type.value in ['STANDARD', 'BUSINESS']:
                    keyboard.append([InlineKeyboardButton("ប្រចាំសប្តាហ៍", callback_data="weekly_summary")])
                    keyboard.append([InlineKeyboardButton("ប្រចាំខែ", callback_data="monthly_summary")])

                keyboard.append([InlineKeyboardButton("បិទ", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)

                group_name = chat.group_name or f"Group {chat.chat_id}"
                text = f"Reports for {group_name}:\nPackage: {package_type.value if package_type else 'Unknown'}\n\nSelect report type:"

                await query.edit_message_text(text, reply_markup=reply_markup)
                return 1008  # CALLBACK_QUERY_CODE
            elif callback_data.startswith("summary_of_"):
                result = await self._handle_date_summary(chat_id, callback_data, query)
                return ConversationHandler.END  # End conversation after showing final report
            elif callback_data == "report_per_shift":
                result = await self._handle_shift_report(chat_id, query)
                return ConversationHandler.END if result else ConversationHandler.END  # End conversation after showing report
            elif callback_data == "other_dates":
                result = await self._handle_other_dates(query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data.startswith("summary_week_"):
                result = await self._handle_week_summary(chat_id, callback_data, query)
                return ConversationHandler.END  # End conversation after showing final report
            elif callback_data.startswith("summary_month_"):
                result = await self._handle_month_summary(chat_id, callback_data, query)
                return ConversationHandler.END  # End conversation after showing final report
            elif callback_data == "other_shift_dates":
                result = await self._handle_other_shift_dates(chat_id, query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data == "show_all_month_dates":
                result = await self._handle_show_all_month_dates(chat_id, query)
                return 1008 if result else ConversationHandler.END  # CALLBACK_QUERY_CODE
            elif callback_data.startswith("shift_date_"):
                date_str = callback_data.replace("shift_date_", "")
                result = await self._handle_shift_date_report(chat_id, date_str, query)
                return ConversationHandler.END if result else ConversationHandler.END  # End conversation after showing report

            # If we get here, it's an unknown callback
            await query.edit_message_text(f"Unhandled callback: {callback_data}")
            return 1008  # CALLBACK_QUERY_CODE

        except Exception as e:
            force_log(f"Error in menu_callback_query_handler: {e}", "MenuHandler")
            try:
                await query.edit_message_text(
                    f"Error processing button action: {str(e)}"
                )
            except Exception:
                pass
            return ConversationHandler.END