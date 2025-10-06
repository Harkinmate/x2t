# X2T Telegram Twitter Bot

## Setup (Termux)
1. Clone the repo: `git clone https://github.com/yourusername/x2t.git`
2. Go into folder: `cd x2t`
3. Run setup: `bash setup_bot.sh`
4. Add your Telegram bot token in `.env` if not already.
5. Bot will run automatically in background and fetch tweets every 1 min.

## Commands
/start - Check bot status  
/help - Show all commands  
/setchannel @channel - Set target Telegram channel  
/addtwitter username - Track Twitter account  
/removetwitter username - Remove tracked account  
/listtwitters - List tracked accounts  
/status - Show bot status and last tweets  
/fetch - Manually fetch latest tweets
