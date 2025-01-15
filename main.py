import os
import logging
from telebot import TeleBot
from config import BOT_TOKEN
from handlers.link_handlers import register_link_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize the bot
bot = TeleBot(BOT_TOKEN)

def setup_handlers():
    """
    Set up all message handlers for the bot.
    """
    try:
        # Register handlers
        register_link_handlers(bot)
        register_admin_handlers(bot)
        register_user_handlers(bot)
        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")
        raise

def main():
    """
    Main function to run the bot.
    """
    try:
        # Setup handlers
        setup_handlers()
        
        # Log bot information
        bot_info = bot.get_me()
        logger.info(f"Bot started successfully: @{bot_info.username}")
        
        # Start the bot
        logger.info("Bot is running...")
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise

# Start the bot
if __name__ == "__main__":
    main()