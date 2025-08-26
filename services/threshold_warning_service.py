from helper.logger_utils import force_log
from services.chat_service import ChatService
from services.shift_service import ShiftService


class ThresholdWarningService:
    """
    Service to handle threshold checking and warning messages.
    This service runs within telethon client to send warnings directly.
    """
    
    def __init__(self, telethon_client=None):
        self.telethon_client = telethon_client
        self.shift_service = ShiftService()
    
    async def check_and_send_warnings(
        self, 
        chat_id: int, 
        new_income_amount: float,
        new_income_currency: str
    ):
        """
        Check if individual transaction amount is below thresholds and send warning messages.
        Called after income is saved to database.
        """
        try:
            # Only check if we have telethon_client
            if not self.telethon_client:
                return
            
            force_log(f"ThresholdWarningService: Checking transaction threshold for chat {chat_id}, amount: {new_income_amount} {new_income_currency}")
            
            # Get thresholds for this chat
            thresholds = await ChatService.get_chat_thresholds(chat_id)
            if not thresholds:
                force_log(f"ThresholdWarningService: No thresholds set for chat {chat_id}")
                return
            
            warnings_to_send = []
            
            # Check KHR threshold
            if thresholds.get("khr_threshold") is not None and new_income_currency == "KHR":
                khr_threshold = thresholds["khr_threshold"]
                
                if new_income_amount < khr_threshold:
                    warning_msg = (
                        f"<pre>- - - សូមត្រូតពិនិត្យមើលបន្ថែម - - -\n\n"
                        f"ប្រាក់ចូល ៛ {new_income_amount:,.0f} តិចជាងធម្មតា</pre>"
                    )
                    warnings_to_send.append(warning_msg)
            
            # Check USD threshold  
            if thresholds.get("usd_threshold") is not None and new_income_currency == "USD":
                usd_threshold = thresholds["usd_threshold"]
                
                if new_income_amount < usd_threshold:
                    warning_msg = (
                        f"<pre>- - - សូមត្រូតពិនិត្យមើលបន្ថែម - - -\n\n"
                        f"ប្រាក់ចូល $ {new_income_amount:.2f} តិចជាងធម្មតា</pre>"
                    )
                    warnings_to_send.append(warning_msg)
            
            # Send warnings if any
            for warning_msg in warnings_to_send:
                await self._send_warning_message(chat_id, warning_msg)
                    
        except Exception as e:
            force_log(f"ThresholdWarningService: Error in check_and_send_warnings: {e}", "ERROR")
    
    async def _send_warning_message(self, chat_id: int, warning_msg: str):
        """Send threshold warning message to the chat"""
        try:
            await self.telethon_client.send_message(
                entity=chat_id,
                message=warning_msg,
                parse_mode='html'
            )
            force_log(f"ThresholdWarningService: Sent warning to chat {chat_id}: {warning_msg}")
        except Exception as send_error:
            force_log(f"ThresholdWarningService: Error sending warning: {send_error}", "ERROR")