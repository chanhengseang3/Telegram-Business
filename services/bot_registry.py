"""
Bot Registry - Singleton pattern to access bot instances across services
"""


class BotRegistry:
    """Singleton registry for bot services"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            self.private_bot = None
            self.business_bot = None
            self.standard_bot = None
            self.admin_bot = None
            self.utils_bot = None
            self._initialized = True
    
    def set_private_bot(self, bot):
        """Set the private bot instance"""
        self.private_bot = bot
    
    def set_business_bot(self, bot):
        """Set the business bot instance"""
        self.business_bot = bot
    
    def set_standard_bot(self, bot):
        """Set the standard bot instance"""
        self.standard_bot = bot
    
    def set_admin_bot(self, bot):
        """Set the admin bot instance"""
        self.admin_bot = bot
    
    def set_utils_bot(self, bot):
        """Set the utils bot instance"""
        self.utils_bot = bot
    
    def get_private_bot(self):
        """Get the private bot instance"""
        return self.private_bot
    
    def get_business_bot(self):
        """Get the business bot instance"""
        return self.business_bot
    
    def get_standard_bot(self):
        """Get the standard bot instance"""
        return self.standard_bot
    
    def get_admin_bot(self):
        """Get the admin bot instance"""
        return self.admin_bot
    
    def get_utils_bot(self):
        """Get the utils bot instance"""
        return self.utils_bot