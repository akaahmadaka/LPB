from config import ADMINS
from database import get_db_session
from models.user_model import User
import logging

# Set up logging
logger = logging.getLogger(__name__)

def handle_start(message, bot):
    """Handle the /start command with referral system."""
    user_id = message.from_user.id
    
    # Extract referral ID from /start command
    args = message.text.split()
    referral_id = None
    if len(args) > 1:
        try:
            referral_id = int(args[1])
            logger.info(f"Referral ID found: {referral_id}")
        except ValueError:
            logger.warning(f"Invalid referral format: {args[1]}")
            referral_id = None
    
    with get_db_session() as session:
        try:
            # Check if user exists
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                # Create new user
                user = User(user_id=user_id, credits=5, referred_by=referral_id)
                session.add(user)
                session.flush()  # Ensure user is saved before handling referral
                
                # Handle referral bonus if valid referral_id exists
                if referral_id and referral_id != user_id:  # Prevent self-referral
                    referrer = session.query(User).filter(User.user_id == referral_id).first()
                    if referrer:
                        logger.info(f"Adding bonus credits to referrer {referral_id}")
                        referrer.credits += 3
                        session.flush()
                
                session.commit()
                logger.info(f"New user created: {user_id}, referred by: {referral_id}")
                bot.reply_to(message, "Welcome! You have 5 credits to start with.")
            else:
                credits_msg = f"You have {user.credits} credits remaining."
                bot.reply_to(message, f"Welcome back! {credits_msg}")
                
        except Exception as e:
            logger.error(f"Error in start handler: {str(e)}")
            session.rollback()
            bot.reply_to(message, "An error occurred. Please try again.")
            raise