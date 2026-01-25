#!/bin/bash

# Framework Patcher Bot - Deployment Script
# This script automates the setup and deployment of the bot.

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${YELLOW}[*] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_error() {
    echo -e "${RED}[!] $1${NC}"
}

# Check if .env exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Creating a template .env file..."
    cat <<EOF > .env
BOT_TOKEN=your_telegram_bot_token
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=FrameworksForge
GITHUB_REPO=FrameworkPatcher
PIXELDRAIN_API_KEY=your_pixeldrain_api_key
EOF
    print_status "Please edit the .env file with your credentials and run this script again."
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Install dependencies
print_status "Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Create systemd service (Optional)
read -p "Do you want to create a systemd service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CUR_DIR=$(pwd)
    USER_NAME=$(whoami)
    
    print_status "Creating systemd service 'framework-bot'..."
    cat <<EOF | sudo tee /etc/systemd/system/framework-bot.service
[Unit]
Description=Framework Patcher Bot
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$CUR_DIR
Environment="PYTHONPATH=$CUR_DIR"
ExecStart=$CUR_DIR/venv/bin/python3 -m Framework
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    print_success "Service created! You can start it with: sudo systemctl start framework-bot"
fi

print_success "Setup completed successfully!"
print_status "To start the bot manually, run: ./venv/bin/python3 -m Framework"
