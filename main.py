"""Main Telegram bot script."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import TELEGRAM_BOT_TOKEN, START_MESSAGE, SUMMARY_NO_LINKS
from link_collector import LinkCollector
from message_formatter import MessageFormatter

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize link collector
link_collector = LinkCollector()
message_formatter = MessageFormatter()

async def check_bot_permissions(chat_id: int, bot) -> bool:
    """Check if bot has required permissions in the chat."""
    try:
        # Get bot's member info in the chat
        member = await bot.get_chat_member(chat_id, bot.id)
        logger.info(f"Bot status in chat {chat_id}: {member.status}")

        # Check bot's status and permissions
        if member.status == 'administrator':
            logger.info(f"Bot is administrator in chat {chat_id}")
            return True
        elif member.status == 'member':
            # For regular members, verify basic permissions
            chat = await bot.get_chat(chat_id)
            if not chat.permissions:
                logger.warning(f"No permissions object found for chat {chat_id}")
                return False
            if not chat.permissions.can_send_messages:
                logger.warning(f"Bot cannot send messages in chat {chat_id}")
                return False
            logger.info(f"Bot is regular member with message permissions in chat {chat_id}")
            return True
        elif member.status in ['restricted', 'left', 'kicked']:
            logger.warning(f"Bot has restricted status in chat {chat_id}: {member.status}")
            return False

        logger.warning(f"Unknown bot status in chat {chat_id}: {member.status}")
        return False

    except TelegramError as e:
        logger.error(f"Failed to check permissions in chat {chat_id}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking permissions in chat {chat_id}: {e}", exc_info=True)
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    try:
        if not update.effective_chat:
            logger.error("No effective chat found in update")
            return

        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        logger.info(f"Start command received in chat {chat_id} (type: {chat_type})")

        if chat_type == "private":
            # Create a deep link URL for adding bot to groups
            bot_username = context.bot.username
            invite_link = f"https://t.me/{bot_username}?startgroup=true"

            await update.message.reply_text(
                START_MESSAGE + f"\n\n[Add me to your group!]({invite_link})",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logger.info("Sent start message in private chat")
        else:
            if not await check_bot_permissions(chat_id, context.bot):
                logger.warning(f"Bot lacks permissions in chat {chat_id}")
                error_msg = (
                    "I don't have the necessary permissions to operate in this chat.\n"
                    "Please make me an admin or ensure I have permission to:\n"
                    "- Send messages\n"
                    "- Read messages\n"
                    "Then try the command again."
                )
                await update.message.reply_text(
                    error_msg,
                    quote=True
                )
                return
            await update.message.reply_text(
                START_MESSAGE,
                disable_web_page_preview=True,
                quote=False
            )
            logger.info("Sent start message in group chat")

    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        try:
            await update.message.reply_text(
                "Sorry, something went wrong. Please make sure I have the necessary permissions and try again.",
                quote=True
            )
        except:
            logger.error("Failed to send error message", exc_info=True)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /summary command."""
    try:
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        logger.info(f"Summary command received in chat {chat_id} (type: {chat_type})")

        # Check bot permissions for group chats
        if chat_type in ['group', 'supergroup']:
            logger.info(f"Checking permissions for group chat {chat_id}")
            if not await check_bot_permissions(chat_id, context.bot):
                logger.warning(f"Bot lacks permissions in chat {chat_id}")
                await update.message.reply_text(
                    "I don't have the necessary permissions to operate in this chat. "
                    "Please make sure I have permission to send messages.",
                    quote=True
                )
                return

        # Get links and format summary
        links = link_collector.get_chat_links(chat_id)
        logger.info(f"Found {len(links)} links for chat {chat_id}")

        try:
            # Generate and send summary
            if not links:
                await update.message.reply_text(
                    SUMMARY_NO_LINKS,
                    quote=False
                )
                logger.info("Sent no links message")
                return

            summary = message_formatter.format_summary(links)
            logger.info(f"Generated summary length: {len(summary)}")

            # Split long messages if needed (Telegram's limit is 4096 characters)
            MAX_MESSAGE_LENGTH = 4000  # Leave some room for formatting
            if len(summary) > MAX_MESSAGE_LENGTH:
                logger.info("Splitting long summary into chunks")
                chunks = [summary[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(summary), MAX_MESSAGE_LENGTH)]
                for chunk in chunks:
                    await update.message.reply_text(
                        chunk,
                        disable_web_page_preview=True,
                        quote=False  # Don't quote the command message
                    )
            else:
                await update.message.reply_text(
                    summary,
                    disable_web_page_preview=True,
                    quote=False  # Don't quote the command message
                )
            logger.info("Summary sent successfully")
        except Exception as format_error:
            logger.error(f"Error formatting or sending summary: {str(format_error)}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Error in summary command: {str(e)}", exc_info=True)
        error_message = (
            "Sorry, I encountered an error while generating the summary. "
            "Please try again or contact the bot administrator if the problem persists."
        )
        try:
            await update.message.reply_text(error_message, quote=True)
        except Exception as reply_error:
            logger.error(f"Failed to send error message: {str(reply_error)}", exc_info=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and extract Twitter/X links."""
    try:
        if not update.message or not update.message.text:
            logger.info("Received message without text")
            return

        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        text = update.message.text.strip()
        username = update.message.from_user.username or str(update.message.from_user.id)

        # Enhanced logging for debugging
        logger.info(f"Processing message in chat {chat_id} (type: {chat_type})")
        logger.info(f"Message text: {text}")
        logger.info(f"From user: {username}")

        # For group chats, verify bot permissions first
        if chat_type in ['group', 'supergroup']:
            if not await check_bot_permissions(chat_id, context.bot):
                logger.warning(f"Bot lacks permissions in chat {chat_id}")
                return

        # Extract and store Twitter/X links
        links = link_collector.extract_twitter_links(text)
        if links:
            logger.info(f"Found {len(links)} Twitter/X links in message")
            for link in links:
                if link_collector.add_link(chat_id, link, username):
                    try:
                        confirmation = message_formatter.format_link_added(username)
                        await update.message.reply_text(
                            confirmation,
                            disable_web_page_preview=True,
                            quote=True  # Reply to the message containing the link
                        )
                    except TelegramError as e:
                        logger.error(f"Error sending confirmation: {str(e)}", exc_info=True)
                else:
                    logger.info(f"Link {link} was not added (possibly duplicate)")
        else:
            logger.info("No Twitter/X links found in message")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        logger.error(f"Message content that caused error: {update.message.text if update.message else 'No message'}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Error occurred: {context.error}", exc_info=True)
    if update and update.message:
        try:
            await update.message.reply_text(
                "Sorry, an error occurred while processing your request. Please try again later."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")

def main():
    """Start the bot."""
    try:
        logger.info("Starting bot...")

        # Create application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("summary", summary_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("Bot is ready to receive messages")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Critical error starting bot: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()