from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes
from analyzers import AnalyzerOrchestrator
import logging

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self):
        self.orchestrator = AnalyzerOrchestrator()

    async def _send_message(self, update: Update, text: str, reply_markup=None):
        """Helper method to send messages"""
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "👋 Welcome to HyStatsio Bot!\n\n"
            "Advanced Market Analysis Platform\n\n"
            "What do you want to analyze?"
        )
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("📊 Funding Rates", callback_data="funding"),
                InlineKeyboardButton("💥 Liquidations", callback_data="liquidations")
            ],
            [
                InlineKeyboardButton("💰 Open Interest", callback_data="oi"),
                InlineKeyboardButton("📈 Volume Analysis", callback_data="volume")
            ],
            [
                InlineKeyboardButton("🔍 Divergences", callback_data="divergence"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_message(update, welcome_message, reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.orchestrator.show_help(update, context)

    async def handle_funding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /funding command"""
        await self.orchestrator.get_funding_analysis(update, context)

    async def handle_liquidations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /liquidations command"""
        await self.orchestrator.get_liquidation_analysis(update, context)

    async def handle_oi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /oi command"""
        await self.orchestrator.get_oi_analysis(update, context)

    async def handle_volume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /volume command"""
        await self.orchestrator.get_volume_analysis(update, context)

    async def handle_divergence(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /divergence command"""
        await self.orchestrator.get_divergence_analysis(update, context)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        await self.orchestrator.handle_callback(update, context)

    async def handle_find_asset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle find asset button click"""
        query = update.callback_query
        await query.answer()
        
        # Send message asking for asset name
        await query.message.reply_text(
            "Please enter the asset name you want to check (e.g., BTC, ETH):",
            reply_markup=ForceReply()
        )
        # Set user state to wait for asset name
        context.user_data['waiting_for_asset'] = True

    async def handle_set_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle set alert button click"""
        query = update.callback_query
        await query.answer()
        
        # Send message asking for asset name and threshold
        await query.message.reply_text(
            "Please enter the asset name and threshold in the format:\n"
            "ASSET THRESHOLD\n"
            "Example: BTC 0.0001\n"
            "The alert will trigger when the funding rate crosses this threshold.",
            reply_markup=ForceReply()
        )
        # Set user state to wait for alert details
        context.user_data['waiting_for_alert'] = True

    async def handle_asset_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user input for asset search"""
        if context.user_data.get('waiting_for_asset'):
            asset = update.message.text.upper()
            asset_data = await self.orchestrator.funding_analyzer.find_asset(asset)
            
            if asset_data:
                message = f"📊 Funding Rate for {asset}:\n\n"
                message += f"Current (1h): {asset_data['current']*100:.4f}%\n"
                message += f"Annualized: {asset_data['annualized']:.2f}%"
                
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"Asset {asset} not found on Hyperliquid.")
            
            # Clear the waiting state
            context.user_data['waiting_for_asset'] = False

    async def handle_alert_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user input for alert setting"""
        if context.user_data.get('waiting_for_alert'):
            try:
                asset, threshold = update.message.text.upper().split()
                threshold = float(threshold)
                
                # Set alert using funding analyzer
                success = await self.orchestrator.funding_analyzer.set_alert(
                    update.effective_user.id, asset, threshold
                )
                
                if success:
                    await update.message.reply_text(
                        f"Alert set for {asset} with threshold {threshold*100:.4f}%\n"
                        "You will be notified when the funding rate crosses this threshold."
                    )
                else:
                    await update.message.reply_text("Failed to set alert. Please try again.")
                    
            except ValueError:
                await update.message.reply_text(
                    "Invalid format. Please use: ASSET THRESHOLD\n"
                    "Example: BTC 0.0001"
                )
            
            # Clear the waiting state
            context.user_data['waiting_for_alert'] = False

    async def close(self):
        """Close API connections"""
        # Close connections in all analyzers
        pass 
        
