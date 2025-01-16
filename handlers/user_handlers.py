from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ForceReply,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database import get_user_by_id, save_user, get_all_links, get_db_session
from handlers.validation import is_valid_title, is_valid_group_link
from models.link_model import Link
from models.user_model import User
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import format_timestamp
from config import ADMINS
from handlers.start_handler import handle_start  # Import the main start handler

logger = logging.getLogger(__name__)

def register_user_handlers(bot):
    """Register user-related command handlers."""
    
    @bot.message_handler(commands=['start'])
    def start_command(message: Message):
        """Forward start command to main handler"""
        handle_start(message, bot)

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
                KeyboardButton("🔗 View Links"),
                KeyboardButton("💎 Check Credits")
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
                KeyboardButton("🔗 View Links"),
                KeyboardButton("💎 Check Credits")
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
                KeyboardButton("🔗 View Links"),
                KeyboardButton("💎 Check Credits")
            )
            bot.reply_to(
                message, 
                "Sorry, an error occurred while fetching links.",
                reply_markup=keyboard
            )

    @bot.message_handler(func=lambda message: message.text == "💎 Check Credits")
    def handle_check_credits(message):
        """Handle Check Credits button click."""
        try:
            user_id = message.from_user.id
            
            with get_db_session() as session:
                user = session.query(User).filter(User.user_id == user_id).first()
                if not user:
                    # Create user if doesn't exist
                    user = User(user_id=user_id, credits=5)
                    session.add(user)
                    session.commit()
                
                bot_username = bot.get_me().username
                referral_link = f"t.me/{bot_username}?start={user_id}"
                message_text = (
                    f"💎 You have {user.credits} credits\n\n"
                    "To earn more credits:\n"
                    "- Invite friends using your referral link\n"
                    "- Get 3 credits for each new user\n\n"
                    f"Your referral link: {referral_link}"
                )
                
                # Create keyboard for consistent UI
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add(
                    KeyboardButton("📝 Add Link"),
                    KeyboardButton("🔗 View Links"),
                    KeyboardButton("💎 Check Credits")
                )
                
                bot.reply_to(
                    message,
                    message_text,
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error in check credits handler: {str(e)}")
            bot.reply_to(message, "Sorry, an error occurred while checking credits.")

    # Register all handlers
    bot.register_next_step_handler_by_chat_id = getattr(bot, 'register_next_step_handler_by_chat_id', {})
    bot.user_data = getattr(bot, 'user_data', {})