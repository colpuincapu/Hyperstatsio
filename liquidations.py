import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)

class LiquidationAnalyzer:
    def __init__(self):
        self.api = HyperliquidAPI()
        self.alerts = {}  # Store user alerts

    async def get_recent_liquidations(self, hours: int = 24) -> List[Dict]:
        """Get recent liquidations for the specified period"""
        try:
            liquidations = await self.api.get_liquidations()
            if not liquidations:
                return []

            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_liquidations = []
            
            for liq in liquidations:
                liq_time = datetime.fromtimestamp(liq.get('timestamp', 0))
                if liq_time >= cutoff_time:
                    recent_liquidations.append(liq)

            return recent_liquidations

        except Exception as e:
            logger.error(f"Error getting recent liquidations: {e}")
            return []

    async def analyze_liquidation_cascade(self, liquidations: List[Dict]) -> Dict:
        """Analyze liquidation cascade patterns"""
        try:
            if not liquidations:
                return {}

            df = pd.DataFrame(liquidations)
            
            # Group by time intervals to detect cascades
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['time_bucket'] = df['timestamp'].dt.floor('5min')  # 5-minute buckets
            
            cascade_analysis = {
                'total_liquidations': len(liquidations),
                'cascade_periods': [],
                'largest_cascade': 0,
                'total_volume': 0
            }

            # Find cascade periods (multiple liquidations in short time)
            grouped = df.groupby('time_bucket').size()
            cascade_periods = grouped[grouped >= 3]  # 3+ liquidations in 5min = cascade
            
            for period, count in cascade_periods.items():
                cascade_analysis['cascade_periods'].append({
                    'time': period,
                    'count': count
                })
                cascade_analysis['largest_cascade'] = max(cascade_analysis['largest_cascade'], count)

            # Calculate total volume
            if 'size' in df.columns:
                cascade_analysis['total_volume'] = df['size'].sum()

            return cascade_analysis

        except Exception as e:
            logger.error(f"Error analyzing liquidation cascade: {e}")
            return {}

    async def filter_liquidations_by_size(self, liquidations: List[Dict], min_size: float = 0) -> List[Dict]:
        """Filter liquidations by minimum size"""
        try:
            if not liquidations:
                return []

            df = pd.DataFrame(liquidations)
            if 'size' in df.columns:
                filtered_df = df[df['size'] >= min_size]
                return filtered_df.to_dict('records')
            
            return liquidations

        except Exception as e:
            logger.error(f"Error filtering liquidations by size: {e}")
            return []

    async def set_liquidation_alert(self, user_id: int, min_size: float, alert_type: str = "size"):
        """Set liquidation alert for user"""
        try:
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            
            self.alerts[user_id].append({
                'min_size': min_size,
                'type': alert_type,
                'created_at': datetime.now()
            })
            
            return True
        except Exception as e:
            logger.error(f"Error setting liquidation alert: {e}")
            return False

    async def check_liquidation_alerts(self) -> List[Dict]:
        """Check liquidation alerts and return triggered ones"""
        triggered_alerts = []
        
        try:
            recent_liquidations = await self.get_recent_liquidations(hours=1)  # Check last hour
            
            for user_id, user_alerts in self.alerts.items():
                for alert in user_alerts:
                    min_size = alert['min_size']
                    
                    # Check for large liquidations
                    large_liquidations = [
                        liq for liq in recent_liquidations 
                        if liq.get('size', 0) >= min_size
                    ]
                    
                    if large_liquidations:
                        triggered_alerts.append({
                            'user_id': user_id,
                            'liquidations': large_liquidations,
                            'alert_type': alert['type']
                        })
            
            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking liquidation alerts: {e}")
            return []

    async def format_liquidation_message(self, liquidations: List[Dict], cascade_analysis: Dict = None) -> str:
        """Format liquidation data for display"""
        if not liquidations:
            return "No recent liquidations found."
        
        message = "💥 Recent Liquidations:\n\n"
        
        # Show recent liquidations
        for liq in liquidations[:10]:  # Show last 10
            message += f"🔸 {liq.get('asset', 'Unknown')}:\n"
            message += f"   Size: {liq.get('size', 0):.2f}\n"
            message += f"   Side: {liq.get('side', 'Unknown')}\n"
            message += f"   Time: {datetime.fromtimestamp(liq.get('timestamp', 0)).strftime('%H:%M:%S')}\n\n"
        
        # Add cascade analysis if available
        if cascade_analysis:
            message += f"📊 Cascade Analysis:\n"
            message += f"   Total: {cascade_analysis.get('total_liquidations', 0)}\n"
            message += f"   Largest Cascade: {cascade_analysis.get('largest_cascade', 0)}\n"
            message += f"   Total Volume: {cascade_analysis.get('total_volume', 0):.2f}\n"
        
        return message

    def get_liquidation_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for liquidation commands"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Large Liquidations", callback_data="large_liquidations"),
                InlineKeyboardButton("🌊 Cascade Analysis", callback_data="cascade_analysis")
            ],
            [
                InlineKeyboardButton("🔔 Set Alert", callback_data="set_liquidation_alert")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 
