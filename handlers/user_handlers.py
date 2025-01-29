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
from utils.logger import logger
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import format_timestamp, is_admin as is_admin_user
from config import ADMINS
from handlers.start_handler import handle_start
from datetime import datetime, timedelta

def create_links_keyboard(links, current_page=0, links_per_page=10):
    """Create paginated keyboard for links list."""
    total_links = len(links)
    total_pages = (total_links + links_per_page - 1) // links_per_page
    
    start_idx = current_page * links_per_page
    end_idx = min(start_idx + links_per_page, total_links)
    current_links = links[start_idx:end_idx]
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Add link buttons
    for link in current_links:
        keyboard.add(
            InlineKeyboardButton(
                text=f"📌 {link.title}",
                callback_data=f"view_link_{link.id}_{current_page}"  # Include current page
            )
        )
    
    # Add navigation buttons
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{current_page-1}")
        )
    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"page_{current_page+1}")
        )
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    return keyboard, total_pages

def check_active_link(user_id: int, session) -> tuple[bool, str]:
    """
    Check if user has an active link and calculate time remaining if they do.
    Admins are exempt from this check.
    
    Args:
        user_id (int): The user's Telegram ID
        session: The database session
        
    Returns:
        tuple[bool, str]: (has_active_link, message)
    """
    try:
        # First check if user is admin
        if is_admin_user(user_id):
            return False, ""  # Admins can always post
            
        # Get user's most recent link
        user_link = (
            session.query(Link)
            .filter(Link.user_id == user_id)
            .order_by(Link.submit_date.desc())
            .first()
        )
        
        if not user_link:
            return False, ""
            
        # Calculate time remaining
        current_time = datetime.utcnow()
        link_age = current_time - user_link.submit_date
        cleanup_days = 3  # Get this from your config
        time_remaining = timedelta(days=cleanup_days) - link_age
        
        # If link hasn't expired yet
        if time_remaining.total_seconds() > 0:
            hours = int(time_remaining.total_seconds() / 3600)
            minutes = int((time_remaining.total_seconds() % 3600) / 60)
            return True, (
                f"You already have an active link:\n"
                f"Title: {user_link.title}\n"
                f"Time remaining: {hours} hours and {minutes} minutes\n\n"
                f"Regular users can only have one active link at a time."
            )
            
        return False, ""
        
    except Exception as e:
        logger.error(f"Error checking active link: {str(e)}")
        return False, "Error checking link status"

def register_user_handlers(bot):
    """Register user-related command handlers."""
    
    @bot.message_handler(commands=['start'])
    def start_command(message: Message):
        """Forward start command to main handler"""
        handle_start(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📝 Add Your Link")
    def handle_add_button(message):
        """Handle Add Link button click."""
        try:
            user_id = message.from_user.id
            is_admin = is_admin_user(user_id)
            
            with get_db_session() as session:
                # Check if user has an active link (skipped for admins)
                if not is_admin:
                    has_active_link, time_message = check_active_link(user_id, session)
                    
                    if has_active_link:
                        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                        keyboard.add(
                            KeyboardButton("📝 Add Your Link"),
                            KeyboardButton("🔗 View Links"),
                            KeyboardButton("💎 Check Credits")
                        )
                        bot.reply_to(message, time_message, reply_markup=keyboard)
                        return
                
                # Send warning message first
                warning_message = (
                    "⚠️DISCLAIMER⚠️\n"
                    "We strictly prohibit and do not endorse any illegal activities, including but not limited to "
                    "hacking, spamming, pornography, or any other harmful material. Violations of these restrictions "
                    "will result in immediate and strict action.\n\n"
                    "Please verify the title and link before sending, as they cannot be changed after submission."
                )
                bot.send_message(message.chat.id, warning_message)
                
                # Wait a short moment before sending the prompt
                # Use force reply to ensure we get a response from the correct user
                prompt = "Please send the title for your link:"
                if is_admin:
                    prompt = "[Admin] " + prompt
                    
                # Important: Register the next step handler after sending the message
                sent_msg = bot.send_message(
                    message.chat.id,
                    prompt,
                    reply_markup=ForceReply()
                )
                bot.register_next_step_handler(sent_msg, process_title)
                
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
                KeyboardButton("📝 Add Your Link"),
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
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                KeyboardButton("📝 Add Your Link"),
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
                
                # Use the new pagination system
                inline_keyboard, total_pages = create_links_keyboard(links)
                
                bot.reply_to(
                    message,
                    f"📋 *Shared Links*\nClick on a title to view details:\nPage 1 of {total_pages}",
                    parse_mode="Markdown",
                    reply_markup=inline_keyboard
                )
            
        except Exception as e:
            logger.error(f"Error in view links handler: {str(e)}")
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(
                KeyboardButton("📝 Add Your Link"),
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
                    KeyboardButton("📝 Add Your Link"),
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