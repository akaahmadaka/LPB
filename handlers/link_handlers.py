from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_session, get_link_by_id
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import format_timestamp

logger = logging.getLogger(__name__)

def register_link_handlers(bot):
    """Register link-related handlers."""
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_link_'))
    def handle_link_view(call: CallbackQuery):
        """Handle link view callback when title is clicked."""
        try:
            # Extract link_id
            _, _, link_id = call.data.split('_')
            link_id = int(link_id)
            
            with get_db_session() as session:
                link = get_link_by_id(session, link_id)
                
                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return
                
                # Create inline keyboard for voting and visiting
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton(f"👍 {link.upvotes}", callback_data=f"upvote_{link_id}"),
                    InlineKeyboardButton(f"👎 {link.downvotes}", callback_data=f"downvote_{link_id}")
                )
                keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=link.url))
                
                # Format link details
                link_text = (
                    f"*{link.title}*\n\n"
                    f"🔗 {link.url}\n"
                    f"👀 {link.clicks} views\n"
                    f"⏰ {format_timestamp(link.submit_date)}"
                )
                
                # Send new message with link details
                bot.send_message(
                    call.message.chat.id,
                    link_text,
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('upvote_', 'downvote_')))
    def handle_vote(call: CallbackQuery):
        """Handle upvote and downvote callbacks."""
        try:
            # Extract vote type and link_id
            action, link_id = call.data.split('_')
            link_id = int(link_id)
            
            with get_db_session() as session:
                link = get_link_by_id(session, link_id)
                
                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return
                
                # Update vote count
                if action == 'upvote':
                    link.upvotes += 1
                    vote_msg = "👍 Upvoted!"
                else:
                    link.downvotes += 1
                    vote_msg = "👎 Downvoted!"
                
                # Update score
                link.score = link.upvotes - link.downvotes
                
                session.commit()
                
                # Update inline keyboard
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton(f"👍 {link.upvotes}", callback_data=f"upvote_{link_id}"),
                    InlineKeyboardButton(f"👎 {link.downvotes}", callback_data=f"downvote_{link_id}")
                )
                keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=link.url))
                
                # Answer callback query
                bot.answer_callback_query(call.id, vote_msg)
                
                # Update message
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Error updating message markup: {str(e)}")
                
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Invalid vote data!")
        except SQLAlchemyError as e:
            logger.error(f"Database error in vote handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ Database error!")
        except Exception as e:
            logger.error(f"Error in vote handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('visit_'))
    def handle_visit(call: CallbackQuery):
        """Handle link visit callbacks."""
        try:
            # Extract link_id
            _, link_id = call.data.split('_')
            link_id = int(link_id)
            
            with get_db_session() as session:
                link = get_link_by_id(session, link_id)
                
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