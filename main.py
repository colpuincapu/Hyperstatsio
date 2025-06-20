import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButton, MenuButtonCommands
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from commands import CommandHandler as BotCommandHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Telegram token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)
else:
    logger.info("✅ Token Telegram trouvé")
    logger.info(f"Token: {TELEGRAM_TOKEN[:10]}...")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Initialize command handler
    command_handler = BotCommandHandler()

    # Add command handlers
    application.add_handler(CommandHandler("start", command_handler.start))
    application.add_handler(CommandHandler("help", command_handler.help_command))
    application.add_handler(CommandHandler("funding", command_handler.handle_funding))
    application.add_handler(CommandHandler("liquidations", command_handler.handle_liquidations))
    application.add_handler(CommandHandler("oi", command_handler.handle_oi))
    application.add_handler(CommandHandler("volume", command_handler.handle_volume))
    application.add_handler(CommandHandler("divergence", command_handler.handle_divergence))

    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(command_handler.handle_callback, pattern="^(funding|liquidations|oi|volume|divergence|help|back_to_menu)$"))
    application.add_handler(CallbackQueryHandler(command_handler.handle_find_asset, pattern="^find_asset$"))
    application.add_handler(CallbackQueryHandler(command_handler.handle_set_alert, pattern="^set_alert$"))

    # Add message handlers for user inputs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, command_handler.handle_asset_input))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, command_handler.handle_alert_input))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main() 
