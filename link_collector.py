"""Module for collecting and managing Twitter/X links."""
from datetime import datetime
import re
import logging
from typing import Dict, List, Tuple

from config import TWITTER_LINK_PATTERN

# Set up logger
logger = logging.getLogger(__name__)

class LinkCollector:
    def __init__(self):
        # Structure: {chat_id: [(link, username, timestamp)]}
        self.links: Dict[int, List[Tuple[str, str, datetime]]] = {}
        logger.info("LinkCollector initialized")

    def extract_twitter_links(self, text: str) -> List[str]:
        """Extract Twitter/X links from text using regex."""
        try:
            logger.info(f"Attempting to extract links from text: {text}")

            # Find all potential links using regex
            matches = re.finditer(TWITTER_LINK_PATTERN, text)
            links = [match.group(0) for match in matches]
            logger.info(f"Initially found links: {links}")

            # Clean and validate links
            cleaned_links = []
            for link in links:
                # Remove query parameters and clean up
                cleaned_link = re.sub(r'\?.*$', '', link.strip())
                # Validate the link structure
                if ('twitter.com' in cleaned_link or 'x.com' in cleaned_link):
                    cleaned_links.append(cleaned_link)
                    logger.info(f"Added valid link: {cleaned_link}")

            logger.info(f"Final cleaned links: {cleaned_links}")
            return cleaned_links

        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}", exc_info=True)
            return []

    def add_link(self, chat_id: int, link: str, username: str) -> bool:
        """Add a new Twitter/X link to the collection."""
        try:
            logger.info(f"Attempting to add link: {link} from user: {username} in chat: {chat_id}")

            # Validate input parameters
            if not isinstance(chat_id, int):
                logger.error(f"Invalid chat_id type: {type(chat_id)}")
                return False
            if not link or not isinstance(link, str):
                logger.error(f"Invalid link: {link}")
                return False
            if not username or not isinstance(username, str):
                logger.error(f"Invalid username: {username}")
                return False

            # Initialize chat collection if needed
            if chat_id not in self.links:
                self.links[chat_id] = []
                logger.info(f"Created new collection for chat {chat_id}")

            # Clean and store the link
            cleaned_link = re.sub(r'\?.*$', '', link.strip())
            logger.info(f"Cleaned link for storage: {cleaned_link}")

            # Check for duplicates
            if any(cleaned_link == existing_link for existing_link, _, _ in self.links[chat_id]):
                logger.info(f"Link {cleaned_link} already exists in chat {chat_id}")
                return False

            # Add new link with current timestamp
            current_time = datetime.now()
            self.links[chat_id].append((cleaned_link, username, current_time))
            logger.info(f"Added link to chat {chat_id}: {cleaned_link}")
            logger.info(f"Current links for chat {chat_id}: {self.links[chat_id]}")
            return True

        except Exception as e:
            logger.error(f"Error adding link: {str(e)}", exc_info=True)
            return False

    def get_chat_links(self, chat_id: int) -> List[Tuple[str, str, datetime]]:
        """Get all links shared in a specific chat."""
        try:
            logger.info(f"Retrieving links for chat {chat_id}")
            # Validate chat_id
            if not isinstance(chat_id, int):
                logger.error(f"Invalid chat_id type in get_chat_links: {type(chat_id)}")
                return []

            # Get links with validation
            links = self.links.get(chat_id, [])
            logger.info(f"Found {len(links)} links for chat {chat_id}")

            # Validate each link tuple
            valid_links = []
            for link_tuple in links:
                if len(link_tuple) != 3:
                    logger.error(f"Invalid link tuple structure: {link_tuple}")
                    continue
                if not all(isinstance(x, (str, datetime)) for x in link_tuple):
                    logger.error(f"Invalid types in link tuple: {link_tuple}")
                    continue
                valid_links.append(link_tuple)

            logger.info(f"Returning {len(valid_links)} validated links")
            return valid_links

        except Exception as e:
            logger.error(f"Error retrieving links: {str(e)}", exc_info=True)
            return []

    def clear_chat_links(self, chat_id: int) -> bool:
        """Clear all links for a specific chat."""
        try:
            if not isinstance(chat_id, int):
                logger.error(f"Invalid chat_id type in clear_chat_links: {type(chat_id)}")
                return False

            if chat_id in self.links:
                logger.info(f"Clearing all links for chat {chat_id}")
                self.links[chat_id] = []
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing links: {str(e)}", exc_info=True)
            return False