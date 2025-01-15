from database import get_user_by_id, get_all_links

def register_user_handlers(bot):
    @bot.message_handler(commands=["profile"])
    def handle_profile(message):
        user = get_user_by_id(message.from_user.id)
        if not user:
            bot.reply_to(message, "You are not registered.")
            return

        # Fetch links submitted by the user
        links = get_all_links()
        user_links = [link for link in links if link.user_id == user.user_id]

        # Create a message with the user's profile
        profile_text = (
            f"👤 **Profile**\n"
            f"Name: {user.first_name} {user.last_name}\n"
            f"Username: @{user.username}\n"
            f"Role: {user.role}\n"
            f"Links Submitted: {len(user_links)}\n"
        )

        bot.reply_to(message, profile_text)