from utils.logger import logger
from telebot.types import Message
from utils.scheduler import link_scheduler
from utils.helpers import is_admin
from config import bot  # Import bot instance from config


def register_admin_handlers(bot):
    """
    Register all admin-related command handlers.
    """
    
    @bot.message_handler(commands=["del"])
    def handle_del_command(message):
        """
        Handle the /del command to delete links.
        Only accessible by admins.
        """
        try:
            if not is_admin(message.from_user.id):
                bot.reply_to(message, "You are not authorized to use this command.")
                logger.warning(f"Unauthorized delete attempt by user {message.from_user.id}")
                return

            # Prompt the admin to tap on a link to delete it
            bot.reply_to(message, "Tap on the link you want to delete.")
            logger.info(f"Delete command initiated by admin {message.from_user.id}")

        except Exception as e:
            logger.error(f"Error in delete command: {str(e)}")
            bot.reply_to(message, "An error occurred. Please try again later.")

    @bot.message_handler(commands=['set_cleanup'])
    def handle_set_cleanup(message: Message):
        """Handle cleanup schedule configuration"""
        try:
            if not is_admin(message.from_user.id):
                bot.reply_to(message, "⛔️ This command is only for admins.")
                return

            # Parse command arguments
            args = message.text.split()
            if len(args) != 3:
                bot.reply_to(message, 
                    "⚠️ Usage: /set_cleanup <runs_per_day> <days_to_keep>\n"
                    "Example: /set_cleanup 4 3")
                return

            runs_per_day = int(args[1])
            days_to_keep = int(args[2])

            # Validate input
            if not (1 <= runs_per_day <= 24):
                bot.reply_to(message, "⚠️ Runs per day must be between 1 and 24")
                return

            if days_to_keep < 1:
                bot.reply_to(message, "⚠️ Days to keep must be at least 1")
                return

            # Setup and start scheduler
            link_scheduler.setup_schedule(runs_per_day, days_to_keep)
            if not link_scheduler.is_running:
                link_scheduler.start()

            # Get next run times
            next_runs = link_scheduler.get_next_run_times()
            next_runs_text = "\n".join(f"• {time}" for time in next_runs)

            response = (
                f"✅ Cleanup schedule configured:\n"
                f"• Running {runs_per_day} times per day\n"
                f"• Removing links older than {days_to_keep} days\n\n"
                f"Next scheduled runs (UTC):\n{next_runs_text}"
            )
            bot.reply_to(message, response)

        except ValueError:
            bot.reply_to(message, "⚠️ Please provide valid numbers for runs per day and days to keep")
        except Exception as e:
            logger.error(f"Error in set_cleanup: {str(e)}")
            bot.reply_to(message, "❌ An error occurred while setting up the cleanup schedule")

    @bot.message_handler(commands=['cleanup_status'])
    def handle_cleanup_status(message: Message):
        """Show current cleanup schedule status"""
        try:
            if not is_admin(message.from_user.id):
                bot.reply_to(message, "⛔️ This command is only for admins.")
                return

            if not link_scheduler.is_running:
                bot.reply_to(message, "⚠️ Cleanup scheduler is not running")
                return

            next_runs = link_scheduler.get_next_run_times()
            next_runs_text = "\n".join(f"• {time}" for time in next_runs)

            status = (
                f"📊 Cleanup Schedule Status:\n"
                f"• Running: {link_scheduler.is_running}\n"
                f"• Runs per day: {link_scheduler.runs_per_day}\n"
                f"• Days to keep: {link_scheduler.cleanup_days}\n\n"
                f"Next scheduled runs (UTC):\n{next_runs_text}"
            )
            bot.reply_to(message, status)

        except Exception as e:
            logger.error(f"Error in cleanup_status: {str(e)}")
            bot.reply_to(message, "❌ An error occurred while getting cleanup status")