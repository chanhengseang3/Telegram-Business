import os


class CredentialLoader:
    BOT_REQUIRED_ENV_VARS = [
        "BOT_TOKEN",
        "BOT_NAME",
        "DB_USER",
        "DB_HOST",
        "DB_NAME",
    ]
    
    TELETHON_REQUIRED_ENV_VARS = [
        "API_ID1",
        "API_HASH1",
        "PHONE_NUMBER1",
    ]
    
    ADDITIONAL_TELETHON_REQUIRED_ENV_VARS = [
        "ADDITIONAL_API_ID_1",
        "ADDITIONAL_API_HASH_1", 
        "ADDITIONAL_PHONE_NUMBER_1",
    ]

    OPTIONAL_ENV_VARS = ["TIMEZONE"]

    def __init__(self):
        self.bot_token: str = ""
        self.bot_name: str = ""
        self.db_user: str = ""
        self.db_password: str = ""
        self.db_host: str = ""
        self.db_name: str = ""
        self.api_id1: str = ""
        self.api_hash1: str = ""
        self.phone_number1: str = ""
        self.admin_bot_token: str = ""
        self.autosum_business_bot_token: str = ""
        self.private_chat_bot_token: str = ""
        self.utils_bot_token: str = ""
        
        # Support for multiple phone numbers (2-9)
        for i in range(2, 10):
            setattr(self, f'api_id{i}', None)
            setattr(self, f'api_hash{i}', None)
            setattr(self, f'phone_number{i}', None)
            
        # Support for additional phone numbers (1-5)
        for i in range(1, 6):
            setattr(self, f'additional_api_id_{i}', None)
            setattr(self, f'additional_api_hash_{i}', None)
            setattr(self, f'additional_phone_number_{i}', None)

    def load_credentials(self, mode: str = "both") -> dict:
        """
        Load the credentials from the environment variables.
        
        Args:
            mode: Credential loading mode - "both", "bots_only", or "telethon_only"
        """
        print("Loading credentials...")
        missing = []
        
        # Load all environment variables
        self.bot_token = os.getenv("BOT_TOKEN") or ""
        self.bot_name = os.getenv("BOT_NAME") or ""
        self.db_user = os.getenv("DB_USER") or ""
        self.db_password = os.getenv("DB_PASSWORD") or ""
        self.db_host = os.getenv("DB_HOST") or ""
        self.db_name = os.getenv("DB_NAME") or ""
        self.api_id1 = os.getenv("API_ID1") or ""
        self.api_hash1 = os.getenv("API_HASH1") or ""
        self.phone_number1 = os.getenv("PHONE_NUMBER1") or ""
        self.admin_bot_token = os.getenv("ADMIN_BOT_TOKEN") or ""
        self.autosum_business_bot_token = os.getenv("AUTOSUM_BUSINESS_BOT_TOKEN") or ""
        self.private_chat_bot_token = os.getenv("PRIVATE_CHAT_BOT") or ""
        self.utils_bot_token = os.getenv("UTILS_BOT_TOKEN") or ""

        # Load additional phone number configurations (2-9)
        for i in range(2, 10):
            api_id_val = os.getenv(f'API_ID{i}')
            api_hash_val = os.getenv(f'API_HASH{i}')
            phone_val = os.getenv(f'PHONE_NUMBER{i}')
            
            print(f"Loading config {i}: API_ID{i}={api_id_val}, API_HASH{i}={api_hash_val}, PHONE_NUMBER{i}={phone_val}")
            
            setattr(self, f'api_id{i}', api_id_val if api_id_val else None)
            setattr(self, f'api_hash{i}', api_hash_val if api_hash_val else None)
            setattr(self, f'phone_number{i}', phone_val if phone_val else None)
            
        # Load additional phone number configurations (1-5) for additional service
        for i in range(1, 6):
            api_id_val = os.getenv(f'ADDITIONAL_API_ID_{i}')
            api_hash_val = os.getenv(f'ADDITIONAL_API_HASH_{i}')
            phone_val = os.getenv(f'ADDITIONAL_PHONE_NUMBER_{i}')
            
            print(f"Loading additional config {i}: ADDITIONAL_API_ID_{i}={api_id_val}, ADDITIONAL_API_HASH_{i}={api_hash_val}, ADDITIONAL_PHONE_NUMBER_{i}={phone_val}")
            
            setattr(self, f'additional_api_id_{i}', api_id_val if api_id_val else None)
            setattr(self, f'additional_api_hash_{i}', api_hash_val if api_hash_val else None)
            setattr(self, f'additional_phone_number_{i}', phone_val if phone_val else None)

        # Determine which variables are required based on mode
        required_vars = []
        if mode == "both":
            required_vars = self.BOT_REQUIRED_ENV_VARS + self.TELETHON_REQUIRED_ENV_VARS
        elif mode == "bots_only":
            required_vars = self.BOT_REQUIRED_ENV_VARS
        elif mode == "telethon_only":
            required_vars = self.TELETHON_REQUIRED_ENV_VARS
        elif mode == "additional_telethon":
            required_vars = self.ADDITIONAL_TELETHON_REQUIRED_ENV_VARS
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'both', 'bots_only', 'telethon_only', or 'additional_telethon'")

        # Check for missing required variables
        for var in required_vars:
            # Convert variable name to attribute name
            attr_name = var.lower()
            if not getattr(self, attr_name):
                missing.append(var)

        if missing:
            error_msg = (
                f"Missing required {mode} environment variables: {', '.join(missing)}\n"
            )
            error_msg += "For local development, set these in your .env file.\n"
            error_msg += "For CI/CD deployment, set these as GitHub Secrets in your repository settings."
            raise EnvironmentError(error_msg)

        print("Credentials loaded successfully")
        return {
            "bot_token": self.bot_token,
            "bot_name": self.bot_name,
            "api_id1": self.api_id1,
            "api_hash1": self.api_hash1,
            "phone_number1": self.phone_number1,
        }
