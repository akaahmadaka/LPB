# Import required modules
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import delete_link, get_user_by_id
from utils.helpers import is_admin

# Set up logging
logger = logging.getLogger(__name__)

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
            user = get_user_by_id(message.from_user.id)
            if not user or user.role != "admin":
                bot.reply_to(message, "You are not authorized to use this command.")
                logger.warning(f"Unauthorized delete attempt by user {message.from_user.id}")
                return

            # Prompt the admin to tap on a link to delete it
            bot.reply_to(message, "Tap on the link you want to delete.")
            logger.info(f"Delete command initiated by admin {message.from_user.id}")

        except Exception as e:
            logger.error(f"Error in delete command: {str(e)}")
            bot.reply_to(message, "An error occurred. Please try again later.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
    def handle_delete_button(call):
        """
        Handle the deletion of links when admin clicks the delete button.
        """
        try:
            # Check if the user is an admin
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "You are not authorized to delete links.")
                logger.warning(f"Unauthorized delete attempt by user {call.from_user.id}")
                return

            # Extract the link ID from the callback data
            link_id = int(call.data.split("_")[1])

            # Delete the link from the database
            delete_link(link_id)
            logger.info(f"Link {link_id} deleted by admin {call.from_user.id}")

            # Notify the admin
            bot.answer_callback_query(call.id, "Link deleted successfully.")

            # Update the message to indicate the link has been deleted
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="This link has been deleted."
            )

        except Exception as e:
            logger.error(f"Error in delete button handler: {str(e)}")
            bot.answer_callback_query(call.id, "An error occurred while deleting the link.")