"""Configuration settings for the Telegram bot."""
import os

# Bot configuration
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Regular expressions for Twitter/X links
TWITTER_LINK_PATTERN = r'https?:\/\/(?:www\.)?(?:twitter\.com|x\.com)\/(?:[^\/\s]+)(?:\/[^\s]*)?'

# Message templates
START_MESSAGE = """
👋 Hello! I'm a Twitter/X Raid Bot.

I'll help track Twitter/X links shared in this chat and create summaries.

Commands:
/start - Show this message
/summary - Generate a summary of shared links

Just add me to a group and I'll start collecting Twitter/X links automatically! 🚀
"""

SUMMARY_NO_LINKS = "No Twitter/X links have been shared in this chat yet! 🤔"