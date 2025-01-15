# Import required modules
from telebot import TeleBot
from config import BOT_TOKEN
from handlers.link_handlers import register_link_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers

# Initialize the bot
bot = TeleBot(BOT_TOKEN)

# Register handlers
register_link_handlers(bot)
register_admin_handlers(bot)
register_user_handlers(bot)

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)