from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_session, get_link_by_id, get_all_links
from utils.logger import logger
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import format_timestamp
from config import ADMINS
from models.user_model import User

def register_link_handlers(bot):
    """Register link-related handlers."""
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_link_'))
    def handle_link_view(call: CallbackQuery):
        """Handle link view callback when title is clicked."""
        try:
            # Extract link_id
            _, _, link_id = call.data.split('_')
            link_id = int(link_id)
            user_id = call.from_user.id
            
            with get_db_session() as session:
                # Skip credit check for admins
                if user_id not in ADMINS:
                    user = session.query(User).filter(User.user_id == user_id).first()
                    if not user:
                        # Create user if doesn't exist
                        user = User(user_id=user_id, credits=5)
                        session.add(user)
                    
                    # Check credits
                    if user.credits <= 0:
                        bot_username = bot.get_me().username
                        referral_link = f"t.me/{bot_username}?start={user_id}"
                        message_text = (
                            "❌ You don't have enough credits!\n\n"
                            "To earn more credits:\n"
                            "- Invite friends using your referral link\n"
                            "- Get 3 credits for each new user\n\n"
                            f"Your referral link: {referral_link}"
                        )
                        bot.answer_callback_query(call.id, "No credits left!")
                        bot.edit_message_text(
                            message_text,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id
                        )
                        return
                    
                    # Deduct credit
                    user.credits -= 1
                
                link = get_link_by_id(link_id, session)
                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return
                
                # Track unique clicks
                if not link.has_user_clicked(user_id):
                    link.add_click(user_id)
                    session.commit()
                
                # Create inline keyboard for voting, visiting, and back button
                keyboard = InlineKeyboardMarkup()
                
                # If user hasn't voted, show vote buttons
                if not link.has_voter_voted(user_id):
                    keyboard.row(
                        InlineKeyboardButton(f"👍 {link.upvotes}", callback_data=f"upvote_{link_id}"),
                        InlineKeyboardButton(f"👎 {link.downvotes}", callback_data=f"downvote_{link_id}")
                    )
                else:
                    # Show disabled buttons if user has voted
                    keyboard.row(
                        InlineKeyboardButton(f"👍 {link.upvotes} ", callback_data="already_voted"),
                        InlineKeyboardButton(f"👎 {link.downvotes} ", callback_data="already_voted")
                    )
                
                keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=link.url))
                keyboard.add(InlineKeyboardButton("⬅️ Back to List", callback_data="back_to_list"))
                
                # Format link details
               # vote_status = "✓ You voted" if link.has_voter_voted(user_id) else "Not voted yet"
                
                link_text = (
                    f"*{link.title}*\n\n"
                    f"🔗 {link.url}\n"
                    f"👀 {link.clicks} views\n"
                   # f"Score: {link.score:.1f}\n"
                   # f"{vote_status}\n"
                   # f"⏰ {format_timestamp(link.submit_date)}"
                )
                
                # Edit the existing message instead of sending a new one
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=link_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                # Answer callback query
                bot.answer_callback_query(call.id)
                
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Invalid link data!")
        except SQLAlchemyError as e:
            logger.error(f"Database error in link view handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Database error!")
        except Exception as e:
            logger.error(f"Error in link view handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_list")
    def handle_back_to_list(call: CallbackQuery):
        """Handle back button to return to the links list."""
        try:
            voter_id = call.from_user.id
            
            with get_db_session() as session:
                links = get_all_links(session)
                
                if not links:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="No links have been shared yet."
                    )
                    return
                
                # Create inline keyboard with titles as buttons
                inline_keyboard = InlineKeyboardMarkup(row_width=1)  # One button per row
                for link in links:
                    # Add vote indicator if voter voted on this link
                   # vote_indicator = "✓ " if link.has_voter_voted(voter_id) else ""
                    
                    inline_keyboard.add(
                        InlineKeyboardButton(
                            text=f"{link.title} ",
                            callback_data=f"view_link_{link.id}"
                        )
                    )
                
                # Edit message to show list again
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📋 *Shared Links*\nClick on a title to view details:",
                    parse_mode="Markdown",
                    reply_markup=inline_keyboard
                )
                
                # Answer callback query
                bot.answer_callback_query(call.id)
                
        except Exception as e:
            logger.error(f"Error in back to list handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('upvote_', 'downvote_')))
    def handle_vote(call: CallbackQuery):
        """Handle upvote and downvote callbacks."""
        try:
            # Extract vote type and link_id
            action, link_id = call.data.split('_')
            link_id = int(link_id)
            voter_id = call.from_user.id
            
            with get_db_session() as session:
                link = get_link_by_id(link_id, session)
                
                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return

                # Strict check if voter has already voted
                if link.has_voter_voted(voter_id):
                    bot.answer_callback_query(call.id, "❌ You've already voted on this link!", show_alert=True)
                    return
                
                # Add vote
                is_upvote = (action == 'upvote')
                success = link.add_vote(voter_id, is_upvote)
                
                if not success:
                    bot.answer_callback_query(call.id, "❌ You've already voted on this link!", show_alert=True)
                    return
                
                # Explicitly flush and refresh the session
                session.flush()
                session.refresh(link)
                session.commit()
                
                logger.info(f"Vote processed - Link: {link_id}, Voter: {voter_id}, Vote type: {action}")
                logger.info(f"Current voter_ids: {link.voter_ids}")
                
                vote_msg = "👍 Upvoted!" if is_upvote else "👎 Downvoted!"
                
                # Update message
                keyboard = InlineKeyboardMarkup()
                
                # If user hasn't voted, show vote buttons
                if not link.has_voter_voted(voter_id):
                    keyboard.row(
                        InlineKeyboardButton(f"👍 {link.upvotes}", callback_data=f"upvote_{link_id}"),
                        InlineKeyboardButton(f"👎 {link.downvotes}", callback_data=f"downvote_{link_id}")
                    )
                else:
                    # Show disabled buttons if user has voted
                    keyboard.row(
                        InlineKeyboardButton(f"👍 {link.upvotes} ", callback_data="already_voted"),
                        InlineKeyboardButton(f"👎 {link.downvotes} ", callback_data="already_voted")
                    )
                
                keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=link.url))
                keyboard.add(InlineKeyboardButton("⬅️ Back to List", callback_data="back_to_list"))
                
                # Update link details message
                #vote_status = "✓ You voted" if link.has_voter_voted(voter_id) else "Not voted yet"
                
                link_text = (
                    f"*{link.title}*\n\n"
                    f"🔗 {link.url}\n"
                    f"👀 {link.clicks} views\n"
                    #f"Score: {link.score:.1f}\n"
                    #f"{vote_status}\n"
                    #f"⏰ {format_timestamp(link.submit_date)}"
                )
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=link_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                # Answer callback query
                bot.answer_callback_query(call.id, vote_msg)
                
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Invalid vote data!")
        except SQLAlchemyError as e:
            logger.error(f"Database error in vote handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Database error!")
        except Exception as e:
            logger.error(f"Error in vote handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")

    @bot.callback_query_handler(func=lambda call: call.data == "already_voted")
    def handle_already_voted(call: CallbackQuery):
        """Handle clicks on already voted buttons."""
        bot.answer_callback_query(call.id, "You have already voted on this link!", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('visit_'))
    def handle_visit(call: CallbackQuery):
        """Handle link visit callbacks."""
        try:
            # Extract link_id
            _, link_id = call.data.split('_')
            link_id = int(link_id)
            
            with get_db_session() as session:
                link = get_link_by_id(link_id, session)
                
                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return
                
                # Increment click counter
                link.clicks += 1
                session.commit()
                
                # Answer callback query with link URL
                bot.answer_callback_query(
                    call.id,
                    "🔗 Opening link...",
                    url=link.url
                )
                
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Invalid link data!")
        except SQLAlchemyError as e:
            logger.error(f"Database error in visit handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Database error!")
        except Exception as e:
            logger.error(f"Error in visit handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")