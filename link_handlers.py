# Import required modules
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import save_link, get_all_links, increment_clicks, increment_upvotes, increment_downvotes
from utils.ranking import calculate_link_score
from utils.helpers import is_valid_group_link
from datetime import datetime
from utils.ranking import calculate_link_score

def register_link_handlers(bot):
    # Handler for /start command
    @bot.message_handler(commands=["start"])
    def handle_start(message):
        bot.reply_to(message, "Welcome! Use /share to submit a link or /get to browse links.")

    # Handler for /share command
    @bot.message_handler(commands=["share"])
    def handle_share(message):
        bot.reply_to(message, "Please send the link and title in the format: Title - URL")

    # Handler for link submission
    @bot.message_handler(func=lambda msg: "-" in msg.text)
def handle_link_submission(message):
    try:
        # Split the message into title and URL
        title, url = message.text.split(" - ", 1)
        url = url.strip()

        # Validate the link
        if not is_valid_group_link(url):
            bot.reply_to(message, "Invalid link. Please submit a valid Telegram group link.")
            return

        # Save the user if they don't already exist
        user = get_user_by_id(message.from_user.id)
        if not user:
            save_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )

        # Save the link to the database with the user ID
        save_link(title, url, message.from_user.id)
        bot.reply_to(message, "Link submitted successfully!")

    except Exception as e:
        bot.reply_to(message, "An error occurred. Please use the format: Title - URL")

    # Handler for /get command
    @bot.message_handler(commands=["get"])
def handle_get_links(message):
    # Fetch all links from the database
    links = get_all_links()

    # Sort links by score
    ranked_links = sorted(links, key=lambda x: calculate_link_score(x), reverse=True)

    # Create a list of buttons for the top 10 links
    keyboard = []
    for link in ranked_links[:10]:
        keyboard.append([InlineKeyboardButton(link.title, callback_data=f"link_{link.id}")])

    # Add a "Next" button for pagination
    keyboard.append([InlineKeyboardButton("Next ➡️", callback_data="next_page")])

    # Send the message with the links
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(message.chat.id, "Here are the links:", reply_markup=reply_markup)

    # Handler for link clicks
    @bot.callback_query_handler(func=lambda call: call.data.startswith("link_"))
    def handle_link_click(call):
        # Extract the link ID from the callback data
        link_id = int(call.data.split("_")[1])

        # Increment the click count for the link
        increment_clicks(link_id)

        # Fetch the link details from the database
        links = get_all_links()
        link = next((link for link in links if link.id == link_id), None)

        if not link:
            bot.answer_callback_query(call.id, "Link not found.")
            return

        # Create a message with the link details and voting buttons
        message_text = f"{link.title}\nLink: {link.url}\nUpvotes: {link.upvotes} | Downvotes: {link.downvotes}"
        keyboard = [
            [InlineKeyboardButton("👍 Upvote", callback_data=f"upvote_{link.id}")],
            [InlineKeyboardButton("👎 Downvote", callback_data=f"downvote_{link.id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the message
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=reply_markup
        )

    # Handler for upvotes
    @bot.callback_query_handler(func=lambda call: call.data.startswith("upvote_"))
    def handle_upvote(call):
        # Extract the link ID from the callback data
        link_id = int(call.data.split("_")[1])

        # Increment the upvote count for the link
        increment_upvotes(link_id)

        # Fetch the updated link details
        links = get_all_links()
        link = next((link for link in links if link.id == link_id), None)

        if not link:
            bot.answer_callback_query(call.id, "Link not found.")
            return

        # Update the message with the new upvote count
        message_text = f"{link.title}\nLink: {link.url}\nUpvotes: {link.upvotes} | Downvotes: {link.downvotes}"
        keyboard = [
            [InlineKeyboardButton("👍 Upvote", callback_data=f"upvote_{link.id}")],
            [InlineKeyboardButton("👎 Downvote", callback_data=f"downvote_{link.id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=reply_markup
        )

    # Handler for downvotes
    @bot.callback_query_handler(func=lambda call: call.data.startswith("downvote_"))
    def handle_downvote(call):
        # Extract the link ID from the callback data
        link_id = int(call.data.split("_")[1])

        # Increment the downvote count for the link
        increment_downvotes(link_id)

        # Fetch the updated link details
        links = get_all_links()
        link = next((link for link in links if link.id == link_id), None)

        if not link:
            bot.answer_callback_query(call.id, "Link not found.")
            return

        # Update the message with the new downvote count
        message_text = f"{link.title}\nLink: {link.url}\nUpvotes: {link.upvotes} | Downvotes: {link.downvotes}"
        keyboard = [
            [InlineKeyboardButton("👍 Upvote", callback_data=f"upvote_{link.id}")],
            [InlineKeyboardButton("👎 Downvote", callback_data=f"downvote_{link.id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=reply_markup
        )