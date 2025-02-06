import telebot
import os

# Telegram bot token
BOT_TOKEN = "7856502542:AAFOlqazGOG0JpwpQjfmm_ARNd4huACWVpM"
bot = telebot.TeleBot(BOT_TOKEN)

# List of admin user IDs
ADMINS = [5250831809]  # Replace with actual admin user IDs

# Database connection URI
DATABASE_URI = "sqlite:///links.db"  # SQLite database file
