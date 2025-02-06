import telebot
import os

# Telegram bot token
BOT_TOKEN = "_+76544678"
bot = telebot.TeleBot(BOT_TOKEN)

# List of admin user IDs
ADMINS = [34567988765445]  # Replace with actual admin user IDs

# Database connection URI
DATABASE_URI = "sqlite:///links.db"  # SQLite database file
