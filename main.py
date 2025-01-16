import logging
from config import bot  # Import bot instance from config
from handlers.link_handlers import register_link_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers
from handlers.start_handler import handle_start
from utils.scheduler import link_scheduler

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

def setup_handlers():
    """Set up all message handlers for the bot."""
    try:
        # Register handlers
        register_link_handlers(bot)
        register_admin_handlers(bot)
        register_user_handlers(bot)
        
        # Register start handler
        @bot.message_handler(commands=['start'])
        def start(message):
            handle_start(message, bot)
        
        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")
        raise

def setup_scheduler():
    """Setup and start the link cleanup scheduler"""
    try:
        # Default configuration: 4 times per day, keep links for 3 days
        link_scheduler.setup_schedule(runs_per_day=4, cleanup_days=3)
        link_scheduler.start()
        logger.info("Link cleanup scheduler initialized")
    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")

def main():
    """Main function to run the bot."""
    try:
        # Setup handlers
        setup_handlers()
        
        # Setup and start scheduler
        setup_scheduler()
        
        # Log bot information
        bot_info = bot.get_me()
        logger.info(f"Bot started successfully: @{bot_info.username}")
        
        # Start the bot
        logger.info("Bot is running...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise
    finally:
        # Ensure scheduler is stopped when bot stops
        link_scheduler.stop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")