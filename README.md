# TG Message Listener Main

"tg_message_listener_main.py" is a Python script that serves as the core of a Telegram bot application, designed to listen for and process messages from Telegram chats, groups, or channels. It uses the Telethon library to interact with the Telegram API, providing an efficient, event-driven system for routing messages to specific handlers based on content or context.

## Features

Asynchronous Message Listening: Utilizes async I/O for real-time message listening without blocking.
Modular Design: Easily extendable with new message handlers for different types of content or commands.
Secure Authentication: Integrates with credentials_telegram.json for secure API key and bot token management.
Event-Driven Processing: Employs Telethon's event listener capabilities for effective message processing.

## Getting Started

## Prerequisites

- Python 3.6+
- Telethon library
- A valid Telegram API ID and hash, obtainable through my.telegram.org
- (Optional) A Telegram bot token, obtainable via BotFather if operating in bot mode.
- MySQL database

## Installation

Clone the repository:

```bash
git clone https://your-repository-url.git
cd your-repository-directory
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

Configure your credentials in .env file:

```bash
DB_NAME=telegram_bot
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost

BOT_TOKEN=BOT_NAME
BOT_NAME=BOT_NAME
CHAT_ID=CHAT_ID
PHONE_NUMBER=PHONE_NUMBER
API_ID=API_ID
API_HASH=API_HASH
```

## Usage

Run the script to start listening for and processing messages:

```bash
python main.py
```

## Structure

**main.py**: The main script that initializes the Telegram client and sets up event listeners for incoming messages.

## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, feel free to fork the repository, make your changes, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.

Feedback and contributions are welcome!

## Deployment

This project supports two separate deployment modes: **Main Telethon Service** and **Additional Telethon Service** for better isolation and reliability.

### Architecture Overview

- **Main Service**: Handles primary phone numbers and critical operations
- **Additional Service**: Handles additional phone numbers independently
- **Benefits**: If additional service fails (e.g., verification codes), main service continues uninterrupted

### GitHub Actions Deployment

The project includes two separate CD pipelines:

1. **`deploy-telethon-main.yml`** - Deploys main service
2. **`deploy-additional-telethon.yml`** - Deploys additional service

### Setting up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

#### Required Secrets for Both Services:
```
HOST=your-server-ip
USERNAME=your-ssh-username  
PASSWORD=your-ssh-password
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
```

#### Main Service Secrets:
```
PHONE_NUMBER1=+1234567890
API_ID1=12345678
API_HASH1=your-api-hash-1

PHONE_NUMBER2=+1234567891  
API_ID2=12345679
API_HASH2=your-api-hash-2
# ... up to PHONE_NUMBER9, API_ID9, API_HASH9
```

#### Additional Service Secrets:
```
ADDITIONAL_PHONE_NUMBER_1=+1234567892
ADDITIONAL_API_ID_1=12345680
ADDITIONAL_API_HASH_1=your-additional-api-hash-1

ADDITIONAL_PHONE_NUMBER_2=+1234567893
ADDITIONAL_API_ID_2=12345681  
ADDITIONAL_API_HASH_2=your-additional-api-hash-2
# ... up to _5
```

### Manual Deployment

#### Deploy Main Service:
1. Go to Actions → Deploy Telethon Client (Main) → Run workflow

#### Deploy Additional Service:
1. Go to Actions → Deploy Additional Telethon Client → Run workflow

### Local Development

#### Running Main Service:
```bash
# Set environment variables in .env.telethon
python main_telethon_only.py
```

#### Running Additional Service:
```bash  
# Set environment variables in .env.additional
python main_telethon_only.py --additional
```

### Service Management (Production)

#### Main Service:
```bash
# Start/stop/restart main service
sudo systemctl start mytelethon
sudo systemctl stop mytelethon  
sudo systemctl restart mytelethon

# View logs
sudo journalctl -u mytelethon -f
```

#### Additional Service:
```bash
# Start/stop/restart additional service
sudo systemctl start mytelethon-additional
sudo systemctl stop mytelethon-additional
sudo systemctl restart mytelethon-additional

# View logs  
sudo journalctl -u mytelethon-additional -f
```

### Verification Code Handling

⚠️ **Important**: Additional services that require verification codes should be authenticated manually:

1. SSH into your server
2. Stop the additional service: `sudo systemctl stop mytelethon-additional`
3. Run manually for verification: `cd /root/telegram-listener && source myenv/bin/activate && python main_telethon_only.py --additional`
4. Enter verification code when prompted
5. Restart service: `sudo systemctl start mytelethon-additional`

### Environment Files Structure

#### Main Service (`.env.telethon`):
```bash
DB_NAME=your-db
DB_USER=your-user
DB_PASSWORD=your-password
DB_HOST=your-host

PHONE_NUMBER1=+1234567890
API_ID1=12345678
API_HASH1=your-api-hash
```

#### Additional Service (`.env.additional`):
```bash
DB_NAME=your-db
DB_USER=your-user  
DB_PASSWORD=your-password
DB_HOST=your-host

ADDITIONAL_PHONE_NUMBER_1=+1234567892
ADDITIONAL_API_ID_1=12345680
ADDITIONAL_API_HASH_1=your-additional-api-hash
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
