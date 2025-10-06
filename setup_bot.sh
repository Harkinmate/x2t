#!/bin/bash

# Update packages
pkg update -y && pkg upgrade -y
pkg install python git -y

# Clone bot repository (if not already cloned)
if [ ! -d "x2t" ]; then
    git clone https://github.com/yourusername/x2t.git
fi
cd x2t

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file (replace with your Telegram bot token)
if [ ! -f ".env" ]; then
cat > .env <<EOL
TELEGRAM_TOKEN=YOUR_BOT_TOKEN_HERE
EOL
fi

# Run the bot in background
nohup python bot.py > bot.log 2>&1 &

echo "✅ Bot setup complete and running in background."
echo "Logs: x2t/bot.log"
