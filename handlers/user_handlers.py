# Import required modules
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_user_by_id,
    get_all_links,
    save_user,
    update_user_role
)
from utils.helpers import rate_limit
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def register_user_handlers(bot):
    """
    Register all user-related command handlers.
    """
    
    @bot.message_handler(commands=["profile"])
    @rate_limit(30)  # Rate limit: 30 seconds between requests
    def handle_profile(message):
        """
        Handle /profile command - shows user profile and their submitted links
        """
        try:
            user_id = message.from_user.id
            user = get_user_by_id(user_id)
            
            if not user:
                # Create new user if not exists
                try:
                    user = save_user(
                        user_id=user_id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name
                    )
                    logger.info(f"New user registered: {user_id}")
                except Exception as e:
                    logger.error(f"Error creating new user: {str(e)}")
                    bot.reply_to(message, "An error occurred while creating your profile. Please try again later.")
                    return

            # Fetch links submitted by the user
            try:
                links = get_all_links()
                user_links = [link for link in links if link.user_id == user.user_id]
                
                # Calculate user statistics
                total_upvotes = sum(link.upvotes for link in user_links)
                total_clicks = sum(link.clicks for link in user_links)
                
                # Create profile message
                profile_text = (
                    f"👤 *User Profile*\n\n"
                    f"*Name:* {user.first_name or 'Not set'} {user.last_name or ''}\n"
                    f"*Username:* @{user.username or 'Not set'}\n"
                    f"*Role:* {user.role}\n"
                    f"*Member since:* {user.registration_time.strftime('%Y-%m-%d')}\n\n"
                    f"📊 *Statistics*\n"
                    f"Links submitted: {len(user_links)}\n"
                    f"Total upvotes: {total_upvotes}\n"
                    f"Total clicks: {total_clicks}\n"
                )

                # Create keyboard with user's links
                keyboard = InlineKeyboardMarkup()
                if user_links:
                    profile_text += "\n🔗 *Your Recent Links:*\n"
                    for link in user_links[:5]:  # Show only 5 most recent links
                        btn = InlineKeyboardButton(
                            link.title[:30] + "..." if len(link.title) > 30 else link.title,
                            callback_data=f"link_{link.id}"
                        )
                        keyboard.add(btn)
                
                # Send profile with markdown formatting
                bot.reply_to(
                    message,
                    profile_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard if user_links else None
                )
                logger.info(f"Profile displayed for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error fetching user links: {str(e)}")
                bot.reply_to(message, "An error occurred while fetching your profile data. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error in profile handler: {str(e)}")
            bot.reply_to(message, "An error occurred. Please try again later.")

    @bot.message_handler(commands=["settings"])
    @rate_limit(10)
    def handle_settings(message):
        """
        Handle /settings command - shows user settings
        """
        try:
            user = get_user_by_id(message.from_user.id)
            if not user:
                bot.reply_to(message, "Please use /profile first to create your profile.")
                return

            # Create settings keyboard
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("Update Profile", callback_data="settings_profile"),
                InlineKeyboardButton("Notifications", callback_data="settings_notifications")
            )

            bot.reply_to(
                message,
                "⚙️ *Settings*\nChoose what you'd like to modify:",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            logger.info(f"Settings menu displayed for user {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Error in settings handler: {str(e)}")
            bot.reply_to(message, "An error occurred. Please try again later.")

    # Callback handler for settings menu
    @bot.callback_query_handler(func=lambda call: call.data.startswith("settings_"))
    def handle_settings_callback(call):
        """
        Handle settings menu callbacks
        """
        try:
            setting_type = call.data.split("_")[1]
            
            if setting_type == "profile":
                bot.answer_callback_query(
                    call.id,
                    "Profile settings will be available soon!"
                )
            elif setting_type == "notifications":
                bot.answer_callback_query(
                    call.id,
                    "Notification settings will be available soon!"
                )
                
            logger.info(f"Settings callback handled for user {call.from_user.id}: {setting_type}")
            
        except Exception as e:
            logger.error(f"Error in settings callback handler: {str(e)}")
            bot.answer_callback_query(call.id, "An error occurred. Please try again.")