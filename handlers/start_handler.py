from config import ADMINS
from database import get_db_session
from models.user_model import User

def handle_start(message, bot):
    """Handle the /start command with referral system."""
    user_id = message.from_user.id
    
    # Check if start parameter contains referral
    args = message.text.split()
    referral_id = None
    if len(args) > 1:
        try:
            referral_id = int(args[1])
        except ValueError:
            pass
    
    with get_db_session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            # New user
            user = User(
                user_id=user_id,
                credits=5,
                referred_by=referral_id
            )
            session.add(user)
            
            # If referred by someone and referrer exists, add credits
            if referral_id and referral_id != user_id:  # Prevent self-referral
                referrer = session.query(User).filter(User.user_id == referral_id).first()
                if referrer:
                    referrer.credits += 3
                    session.commit()
            
            session.commit()
            bot.reply_to(message, "Welcome! You have 5 credits to start with.")
        else:
            credits_msg = f"You have {user.credits} credits remaining."
            bot.reply_to(message, f"Welcome back! {credits_msg}")