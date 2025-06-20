import aiohttp
import asyncio
import websockets
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HyperliquidAPI:
    def __init__(self):
        self.base_url = "https://api.hyperliquid.xyz"
        self.ws_url = "wss://api.hyperliquid.xyz/ws"
        self._ws = None
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """Make HTTP request to Hyperliquid API"""
        session = await self._get_session()
        try:
            logger.info(f"Making request to {endpoint} with payload: {payload}")
            async with session.post(f"{self.base_url}{endpoint}", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Received response: {data}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"API Error: {response.status} - {error_text}")
                    return {}
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {}

    async def get_asset_contexts(self) -> List[Dict]:
        """Get all market data in one request"""
        data = await self._make_request("/info", {"type": "metaAndAssetCtxs"})
        if not data:
            logger.error("No data received from API")
            return []

        try:
            if not isinstance(data, list) or len(data) < 2:
                logger.error(f"Invalid data structure: {data}")
                return []

            # Get asset names from metadata
            metadata = data[0]
            if not isinstance(metadata, dict):
                logger.error("Invalid metadata format")
                return []
                
            # Extract asset names from the metadata structure
            asset_names = []
            if "assetMeta" in metadata:
                asset_names = [meta.get("name") for meta in metadata["assetMeta"]]
            elif "universe" in metadata:
                asset_names = [asset.get("name") for asset in metadata["universe"]]
                
            if not asset_names:
                logger.error("No asset names found in metadata")
                return []
                
            logger.info(f"Found {len(asset_names)} asset names")

            contexts = data[1]
            if not isinstance(contexts, list):
                logger.error(f"Invalid contexts structure: {contexts}")
                return []

            parsed_contexts = []
            for i, asset in enumerate(contexts):
                try:
                    if not isinstance(asset, dict):
                        continue
                        
                    if i >= len(asset_names):
                        logger.error(f"Index {i} out of range for asset names")
                        continue
                        
                    name = asset_names[i]
                    if not name:
                        logger.error(f"No name found for asset index {i}")
                        continue
                    
                    parsed_asset = {
                        "name": name,
                        "markPx": float(asset.get("markPx", 0)),
                        "openInterest": float(asset.get("openInterest", 0)),
                        "funding": float(asset.get("funding", 0)),
                        "dayVolume": float(asset.get("dayNtlVlm", 0)),
                        "timestamp": int(datetime.now().timestamp())
                    }
                    
                    logger.info(f"Successfully parsed asset {name}: funding={parsed_asset['funding']}")
                    parsed_contexts.append(parsed_asset)
                except Exception as e:
                    logger.error(f"Error parsing asset {i}: {str(e)}")
                    continue

            logger.info(f"Successfully parsed {len(parsed_contexts)} assets")
            return parsed_contexts

        except Exception as e:
            logger.error(f"Error parsing asset contexts: {str(e)}")
            return []

    async def get_funding_rates(self) -> List[Dict]:
        """Get current funding rates"""
        contexts = await self.get_asset_contexts()
        if not contexts:
            logger.error("No contexts available for funding rates")
            return []

        try:
            funding_rates = []
            for asset in contexts:
                try:
                    if not asset.get("name") or asset.get("funding") is None:
                        continue
                        
                    funding_rates.append({
                        "token": asset["name"],
                        "rate": float(asset["funding"]),
                        "timestamp": asset["timestamp"]
                    })
                    logger.info(f"Added funding rate for {asset['name']}: {asset['funding']}")
                except Exception as e:
                    logger.error(f"Error processing asset {asset}: {str(e)}")
                    continue
                    
            logger.info(f"Found {len(funding_rates)} funding rates")
            return funding_rates
        except Exception as e:
            logger.error(f"Error parsing funding rates: {str(e)}")
            return []

    async def get_open_interest(self) -> Dict:
        """Get Open Interest data"""
        contexts = await self.get_asset_contexts()
        if not contexts:
            logger.error("No contexts available for open interest")
            return {}

        try:
            oi_data = {}
            for asset in contexts:
                if asset.get("openInterest") is not None:
                    oi_data[asset["name"]] = {
                        "value": float(asset["openInterest"]),
                        "timestamp": asset["timestamp"]
                    }
            logger.info(f"Found open interest data for {len(oi_data)} assets")
            return oi_data
        except Exception as e:
            logger.error(f"Error parsing open interest: {str(e)}")
            return {}

    async def get_volume(self) -> Dict:
        """Get volume data"""
        contexts = await self.get_asset_contexts()
        if not contexts:
            logger.error("No contexts available for volume")
            return {}

        try:
            volume_data = {}
            for asset in contexts:
                if asset.get("dayVolume") is not None:
                    volume_data[asset["name"]] = {
                        "value": float(asset["dayVolume"]),
                        "timestamp": asset["timestamp"]
                    }
            logger.info(f"Found volume data for {len(volume_data)} assets")
            return volume_data
        except Exception as e:
            logger.error(f"Error parsing volume: {str(e)}")
            return {}

    async def get_liquidations(self) -> List[Dict]:
        """Get recent liquidations"""
        if not self._ws:
            await self.connect_ws()
        
        try:
            # Subscribe to liquidation events
            await self._ws.send(json.dumps({
                "method": "subscribe",
                "params": ["liquidation"]
            }))
            
            # Wait for messages
            liquidations = []
            start_time = datetime.now()
            while (datetime.now() - start_time).seconds < 5:  # Wait up to 5 seconds
                try:
                    msg = await asyncio.wait_for(self._ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if "liquidation" in data:
                        liquidations.append(data["liquidation"])
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing liquidation message: {str(e)}")
                    continue
            
            logger.info(f"Found {len(liquidations)} liquidations")
            return liquidations
        except Exception as e:
            logger.error(f"Error getting liquidations: {str(e)}")
            return []

    async def connect_ws(self):
        """Connect to WebSocket"""
        try:
            self._ws = await websockets.connect(self.ws_url)
            logger.info("WebSocket connected successfully")
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            self._ws = None

    async def close(self):
        """Close all connections"""
        if self._ws:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close() 
            self._ws = None 

    async def get_funding_history_batch(self, coins: List[str], start_time: int, end_time: int) -> Dict[str, List[Dict]]:
        """Get historical funding rates for multiple coins in one request"""
        if not coins:
            return {}
            
        try:
            # Prepare batch request
            payload = {
                "type": "fundingHistoryBatch",
                "coins": coins,
                "startTime": start_time,
                "endTime": end_time
            }
            
            data = await self._make_request("/info", payload)
            if not data:
                logger.error("No funding history data received")
                return {}
                
            # Process response
            result = {}
            for coin, history in data.items():
                if isinstance(history, list):
                    result[coin] = history
                    
            return result
        except Exception as e:
            logger.error(f"Error getting batch funding history: {str(e)}")
            return {} 