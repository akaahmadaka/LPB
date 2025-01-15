import logging
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.exc import SQLAlchemyError
from database import (
    get_db_session,
    get_link_by_id,
    save_link,
    get_all_links,
    get_user_by_id
)
from handlers.validation import is_valid_group_link, is_valid_title
from utils.helpers import rate_limit, format_timestamp
from models.link_model import Link

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def register_link_handlers(bot):
    """Register all link-related command handlers."""
    
    @bot.message_handler(commands=['add'])
    @rate_limit(30)
    def handle_add_link(message: Message):
        """Handle /add command to add new links."""
        try:
            # Check if user exists
            user = get_user_by_id(message.from_user.id)
            if not user:
                bot.reply_to(message, "Please use /start to register first.")
                return

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
                        f"*Time:* {format_timestamp(new_link.created_at)}",
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
    @rate_limit(10)
    def handle_list_links(message: Message):
        """Handle /links command to list all links."""
        try:
            page = 1
            per_page = 5
            
            # Get all links
            with get_db_session() as session:
                links = session.query(Link)\
                    .filter(Link.is_active == True)\
                    .order_by(Link.created_at.desc())\
                    .all()

                if not links:
                    bot.reply_to(message, "No links found.")
                    return

                # Create message with inline keyboard
                keyboard = InlineKeyboardMarkup()
                response = "*📋 Latest Links:*\n\n"

                for i, link in enumerate(links[:per_page], 1):
                    response += (
                        f"{i}. *{link.title}*\n"
                        f"🔗 [{link.url}]({link.url})\n"
                        f"👍 {link.upvotes} | 👎 {link.downvotes} | 👀 {link.clicks}\n"
                        f"Added: {format_timestamp(link.created_at)}\n\n"
                    )
                    keyboard.add(
                        InlineKeyboardButton(
                            f"Visit {link.title[:20]}...", 
                            url=link.url
                        )
                    )

                # Add navigation buttons if needed
                if len(links) > per_page:
                    keyboard.row(
                        InlineKeyboardButton("⬅️ Prev", callback_data=f"links_prev_{page}"),
                        InlineKeyboardButton("➡️ Next", callback_data=f"links_next_{page}")
                    )

                bot.reply_to(
                    message,
                    response,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
                logger.info(f"Links list displayed for user {message.from_user.id}")

        except Exception as e:
            logger.error(f"Error in handle_list_links: {str(e)}")
            bot.reply_to(message, "An error occurred. Please try again later.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('upvote_', 'downvote_')))
    def handle_vote(call):
        """Handle upvote/downvote callback queries."""
        try:
            action, link_id = call.data.split('_')
            link_id = int(link_id)

            with get_db_session() as session:
                link = session.query(Link).get(link_id)
                if not link:
                    bot.answer_callback_query(call.id, "Link not found!")
                    return

                if action == 'upvote':
                    link.increment_upvotes()
                    message = "👍 Upvoted!"
                else:
                    link.increment_downvotes()
                    message = "👎 Downvoted!"

                session.commit()
                bot.answer_callback_query(call.id, message)

                # Update message with new vote counts
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton(f"👍 {link.upvotes}", callback_data=f"upvote_{link_id}"),
                    InlineKeyboardButton(f"👎 {link.downvotes}", callback_data=f"downvote_{link_id}")
                )
                keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=link.url))

                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=keyboard
                )

        except Exception as e:
            logger.error(f"Error in handle_vote: {str(e)}")
            bot.answer_callback_query(call.id, "An error occurred. Please try again.")

    # Corrected error handler signature
    def handle_errors(bot_instance, update):
        """Handle errors that occur during message processing."""
        try:
            logger.error(f"Update {update} caused an error")
            if hasattr(update, 'message') and update.message:
                bot_instance.reply_to(
                    update.message,
                    "Sorry, an error occurred while processing your request."
                )
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")

    # Register the middleware handler
    bot.register_middleware_handler(handle_errors, update_types=['update'])