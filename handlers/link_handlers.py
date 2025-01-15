# Import required modules
import logging
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_session, Link
from sqlalchemy.exc import SQLAlchemyError
from handlers.validation import is_valid_title, is_valid_group_link
from utils.helpers import format_timestamp

# Set up logging
logger = logging.getLogger(__name__)

def register_link_handlers(bot):
    """
    Register all link-related command handlers.
    """
    
    @bot.message_handler(commands=['add'])
    def handle_add_link(message: Message):
        """Handle /add command to add new links."""
        try:
            # Parse command arguments
            args = message.text.split(maxsplit=2)
            if len(args) < 3:
                bot.reply_to(message, 
                    "Please use the format: /add <title> <link>\n"
                    "Example: /add My Group https://t.me/mygroup"
                )
                return

            title = args[1]
            url = args[2]

            # Validate input
            title_valid, title_error = is_valid_title(title)
            if not title_valid:
                bot.reply_to(message, f"Invalid title: {title_error}")
                return

            url_valid, url_error = is_valid_group_link(url)
            if not url_valid:
                bot.reply_to(message, f"Invalid link: {url_error}")
                return

            # Save link to database
            with get_db_session() as session:
                try:
                    new_link = Link(
                        title=title,
                        url=url,
                        user_id=message.from_user.id
                    )
                    session.add(new_link)
                    session.commit()

                    # Create confirmation message with inline keyboard
                    keyboard = InlineKeyboardMarkup()
                    keyboard.row(
                        InlineKeyboardButton("👍 Upvote", callback_data=f"upvote_{new_link.id}"),
                        InlineKeyboardButton("👎 Downvote", callback_data=f"downvote_{new_link.id}")
                    )
                    keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=new_link.url))

                    bot.reply_to(
                        message,
                        f"✅ Link added successfully!\n\n"
                        f"*Title:* {title}\n"
                        f"*Link:* {url}\n"
                        f"*Added by:* @{message.from_user.username or 'Anonymous'}\n"
                        f"*Time:* {format_timestamp(new_link.submit_date)}",  # Changed from created_at to submit_date
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    logger.info(f"New link added: {title} by user {message.from_user.id}")

                except SQLAlchemyError as e:
                    logger.error(f"Database error while adding link: {str(e)}")
                    bot.reply_to(message, "Error saving link. Please try again later.")
                    return

        except Exception as e:
            logger.error(f"Error in handle_add_link: {str(e)}")
            bot.reply_to(message, "An error occurred. Please try again later.")

    @bot.message_handler(commands=['links'])
    def handle_list_links(message: Message):
        """Handle /links command to list all shared links."""
        try:
            with get_db_session() as session:
                links = session.query(Link).order_by(Link.submit_date.desc()).limit(10).all()

                if not links:
                    bot.reply_to(message, "No links have been shared yet.")
                    return

                response = "🔗 *Recently Shared Links:*\n\n"
                for link in links:
                    response += (
                        f"*{link.title}*\n"
                        f"Posted by: @{link.user.username or 'Anonymous'}\n"
                        f"Time: {format_timestamp(link.submit_date)}\n"  # Changed from created_at to submit_date
                        f"Upvotes: {link.upvotes} | Downvotes: {link.downvotes}\n"
                        f"[Visit Link]({link.url})\n\n"
                    )

                bot.reply_to(message, response, parse_mode="Markdown")
                logger.info(f"Links list displayed for user {message.from_user.id}")

        except Exception as e:
            logger.error(f"Error in handle_list_links: {str(e)}")
            bot.reply_to(message, "An error occurred while fetching links. Please try again later.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('upvote_', 'downvote_')))
    def handle_vote(call):
        """Handle upvote/downvote callbacks."""
        try:
            action, link_id = call.data.split('_')
            link_id = int(link_id)

            with get_db_session() as session:
                link = session.query(Link).get(link_id)
                if not link:
                    bot.answer_callback_query(call.id, "Link not found!")
                    return

                if action == "upvote":
                    link.upvotes += 1
                    message = "👍 Upvote recorded!"
                else:
                    link.downvotes += 1
                    message = "👎 Downvote recorded!"

                session.commit()
                bot.answer_callback_query(call.id, message)
                logger.info(f"Vote recorded for link {link_id}: {action}")

        except Exception as e:
            logger.error(f"Error in handle_vote: {str(e)}")
            bot.answer_callback_query(call.id, "Error processing vote. Please try again.")