"""Module for formatting bot messages."""
from datetime import datetime
from typing import List, Tuple
import html
import logging

# Set up logger
logger = logging.getLogger(__name__)

class MessageFormatter:
    @staticmethod
    def format_summary(links: List[Tuple[str, str, datetime]]) -> str:
        """Format the summary message with collected links."""
        try:
            logger.info(f"Formatting summary for {len(links)} links")

            if not links:
                logger.info("No links to format, returning empty message")
                return "No Twitter/X links have been shared yet! 🤔"

            summary = "📊 Twitter/X Links Summary:\n\n"

            # Group links by user
            user_links = {}
            for link, username, timestamp in links:
                if username not in user_links:
                    user_links[username] = []
                user_links[username].append((link, timestamp))

            logger.info(f"Grouped links by {len(user_links)} users")

            # Format summary by user
            for username, user_link_list in user_links.items():
                # Escape special characters in username
                safe_username = html.escape(username)
                summary += f"👤 {safe_username}:\n"
                for link, timestamp in user_link_list:
                    try:
                        time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                        # Don't use markdown for links, just show them as plain text
                        summary += f"🔗 {link}\n📅 Shared on: {time_str}\n\n"
                    except Exception as e:
                        logger.error(f"Error formatting link entry: {str(e)}", exc_info=True)
                        continue

            summary += "Use these links to engage and support! 🚀"
            logger.info(f"Successfully formatted summary (length: {len(summary)})")
            return summary

        except Exception as e:
            logger.error(f"Error in format_summary: {str(e)}", exc_info=True)
            return "Sorry, there was an error formatting the summary. Please try again."

    @staticmethod
    def format_link_added(username: str) -> str:
        """Format message for when a new link is added."""
        try:
            if not username:
                logger.warning("Empty username provided to format_link_added")
                username = "Unknown User"

            safe_username = html.escape(username)
            return f"✅ Twitter/X link from {safe_username} has been collected!"

        except Exception as e:
            logger.error(f"Error in format_link_added: {str(e)}", exc_info=True)
            return "✅ Twitter/X link has been collected!"