import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)

class VolumePriceDivergenceAnalyzer:
    def __init__(self):
        self.api = HyperliquidAPI()
        self.alerts = {}  # Store user alerts
        self.historical_data = {}  # Cache historical data

    async def get_market_data(self) -> Dict[str, Dict]:
        """Get current market data (price and volume) for all assets"""
        try:
            # Get both volume and price data
            volume_data = await self.api.get_volume()
            contexts = await self.api.get_asset_contexts()
            
            market_data = {}
            
            # Combine volume and price data
            for context in contexts:
                asset_name = context.get('name')
                if asset_name:
                    market_data[asset_name] = {
                        'price': context.get('markPx', 0),
                        'volume': context.get('dayVolume', 0),
                        'timestamp': context.get('timestamp', datetime.now().timestamp())
                    }
            
            return market_data

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}

    async def detect_volume_price_divergence(self, threshold: float = 0.5) -> List[Dict]:
        """Detect divergences between volume and price movements"""
        try:
            market_data = await self.get_market_data()
            if not market_data:
                return []

            divergences = []
            
            for asset, data in market_data.items():
                current_price = data.get('price', 0)
                current_volume = data.get('volume', 0)
                
                # This would need historical data for proper analysis
                # For now, we'll use placeholder logic
                
                # Calculate price and volume changes (placeholder)
                price_change = 0  # Would need historical price data
                volume_change = 0  # Would need historical volume data
                
                # Detect divergence patterns
                if abs(volume_change) > threshold and abs(price_change) < threshold * 0.1:
                    # High volume, low price movement
                    divergences.append({
                        'asset': asset,
                        'type': 'volume_spike_no_price',
                        'volume_change': volume_change,
                        'price_change': price_change,
                        'current_price': current_price,
                        'current_volume': current_volume,
                        'severity': 'high' if abs(volume_change) > threshold * 2 else 'medium'
                    })
                
                elif abs(price_change) > threshold and abs(volume_change) < threshold * 0.1:
                    # High price movement, low volume
                    divergences.append({
                        'asset': asset,
                        'type': 'price_spike_low_volume',
                        'volume_change': volume_change,
                        'price_change': price_change,
                        'current_price': current_price,
                        'current_volume': current_volume,
                        'severity': 'high' if abs(price_change) > threshold * 2 else 'medium'
                    })

            # Sort by severity
            df = pd.DataFrame(divergences)
            if not df.empty:
                df = df.sort_values('severity', ascending=False)
                return df.to_dict('records')
            
            return []

        except Exception as e:
            logger.error(f"Error detecting volume-price divergence: {e}")
            return []

    async def analyze_divergence_patterns(self, hours: int = 24) -> Dict:
        """Analyze divergence patterns over time"""
        try:
            divergences = await self.detect_volume_price_divergence()
            if not divergences:
                return {}

            df = pd.DataFrame(divergences)
            
            analysis = {
                'total_divergences': len(divergences),
                'volume_spike_no_price': len(df[df['type'] == 'volume_spike_no_price']),
                'price_spike_low_volume': len(df[df['type'] == 'price_spike_low_volume']),
                'high_severity': len(df[df['severity'] == 'high']),
                'medium_severity': len(df[df['severity'] == 'medium']),
                'top_divergences': df.head(5).to_dict('records')
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing divergence patterns: {e}")
            return {}

    async def set_divergence_alert(self, user_id: int, asset: str, alert_type: str = "any"):
        """Set divergence alert for user"""
        try:
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            
            self.alerts[user_id].append({
                'asset': asset.upper(),
                'type': alert_type,
                'created_at': datetime.now()
            })
            
            return True
        except Exception as e:
            logger.error(f"Error setting divergence alert: {e}")
            return False

    async def check_divergence_alerts(self) -> List[Dict]:
        """Check divergence alerts and return triggered ones"""
        triggered_alerts = []
        
        try:
            divergences = await self.detect_volume_price_divergence()
            
            for user_id, user_alerts in self.alerts.items():
                for alert in user_alerts:
                    asset = alert['asset']
                    alert_type = alert['type']
                    
                    # Find matching divergences
                    asset_divergences = [
                        div for div in divergences 
                        if div['asset'] == asset and 
                        (alert_type == "any" or div['type'] == alert_type)
                    ]
                    
                    if asset_divergences:
                        triggered_alerts.append({
                            'user_id': user_id,
                            'asset': asset,
                            'divergences': asset_divergences,
                            'alert_type': alert_type
                        })
            
            return triggered_alerts

        except Exception as e:
            logger.error(f"Error checking divergence alerts: {e}")
            return []

    async def format_divergence_message(self, divergences: List[Dict], analysis: Dict = None) -> str:
        """Format divergence data for display"""
        if not divergences:
            return "No volume-price divergences detected."
        
        message = "📊 Volume-Price Divergence Analysis:\n\n"
        
        # Show top divergences
        message += "🚨 Detected Divergences:\n"
        for div in divergences[:10]:  # Show top 10
            message += f"🔸 {div['asset']}:\n"
            message += f"   Type: {div['type']}\n"
            message += f"   Severity: {div['severity']}\n"
            message += f"   Volume Change: {div['volume_change']:+.2f}%\n"
            message += f"   Price Change: {div['price_change']:+.2f}%\n\n"
        
        # Add analysis if available
        if analysis:
            message += f"📈 Summary:\n"
            message += f"   Total Divergences: {analysis.get('total_divergences', 0)}\n"
            message += f"   Volume Spikes (No Price): {analysis.get('volume_spike_no_price', 0)}\n"
            message += f"   Price Spikes (Low Volume): {analysis.get('price_spike_low_volume', 0)}\n"
            message += f"   High Severity: {analysis.get('high_severity', 0)}\n"
        
        return message

    def get_divergence_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for divergence commands"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Divergences", callback_data="divergences"),
                InlineKeyboardButton("📈 Analysis", callback_data="divergence_analysis")
            ],
            [
                InlineKeyboardButton("🔔 Set Alert", callback_data="set_divergence_alert")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 
