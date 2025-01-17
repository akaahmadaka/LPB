from config import ADMINS
from utils.logger import logger
from database import get_db_session
from models.user_model import User
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from utils.logger import logger


def handle_start(message, bot):
    """Handle the /start command with referral system."""
    user_id = message.from_user.id
    logger.info(f"Start command received from user {user_id}")
    
    # Create keyboard with buttons
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("📝 Add Your Link"),
        KeyboardButton("🔗 View Links"),
        KeyboardButton("💎 Check Credits")
    )
    
    # Enhanced referral ID extraction
    referral_id = None
    try:
        # Split the message text and get everything after /start
        command_parts = message.text.strip().split()
        logger.info(f"Command parts: {command_parts}")
        
        if len(command_parts) > 1:
            referral_id = int(command_parts[1])
            logger.info(f"Successfully extracted referral_id: {referral_id}")
    except Exception as e:
        logger.error(f"Error extracting referral ID: {str(e)}")
        referral_id = None

    with get_db_session() as session:
        try:
            # Check if user exists
            user = session.query(User).filter(User.user_id == user_id).first()
            logger.info(f"Existing user check: {'Found' if user else 'Not found'}")
            
            # Handle new user registration
            if not user:
                logger.info(f"Creating new user with ID {user_id}, referred by {referral_id}")
                
                # Verify referrer exists and is different from new user
                referrer = None
                if referral_id and referral_id != user_id:
                    referrer = session.query(User).filter(User.user_id == referral_id).first()
                    logger.info(f"Referrer found: {referrer is not None}")
                
                # Create new user with referral info
                user = User(
                    user_id=user_id,
                    credits=5,
                    referred_by=referral_id if referrer else None
                )
                session.add(user)
                session.flush()
                logger.info(f"New user created with referred_by: {user.referred_by}")
                
                # Handle referral rewards
                if referrer:
                    old_credits = referrer.credits
                    referrer.credits += 3  # Add 3 credits to referrer
                    session.flush()  # Ensure credits are updated
                    logger.info(f"Updated referrer (ID: {referral_id}) credits: {old_credits} -> {referrer.credits}")
                    
                    # Prepare welcome messages
                    welcome_msg = (
                        f"Welcome! 👋\n\n"
                        f"Here you can find group links Or YOU CAN ALSO SHARE YOUR GROUP LINK\n"
                        f"Use the buttons below to add or view links!"
                    )
                    
                    # Notify referrer about successful referral
                    try:
                        bot.send_message(
                            referral_id,
                            f"🎉 1 New user joined using your referral!\n"
                            f"You received 3 credits!\n"
                            f"Your new balance: {referrer.credits} credits"
                        )
                        logger.info(f"Referral notification sent to user {referral_id}")
                    except Exception as e:
                        logger.error(f"Failed to send referrer notification: {str(e)}")
                else:
                    welcome_msg = (
                        f"Welcome! 👋\n\n"
                        f"Here you can find group links Or YOU CAN ALSO SHARE YOUR GROUP LINK\n"
                        f"Use the buttons below to add or view links!"
                    )
                
                session.commit()
                logger.info("New user registration completed successfully")
                bot.reply_to(message, welcome_msg, reply_markup=keyboard)
                
            else:
                logger.info("Processing existing user...")
                # Generate referral link for existing user
                bot_username = bot.get_me().username
                referral_link = f"https://t.me/{bot_username}?start={user_id}"
                
                response_msg = (
                    f"Welcome back! 👋\n\n"
                    f"Here you can find group links Or YOU CAN ALSO SHARE YOUR GROUP LINK\n\n"
                    f"Use the buttons below to add or view links!"
                )
                bot.reply_to(message, response_msg, reply_markup=keyboard)
                logger.info("Sent welcome back message to existing user")

        except Exception as e:
            logger.error(f"Critical error in start handler: {str(e)}")
            session.rollback()
            bot.reply_to(message, "An error occurred. Please try again.")
            raise

    logger.info("Start handler completed successfully")