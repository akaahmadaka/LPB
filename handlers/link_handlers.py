from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_session, get_link_by_id, get_all_links
from utils.logger import logger
from sqlalchemy.exc import SQLAlchemyError
from utils.helpers import format_timestamp
from config import ADMINS
from models.user_model import User


def escape_markdown(text):
    """Escape Markdown special characters."""
    special_chars = ['_', '*', '`', '[', ']']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


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


def create_link_detail_keyboard(link, voter_id, current_page=0):
    """Create keyboard for link detail view."""
    keyboard = InlineKeyboardMarkup()

    # Add vote buttons
    if not link.has_voter_voted(voter_id):
        keyboard.row(
            InlineKeyboardButton(f"👍 {link.upvotes}", callback_data=f"upvote_{link.id}_{current_page}"),
            InlineKeyboardButton(f"👎 {link.downvotes}", callback_data=f"downvote_{link.id}_{current_page}")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(f"👍 {link.upvotes} ", callback_data="already_voted"),
            InlineKeyboardButton(f"👎 {link.downvotes} ", callback_data="already_voted")
        )

    # Add visit and back buttons
    keyboard.add(InlineKeyboardButton("🔗 Visit Link", url=link.url))
    keyboard.add(InlineKeyboardButton("⬅️ Back to List", callback_data=f"page_{current_page}"))

    return keyboard


def register_link_handlers(bot):
    """Register link-related handlers."""

    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_link_'))
    def handle_link_view(call: CallbackQuery):
        """Handle link view callback when title is clicked."""
        try:
            # Extract link_id and page number
            parts = call.data.split('_')
            link_id = int(parts[2])
            current_page = int(parts[3]) if len(parts) > 3 else 0
            user_id = call.from_user.id

            with get_db_session() as session:
                # Credit check logic
                if user_id not in ADMINS:
                    user = session.query(User).filter(User.user_id == user_id).first()
                    if not user:
                        user = User(user_id=user_id, credits=5)
                        session.add(user)

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

                    user.credits -= 1

                link = get_link_by_id(link_id, session)
                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return

                if not link.has_user_clicked(user_id):
                    link.add_click(user_id)
                    session.commit()

                keyboard = create_link_detail_keyboard(link, user_id, current_page)

                # Escape special characters in title and URL for Markdown
                safe_title = escape_markdown(link.title)
                safe_url = escape_markdown(link.url)

                link_text = (
                    f"*{safe_title}*\n\n"
                    f"🔗 `{safe_url}`\n"
                    f"👀 {link.clicks} views\n"
                )

                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=link_text,
                    parse_mode="MarkdownV2",  # Use MarkdownV2 for better escaping
                    reply_markup=keyboard,
                    disable_web_page_preview=True  # Prevent URL preview to avoid formatting issues
                )

                bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in link view handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('upvote_', 'downvote_')))
    def handle_vote(call: CallbackQuery):
        """Handle upvote and downvote callbacks."""
        try:
            # Extract vote type, link_id, and page number
            parts = call.data.split('_')
            action = parts[0]
            link_id = int(parts[1])
            current_page = int(parts[2]) if len(parts) > 2 else 0
            voter_id = call.from_user.id

            with get_db_session() as session:
                link = get_link_by_id(link_id, session)

                if not link:
                    bot.answer_callback_query(call.id, "❌ Link not found!")
                    return

                if link.has_voter_voted(voter_id):
                    bot.answer_callback_query(call.id, "❌ You've already voted on this link!", show_alert=True)
                    return

                is_upvote = (action == 'upvote')
                success = link.add_vote(voter_id, is_upvote)

                if not success:
                    bot.answer_callback_query(call.id, "❌ You've already voted on this link!", show_alert=True)
                    return

                session.flush()
                session.refresh(link)
                session.commit()

                vote_msg = "👍 Upvoted!" if is_upvote else "👎 Downvoted!"

                # Use the helper function to create the keyboard with the current page
                keyboard = create_link_detail_keyboard(link, voter_id, current_page)

                # Escape special characters in title and URL for Markdown
                safe_title = escape_markdown(link.title)
                safe_url = escape_markdown(link.url)

                link_text = (
                    f"*{safe_title}*\n\n"
                    f"🔗 `{safe_url}`\n"
                    f"👀 {link.clicks} views\n"
                )

                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=link_text,
                    parse_mode="MarkdownV2",  # Use MarkdownV2 for better escaping
                    reply_markup=keyboard,
                    disable_web_page_preview=True  # Prevent URL preview to avoid formatting issues
                )

                bot.answer_callback_query(call.id, vote_msg)

        except Exception as e:
            logger.error(f"Error in vote handler: {str(e)}")
            bot.answer_callback_query(call.id, "❌ An error occurred!")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
    def handle_page_navigation(call: CallbackQuery):
        """Handle pagination navigation."""
        try:
            current_page = int(call.data.split('_')[1])

            with get_db_session() as session:
                links = get_all_links(session)

                if not links:
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="No links have been shared yet."
                    )
                    return

                keyboard, total_pages = create_links_keyboard(links, current_page)

                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"📋 *Shared Links*\nClick on a title to view details:\nPage {current_page + 1} of {total_pages}",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )

                bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error in page navigation handler: {str(e)}")
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