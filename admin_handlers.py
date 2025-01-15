# Import required modules
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import delete_link
from utils.helpers import is_admin

def register_admin_handlers(bot):
    # Handler for /del command
    @bot.message_handler(commands=["del"])
def handle_del_command(message):
    user = get_user_by_id(message.from_user.id)
    if not user or user.role != "admin":
        bot.reply_to(message, "You are not authorized to use this command.")
        return

        # Prompt the admin to tap on a link to delete it
        bot.reply_to(message, "Tap on the link you want to delete.")

    # Handler for "Delete" button callback
    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
    def handle_delete_button(call):
        # Check if the user is an admin
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "You are not authorized to delete links.")
            return

        # Extract the link ID from the callback data
        link_id = int(call.data.split("_")[1])

        # Delete the link from the database
        delete_link(link_id)

        # Notify the admin
        bot.answer_callback_query(call.id, "Link deleted successfully.")

        # Update the message to indicate the link has been deleted
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="This link has been deleted."
        )