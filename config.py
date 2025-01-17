import telebot
import os

# Telegram bot token
BOT_TOKEN = "445665433334677"
bot = telebot.TeleBot(BOT_TOKEN)

# List of admin user IDs
ADMINS = [3457654446]  # Replace with actual admin user IDs

# Database connection URI
DATABASE_URI = "sqlite:///links.db"  # SQLite database file
