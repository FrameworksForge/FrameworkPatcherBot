# Framework Patcher Bot

A powerful Telegram bot designed to automate the patching of Android framework files (framework.jar, services.jar, miui-services.jar) for Xiaomi devices. This bot interfaces with GitHub Actions to perform complex patching tasks in a secure environment.

## Features

- **Automated Workflow Triggering**: Automatically detects the correct API level and triggers the corresponding GitHub Action.
- **Support for Multi-Features**:
    - Signature Verification Bypass
    - CN Notification Fix (Android 15+)
    - Secure Flag Disable (Android 15+)
    - Kaorios Toolbox / Play Integrity Fix (Android 15+)
- **Device Database**: Integration with Xiaomi firmware trackers to suggest/validate device codenames and ROM versions.
- **Manual Mode**: Allows users to manually enter ROM and Android versions if not found in the database.
- **Safe Tagging**: Robust sanitization of release tags and version names for reliable GitHub Releases.

## Setup & Deployment

### Prerequisites

- Linux server (Ubuntu/Debian recommended)
- Python 3.10+
- Git
- Telegram Bot Token (from @BotFather)
- GitHub Personal Access Token (Classic recommended with workflow scope)

### Quick Deployment

Clone the repository and run the deployment script:

```bash
git clone https://github.com/FrameworksForge/FrameworkPatcherBot.git
cd FrameworkPatcherBot
chmod +x deploy.sh
./deploy.sh
```

The script will guide you through:
1. Creating a .env file for your credentials.
2. Setting up a Python virtual environment.
3. (Optional) Creating a systemd service for 24/7 uptime.

## Configuration

Your .env file should contain the following:

```env
BOT_TOKEN=your_telegram_bot_token
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=FrameworksForge
GITHUB_REPO=FrameworkPatcher
PIXELDRAIN_API_KEY=your_pixeldrain_api_key
```

## Credits

- Core logic and patching by [FrameworksForge Team](https://github.com/FrameworksForge)
- Data provided by [Xiaomi Firmware Updater](https://github.com/XiaomiFirmwareUpdater)

---
*Maintained by the FrameworksForge Community.*
