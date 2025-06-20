import logging
from typing import Dict, List
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from funding import FundingAnalyzer
from liquidations import LiquidationAnalyzer
from open_interest import OpenInterestAnalyzer
from volume_spike import VolumeSpikeAnalyzer
from volume_price_divergence import VolumePriceDivergenceAnalyzer

logger = logging.getLogger(__name__)

class AnalyzerOrchestrator:
    def __init__(self):
        self.funding_analyzer = FundingAnalyzer()
        self.liquidation_analyzer = LiquidationAnalyzer()
        self.oi_analyzer = OpenInterestAnalyzer()
        self.volume_analyzer = VolumeSpikeAnalyzer()
        self.divergence_analyzer = VolumePriceDivergenceAnalyzer()

    async def get_funding_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get funding rate analysis"""
        loading_message = None
        try:
            # Send loading message
            loading_message = await self._send_message(update, "⏳ Loading funding rates...")
            
            # Get funding data
            funding_data = await self.funding_analyzer.get_top_funding_rates()
            
            # Format message
            message = await self.funding_analyzer.format_funding_message(funding_data)
            
            # Delete loading message
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as e:
                    logger.error(f"Error deleting loading message: {e}")
            
            # Send message with keyboard
            keyboard = self.funding_analyzer.get_funding_keyboard()
            await self._send_message(update, message, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in funding analysis: {e}")
            # Delete loading message if there was an error
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as del_e:
                    logger.error(f"Error deleting loading message after error: {del_e}")
            await self._send_message(update, "An error occurred while analyzing funding rates.")

    async def get_liquidation_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get liquidation analysis"""
        loading_message = None
        try:
            # Send loading message
            loading_message = await self._send_message(update, "⏳ Loading liquidations...")
            
            # Get liquidation data
            liquidations = await self.liquidation_analyzer.get_recent_liquidations()
            cascade_analysis = await self.liquidation_analyzer.analyze_liquidation_cascade(liquidations)
            
            # Format message
            message = await self.liquidation_analyzer.format_liquidation_message(liquidations, cascade_analysis)
            
            # Delete loading message
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as e:
                    logger.error(f"Error deleting loading message: {e}")
            
            # Send message with keyboard
            keyboard = self.liquidation_analyzer.get_liquidation_keyboard()
            await self._send_message(update, message, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in liquidation analysis: {e}")
            # Delete loading message if there was an error
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as del_e:
                    logger.error(f"Error deleting loading message after error: {del_e}")
            await self._send_message(update, "An error occurred while analyzing liquidations.")

    async def get_oi_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get open interest analysis"""
        loading_message = None
        try:
            # Send loading message
            loading_message = await self._send_message(update, "⏳ Loading open interest data...")
            
            # Get OI data
            oi_data = await self.oi_analyzer.analyze_oi_changes()
            spikes = await self.oi_analyzer.detect_oi_spikes()
            
            # Format message
            message = await self.oi_analyzer.format_oi_message(oi_data, spikes)
            
            # Delete loading message
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as e:
                    logger.error(f"Error deleting loading message: {e}")
            
            # Send message with keyboard
            keyboard = self.oi_analyzer.get_oi_keyboard()
            await self._send_message(update, message, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in OI analysis: {e}")
            # Delete loading message if there was an error
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as del_e:
                    logger.error(f"Error deleting loading message after error: {del_e}")
            await self._send_message(update, "An error occurred while analyzing open interest.")

    async def get_volume_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get volume analysis"""
        loading_message = None
        try:
            # Send loading message
            loading_message = await self._send_message(update, "⏳ Loading volume data...")
            
            # Get volume data
            volume_data = await self.volume_analyzer.detect_volume_patterns()
            spikes = await self.volume_analyzer.analyze_volume_spikes()
            
            # Format message
            message = await self.volume_analyzer.format_volume_message(volume_data, spikes)
            
            # Delete loading message
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as e:
                    logger.error(f"Error deleting loading message: {e}")
            
            # Send message with keyboard
            keyboard = self.volume_analyzer.get_volume_keyboard()
            await self._send_message(update, message, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in volume analysis: {e}")
            # Delete loading message if there was an error
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as del_e:
                    logger.error(f"Error deleting loading message after error: {del_e}")
            await self._send_message(update, "An error occurred while analyzing volume.")

    async def get_divergence_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get volume-price divergence analysis"""
        loading_message = None
        try:
            # Send loading message
            loading_message = await self._send_message(update, "⏳ Loading divergence analysis...")
            
            # Get divergence data
            divergences = await self.divergence_analyzer.detect_volume_price_divergence()
            analysis = await self.divergence_analyzer.analyze_divergence_patterns()
            
            # Format message
            message = await self.divergence_analyzer.format_divergence_message(divergences, analysis)
            
            # Delete loading message
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as e:
                    logger.error(f"Error deleting loading message: {e}")
            
            # Send message with keyboard
            keyboard = self.divergence_analyzer.get_divergence_keyboard()
            await self._send_message(update, message, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in divergence analysis: {e}")
            # Delete loading message if there was an error
            if loading_message:
                try:
                    await loading_message.delete()
                except Exception as del_e:
                    logger.error(f"Error deleting loading message after error: {del_e}")
            await self._send_message(update, "An error occurred while analyzing divergences.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "funding":
            await self.get_funding_analysis(update, context)
        elif query.data == "liquidations":
            await self.get_liquidation_analysis(update, context)
        elif query.data == "oi":
            await self.get_oi_analysis(update, context)
        elif query.data == "volume":
            await self.get_volume_analysis(update, context)
        elif query.data == "divergence":
            await self.get_divergence_analysis(update, context)
        elif query.data == "help":
            await self.show_help(update, context)
        elif query.data == "back_to_menu":
            await self.show_main_menu(update, context)

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        try:
            # Delete the current message if it's a callback query
            if update.callback_query:
                await update.callback_query.message.delete()
        except Exception as e:
            logger.error(f"Error deleting current message: {e}")
        
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

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_message = (
            "📚 HyStatsio Bot - Advanced Market Analysis\n\n"
            "Available Analysis Modules:\n\n"
            "📊 Funding Rate Dashboard:\n"
            "• Top funding rates with 24h changes\n"
            "• Find specific assets\n"
            "• Set funding rate alerts\n\n"
            "💥 Liquidation Scanner:\n"
            "• Recent liquidations analysis\n"
            "• Cascade detection\n"
            "• Size-based filtering\n\n"
            "💰 Open Interest Analyzer:\n"
            "• OI trends and changes\n"
            "• Spike detection\n"
            "• Alert system\n\n"
            "📈 Volume Spike Detector:\n"
            "• Volume pattern analysis\n"
            "• Spike detection\n"
            "• Historical comparison\n\n"
            "📊 Volume-Price Divergence:\n"
            "• Divergence detection\n"
            "• Pattern analysis\n"
            "• Automated alerts\n\n"
            "Use the menu buttons to access each module!"
        )
        await self._send_message(update, help_message)

    async def _send_message(self, update: Update, text: str, reply_markup=None):
        """Helper method to send messages"""
        try:
            if update.callback_query:
                message = await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
            else:
                message = await update.message.reply_text(text, reply_markup=reply_markup)
            return message
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None 
