import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)

class VolumeSpikeAnalyzer:
    def __init__(self):
        self.api = HyperliquidAPI()
        self.alerts = {}  # Store user alerts
        self.historical_data = {}  # Cache historical data

    async def get_volume_data(self) -> Dict[str, Dict]:
        """Get current volume data for all assets"""
        try:
            volume_data = await self.api.get_volume()
            return volume_data
        except Exception as e:
            logger.error(f"Error getting volume data: {e}")
            return {}

    async def analyze_volume_spikes(self, threshold: float = 2.0) -> List[Dict]:
        """Analyze volume spikes compared to historical averages"""
        try:
            volume_data = await self.get_volume_data()
            if not volume_data:
                return []

            spikes = []
            
            for asset, data in volume_data.items():
                current_volume = data.get('value', 0)
                
                # Calculate average volume (this would need historical data)
                # For now, we'll use a simple threshold
                avg_volume = current_volume / 2  # Placeholder
                
                if current_volume > avg_volume * threshold:
                    spike_ratio = current_volume / avg_volume
                    spikes.append({
                        'asset': asset,
                        'current_volume': current_volume,
                        'avg_volume': avg_volume,
                        'spike_ratio': spike_ratio,
                        'timestamp': data.get('timestamp', datetime.now().timestamp())
                    })

            # Sort by spike ratio
            df = pd.DataFrame(spikes)
            df = df.sort_values('spike_ratio', ascending=False)
            
            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Error analyzing volume spikes: {e}")
            return []

    async def detect_volume_patterns(self, hours: int = 24) -> Dict:
        """Detect volume patterns over time"""
        try:
            volume_data = await self.get_volume_data()
            if not volume_data:
                return {}

            # Create DataFrame for analysis
            df = pd.DataFrame([
                {
                    'asset': asset,
                    'volume': data.get('value', 0),
                    'timestamp': data.get('timestamp', datetime.now().timestamp())
                }
                for asset, data in volume_data.items()
            ])

            if df.empty:
                return {}

            # Calculate statistics
            stats = {
                'total_volume': df['volume'].sum(),
                'avg_volume': df['volume'].mean(),
                'max_volume': df['volume'].max(),
                'min_volume': df['volume'].min(),
                'volume_std': df['volume'].std(),
                'top_assets': df.nlargest(5, 'volume')[['asset', 'volume']].to_dict('records')
            }

            return stats

        except Exception as e:
            logger.error(f"Error detecting volume patterns: {e}")
            return {}

    async def set_volume_alert(self, user_id: int, asset: str, threshold: float, alert_type: str = "spike"):
        """Set volume spike alert for user"""
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
            logger.error(f"Error setting volume alert: {e}")
            return False

    async def check_volume_alerts(self) -> List[Dict]:
        """Check volume alerts and return triggered ones"""
        triggered_alerts = []
        
        try:
            volume_data = await self.get_volume_data()
            spikes = await self.analyze_volume_spikes()
            
            for user_id, user_alerts in self.alerts.items():
                for alert in user_alerts:
                    asset = alert['asset']
                    threshold = alert['threshold']
                    
                    # Check for spikes
                    asset_spike = next((spike for spike in spikes if spike['asset'] == asset), None)
                    
                    if asset_spike and asset_spike['spike_ratio'] >= threshold:
                        triggered_alerts.append({
                            'user_id': user_id,
                            'asset': asset,
                            'spike_ratio': asset_spike['spike_ratio'],
                            'current_volume': asset_spike['current_volume'],
                            'alert_type': alert['type']
                        })
            
            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking volume alerts: {e}")
            return []

    async def format_volume_message(self, volume_data: Dict, spikes: List[Dict] = None) -> str:
        """Format volume data for display"""
        if not volume_data:
            return "No volume data available."
        
        message = "📈 Volume Analysis:\n\n"
        
        # Show volume statistics
        if 'total_volume' in volume_data:
            message += f"📊 Total Volume: {volume_data['total_volume']:,.0f}\n"
            message += f"📊 Average Volume: {volume_data['avg_volume']:,.0f}\n"
            message += f"📊 Max Volume: {volume_data['max_volume']:,.0f}\n\n"
        
        # Show top assets by volume
        if 'top_assets' in volume_data:
            message += "🏆 Top Assets by Volume:\n"
            for asset_data in volume_data['top_assets']:
                message += f"🔸 {asset_data['asset']}: {asset_data['volume']:,.0f}\n"
            message += "\n"
        
        # Add spike analysis if available
        if spikes:
            message += "🚨 Volume Spikes:\n"
            for spike in spikes[:5]:  # Show top 5 spikes
                message += f"🔸 {spike['asset']}: {spike['spike_ratio']:.1f}x normal\n"
        
        return message

    def get_volume_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for volume commands"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Volume Stats", callback_data="volume_stats"),
                InlineKeyboardButton("🚨 Spikes", callback_data="volume_spikes")
            ],
            [
                InlineKeyboardButton("🔔 Set Alert", callback_data="set_volume_alert")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 
