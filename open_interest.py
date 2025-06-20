import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)

class OpenInterestAnalyzer:
    def __init__(self):
        self.api = HyperliquidAPI()
        self.alerts = {}  # Store user alerts
        self.historical_data = {}  # Cache historical data

    async def get_open_interest_data(self) -> Dict[str, Dict]:
        """Get current open interest data for all assets"""
        try:
            oi_data = await self.api.get_open_interest()
            return oi_data
        except Exception as e:
            logger.error(f"Error getting open interest data: {e}")
            return {}

    async def analyze_oi_changes(self, hours: int = 24) -> List[Dict]:
        """Analyze open interest changes over time"""
        try:
            current_oi = await self.get_open_interest_data()
            if not current_oi:
                return []

            # Get historical data (you might need to implement this in the API)
            # For now, we'll work with current data
            analysis_results = []
            
            for asset, data in current_oi.items():
                current_value = data.get('value', 0)
                
                # Calculate percentage change (if historical data available)
                change_pct = 0  # Placeholder
                
                analysis_results.append({
                    'asset': asset,
                    'current_oi': current_value,
                    'change_24h': change_pct,
                    'timestamp': data.get('timestamp', datetime.now().timestamp())
                })

            # Sort by current OI
            df = pd.DataFrame(analysis_results)
            df = df.sort_values('current_oi', ascending=False)
            
            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Error analyzing OI changes: {e}")
            return []

    async def detect_oi_spikes(self, threshold: float = 0.1) -> List[Dict]:
        """Detect sudden changes in open interest"""
        try:
            oi_data = await self.analyze_oi_changes()
            spikes = []
            
            for data in oi_data:
                change_pct = abs(data.get('change_24h', 0))
                if change_pct >= threshold:
                    spikes.append({
                        'asset': data['asset'],
                        'change_pct': change_pct,
                        'current_oi': data['current_oi'],
                        'type': 'increase' if data.get('change_24h', 0) > 0 else 'decrease'
                    })
            
            return spikes

        except Exception as e:
            logger.error(f"Error detecting OI spikes: {e}")
            return []

    async def set_oi_alert(self, user_id: int, asset: str, threshold: float, alert_type: str = "spike"):
        """Set open interest alert for user"""
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
            logger.error(f"Error setting OI alert: {e}")
            return False

    async def check_oi_alerts(self) -> List[Dict]:
        """Check open interest alerts and return triggered ones"""
        triggered_alerts = []
        
        try:
            oi_data = await self.get_open_interest_data()
            
            for user_id, user_alerts in self.alerts.items():
                for alert in user_alerts:
                    asset = alert['asset']
                    threshold = alert['threshold']
                    current_oi = oi_data.get(asset, {}).get('value', 0)
                    
                    # Check for significant changes
                    if alert['type'] == "spike":
                        # This would need historical data for proper implementation
                        # For now, we'll use a simple threshold check
                        if current_oi >= threshold:
                            triggered_alerts.append({
                                'user_id': user_id,
                                'asset': asset,
                                'current_oi': current_oi,
                                'threshold': threshold,
                                'alert_type': alert['type']
                            })
            
            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking OI alerts: {e}")
            return []

    async def format_oi_message(self, oi_data: List[Dict], spikes: List[Dict] = None) -> str:
        """Format open interest data for display"""
        if not oi_data:
            return "No open interest data available."
        
        message = "💰 Open Interest Analysis:\n\n"
        
        # Show top assets by OI
        message += "📊 Top Assets by Open Interest:\n"
        for data in oi_data[:10]:  # Show top 10
            message += f"🔸 {data['asset']}:\n"
            message += f"   OI: {data['current_oi']:,.0f}\n"
            message += f"   24h Change: {data['change_24h']:+.2f}%\n\n"
        
        # Add spike analysis if available
        if spikes:
            message += "🚨 Significant Changes:\n"
            for spike in spikes[:5]:  # Show top 5 spikes
                message += f"🔸 {spike['asset']}: {spike['change_pct']:+.2f}% ({spike['type']})\n"
        
        return message

    def get_oi_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for open interest commands"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Top OI", callback_data="top_oi"),
                InlineKeyboardButton("🚨 Spikes", callback_data="oi_spikes")
            ],
            [
                InlineKeyboardButton("🔔 Set Alert", callback_data="set_oi_alert")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 
