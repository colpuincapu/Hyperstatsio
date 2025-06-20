import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes
from hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)

class FundingAnalyzer:
    def __init__(self):
        self.api = HyperliquidAPI()
        self.alerts = {}  # Store user alerts

    async def get_top_funding_rates(self, hours: int = 24) -> List[Dict]:
        """Get top funding rates for the specified period"""
        try:
            # Get current funding rates
            funding_rates = await self.api.get_funding_rates()
            if not funding_rates:
                return []

            # Get historical data
            end_time = int(datetime.now().timestamp())
            start_time = end_time - (hours * 60 * 60)
            
            tokens = [rate["token"] for rate in funding_rates if rate.get("token")]
            history = await self.api.get_funding_history_batch(tokens, start_time, end_time)

            # Create DataFrame for analysis
            funding_data = []
            for rate in funding_rates:
                token = rate.get("token")
                if not token:
                    continue

                current_rate = rate["rate"]
                annualized_rate = current_rate * 24 * 365 * 100

                # Calculate 24h change
                change_24h = 0
                if token in history and history[token]:
                    oldest_rate = float(history[token][-1]["fundingRate"])
                    change_24h = ((current_rate - oldest_rate) / abs(oldest_rate)) * 100 if oldest_rate != 0 else 0

                funding_data.append({
                    "token": token,
                    "current": current_rate,
                    "annualized": annualized_rate,
                    "change_24h": change_24h
                })

            # Sort by current rate and return top 5
            df = pd.DataFrame(funding_data)
            df = df.sort_values('current', ascending=False).head(5)
            
            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Error getting top funding rates: {e}")
            return []

    async def find_asset(self, asset: str) -> Optional[Dict]:
        """Find specific asset funding data"""
        try:
            funding_rates = await self.api.get_funding_rates()
            asset_data = next((rate for rate in funding_rates if rate.get("token") == asset.upper()), None)
            
            if asset_data:
                current_rate = asset_data["rate"]
                annualized_rate = current_rate * 24 * 365 * 100
                
                return {
                    "token": asset_data["token"],
                    "current": current_rate,
                    "annualized": annualized_rate
                }
            return None

        except Exception as e:
            logger.error(f"Error finding asset {asset}: {e}")
            return None

    async def set_alert(self, user_id: int, asset: str, threshold: float, alert_type: str = "cross"):
        """Set funding rate alert for user"""
        try:
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            
            self.alerts[user_id].append({
                'asset': asset.upper(),
                'threshold': threshold,
                'type': alert_type,
                'created_at': datetime.now()
            })
            
            return True
        except Exception as e:
            logger.error(f"Error setting alert: {e}")
            return False

    async def check_alerts(self) -> List[Dict]:
        """Check all alerts and return triggered ones"""
        triggered_alerts = []
        
        try:
            funding_rates = await self.api.get_funding_rates()
            current_rates = {rate["token"]: rate["rate"] for rate in funding_rates}
            
            for user_id, user_alerts in self.alerts.items():
                for alert in user_alerts:
                    asset = alert['asset']
                    threshold = alert['threshold']
                    current_rate = current_rates.get(asset)
                    
                    if current_rate is not None:
                        # Check if threshold is crossed
                        if alert['type'] == "cross":
                            if abs(current_rate) >= abs(threshold):
                                triggered_alerts.append({
                                    'user_id': user_id,
                                    'asset': asset,
                                    'current_rate': current_rate,
                                    'threshold': threshold,
                                    'alert_type': alert['type']
                                })
                        elif alert['type'] == "positive":
                            if current_rate > threshold:
                                triggered_alerts.append({
                                    'user_id': user_id,
                                    'asset': asset,
                                    'current_rate': current_rate,
                                    'threshold': threshold,
                                    'alert_type': alert['type']
                                })
                        elif alert['type'] == "negative":
                            if current_rate < threshold:
                                triggered_alerts.append({
                                    'user_id': user_id,
                                    'asset': asset,
                                    'current_rate': current_rate,
                                    'threshold': threshold,
                                    'alert_type': alert['type']
                                })
            
            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return []

    async def format_funding_message(self, funding_data: List[Dict]) -> str:
        """Format funding data for display"""
        if not funding_data:
            return "No funding data available."
        
        message = "📊 Top 5 Funding Rates (24h):\n\n"
        for data in funding_data:
            message += f"🔹 {data['token']}:\n"
            message += f"   Current (1h): {data['current']*100:.4f}%\n"
            message += f"   Annualized: {data['annualized']:.2f}%\n"
            message += f"   24h Change: {data['change_24h']:+.2f}%\n\n"
        
        return message

    def get_funding_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for funding commands"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Find an Asset", callback_data="find_asset"),
                InlineKeyboardButton("🔔 Set Alert", callback_data="set_alert")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 
