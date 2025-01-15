import os
import logging
from telebot import TeleBot, apihelper  # Add apihelper import
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

def create_bot():
    """Create and configure the bot instance."""
    try:
        if not BOT_TOKEN:
            raise ValueError("Bot token not found in configuration")
            
        # Enable middleware support BEFORE creating the bot instance
        apihelper.ENABLE_MIDDLEWARE = True
        
        # Create bot instance
        bot = TeleBot(BOT_TOKEN, parse_mode='Markdown')
        
        # Add global error handling
        @bot.middleware_handler(update_types=['message'])
        def global_error_handler(bot_instance, update):
            try:
                logger.debug(f"Processing update: {update}")
                return True  # Continue processing
            except Exception as e:
                logger.error(f"Error in middleware: {str(e)}")
                return False  # Stop processing on error
        
        return bot
    except Exception as e:
        logger.error(f"Error creating bot: {str(e)}")
        raise

def setup_handlers(bot):
    """Set up all message handlers for the bot."""
    try:
        # Register handlers and check for successful registration
        if not bot:
            raise ValueError("Bot instance is None")

        # Register handlers
        register_link_handlers(bot)
        register_admin_handlers(bot)
        register_user_handlers(bot)

        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")
        raise

def main():
    """Main function to run the bot."""
    try:
        # Create bot instance
        bot = create_bot()
        
        # Setup handlers
        setup_handlers(bot)
        
        # Log bot information
        bot_info = bot.get_me()
        logger.info(f"Bot started successfully: @{bot_info.username}")
        
        # Start the bot
        logger.info("Bot is running...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")