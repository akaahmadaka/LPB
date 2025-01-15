from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, ForceReply
from database import get_user_by_id, save_user, get_all_links, get_db_session
from handlers.validation import is_valid_title, is_valid_group_link
from models.link_model import Link
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import format_timestamp

logger = logging.getLogger(__name__)

def register_user_handlers(bot):
    """Register user-related command handlers."""
    
    @bot.message_handler(commands=['start'])
    def handle_start(message: Message):
        """Handle /start command with buttons."""
        try:
            user_id = message.from_user.id
            user = get_user_by_id(user_id)
            
            if not user:
                user = save_user(user_id)
            
            # Create keyboard with two buttons
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                KeyboardButton("📝 Add Link"),
                KeyboardButton("🔗 View Links")
            )
            
            welcome_message = "Welcome! 👋\n\nI'm your Link Posting Bot. Use the buttons below to add or view links."
            
            bot.reply_to(message, welcome_message, reply_markup=keyboard)
            logger.info(f"Start command handled for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in start handler: {str(e)}")
            bot.reply_to(message, "Sorry, an error occurred. Please try again.")

    @bot.message_handler(func=lambda message: message.text == "📝 Add Link")
    def handle_add_button(message):
        """Handle Add Link button click."""
        try:
            # Prompt for title
            msg = bot.reply_to(message, "Please send the title for your link:", reply_markup=ForceReply())
            # Register the next step handler
            bot.register_next_step_handler(msg, process_title)
        except Exception as e:
            logger.error(f"Error in add button handler: {str(e)}")
            bot.reply_to(message, "Sorry, an error occurred. Please try again.")

    def process_title(message):
        """Process the title and ask for the link."""
        try:
            title = message.text
            
            # Validate title
            title_valid, title_error = is_valid_title(title)
            if not title_valid:
                bot.reply_to(message, f"Invalid title: {title_error}")
                return

            # Store title temporarily
            bot.user_data = getattr(bot, 'user_data', {})
            bot.user_data[message.from_user.id] = {'title': title}
            
            # Ask for link
            msg = bot.reply_to(message, "Great! Now please send the link:", reply_markup=ForceReply())
            bot.register_next_step_handler(msg, process_link)
        except Exception as e:
            logger.error(f"Error processing title: {str(e)}")
            bot.reply_to(message, "Sorry, an error occurred. Please try again.")

    def process_link(message):
        """Process the link and save to database."""
        try:
            url = message.text
            user_id = message.from_user.id
            
            # Validate link
            url_valid, url_error = is_valid_group_link(url)
            if not url_valid:
                bot.reply_to(message, f"Invalid link: {url_error}")
                return

            # Get stored title
            stored_data = bot.user_data.get(user_id, {})
            title = stored_data.get('title')
            
            if not title:
                bot.reply_to(message, "Sorry, something went wrong. Please try again.")
                return

            submit_time = None  # We'll store this for the message

            # Save link to database
            with get_db_session() as session:
                new_link = Link(
                    title=title,
                    url=url,
                    user_id=user_id
                )
                session.add(new_link)
                session.flush()  # This will populate the submit_date
                submit_time = new_link.submit_date  # Store it before committing
                session.commit()

            # Clear stored data
            bot.user_data.pop(user_id, None)
            
            # Send success message with keyboard
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                KeyboardButton("📝 Add Link"),
                KeyboardButton("🔗 View Links")
            )
            
            bot.reply_to(
                message,
                f"✅ Link added successfully!\n\n"
                f"*Title:* {title}\n"
                f"*Link:* {url}\n"
                f"*Time:* {format_timestamp(submit_time)}",  # Use the stored time
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error processing link: {str(e)}")
            bot.reply_to(message, "Sorry, an error occurred. Please try again.")

    @bot.message_handler(func=lambda message: message.text == "🔗 View Links")
    def handle_view_links(message):
        """Handle View Links button click."""
        try:
            # Create keyboard for consistent UI
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                KeyboardButton("📝 Add Link"),
                KeyboardButton("🔗 View Links")
            )

            with get_db_session() as session:
                links = get_all_links(session)
                
                if not links:
                    bot.reply_to(
                        message, 
                        "No links have been shared yet.", 
                        reply_markup=keyboard
                    )
                    return
                
                # Create inline keyboard with titles as buttons
                inline_keyboard = InlineKeyboardMarkup(row_width=1)  # One button per row
                for link in links:
                    inline_keyboard.add(
                        InlineKeyboardButton(
                            text=f"📌 {link.title}",
                            callback_data=f"view_link_{link.id}"
                        )
                    )
                
                # Send message with title buttons
                bot.reply_to(
                    message,
                    "📋 *Shared Links*\nClick on a title to view details:",
                    parse_mode="Markdown",
                    reply_markup=inline_keyboard
                )
            
        except Exception as e:
            logger.error(f"Error in view links handler: {str(e)}")
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                KeyboardButton("📝 Add Link"),
                KeyboardButton("🔗 View Links")
            )
            bot.reply_to(
                message, 
                "Sorry, an error occurred while fetching links.",
                reply_markup=keyboard
            )

    # Register all handlers
    bot.register_next_step_handler_by_chat_id = getattr(bot, 'register_next_step_handler_by_chat_id', {})
    bot.user_data = getattr(bot, 'user_data', {})