"""
Data Collection Agent - CoinGecko API
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List
import requests
import pandas as pd

logger = logging.getLogger(__name__)

REQUEST_DELAY = 3.0  # Seconds between API calls


class CoinGeckoDataAgent:
    """Agent 1: Data collection from CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, top_n: int = 100):
        self.top_n = top_n
        self.cache_file = "data/crypto_data.json"
        
    def fetch_top_coins(self) -> List[Dict]:
        """Fetch top cryptocurrencies by market cap"""
        logger.info(f"Fetching top {self.top_n} cryptocurrencies...")
        
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.top_n,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            coins = response.json()
            logger.info(f"✓ Fetched {len(coins)} coins")
            return coins
        except Exception as e:
            logger.error(f"Error fetching coins: {e}")
            return []
    
    def fetch_ohlc_with_retry(self, coin_id: str, days: int = 30, max_retries: int = 3) -> pd.DataFrame:
        """Fetch OHLC data with retry logic"""
        url = f"{self.BASE_URL}/coins/{coin_id}/ohlc"
        params = {"vs_currency": "usd", "days": days}
        
        for attempt in range(max_retries):
            try:
                time.sleep(REQUEST_DELAY)
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = REQUEST_DELAY * (attempt + 2)
                    logger.warning(f"Rate limited for {coin_id}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    return pd.DataFrame()
                
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
                
            except requests.exceptions.HTTPError as e:
                if "429" in str(e):
                    wait_time = REQUEST_DELAY * (attempt + 2)
                    time.sleep(wait_time)
                    continue
                logger.error(f"Error fetching OHLC for {coin_id}: {e}")
                return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching OHLC for {coin_id}: {e}")
                return pd.DataFrame()
        
        return pd.DataFrame()
    
    def get_market_context(self) -> Dict:
        """Get global market context"""
        url = f"{self.BASE_URL}/global"
        
        try:
            time.sleep(REQUEST_DELAY)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()['data']
            
            return {
                "btc_dominance": data.get('market_cap_percentage', {}).get('btc', 0),
                "total_market_cap": data.get('total_market_cap', {}).get('usd', 0),
                "total_volume_24h": data.get('total_volume', {}).get('usd', 0),
                "active_cryptocurrencies": data.get('active_cryptocurrencies', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching market context: {e}")
            return {}
    
    def collect_data(self) -> Dict:
        """Main data collection pipeline"""
        logger.info("=== Starting Data Collection ===")
        
        coins = self.fetch_top_coins()
        market_context = self.get_market_context()
        
        crypto_data = {
            "timestamp": datetime.now().isoformat(),
            "market_context": market_context,
            "coins": []
        }
        
        # Filter out stablecoins and wrapped tokens
        excluded = ['USDT', 'USDC', 'DAI', 'BUSD', 'USDS', 'USDE', 'PYUSD', 'TUSD', 'FDUSD', 'USDT0', 'BSC-USD']
        
        tradeable_coins = [c for c in coins if c['symbol'].upper() not in excluded]
        coins_to_process = min(25, len(tradeable_coins))
        
        logger.info(f"Processing {coins_to_process} tradeable coins...")
        
        for i, coin in enumerate(tradeable_coins[:coins_to_process]):
            logger.info(f"Processing {coin['symbol'].upper()} ({i+1}/{coins_to_process})...")
            
            ohlc = self.fetch_ohlc_with_retry(coin['id'], days=30)
            
            if not ohlc.empty and len(ohlc) >= 20:
                ohlc_list = []
                for _, row in ohlc.iterrows():
                    ohlc_list.append({
                        "timestamp": row['timestamp'].isoformat(),
                        "open": float(row['open']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "close": float(row['close'])
                    })
                
                coin_data = {
                    "id": coin['id'],
                    "symbol": coin['symbol'].upper(),
                    "name": coin['name'],
                    "current_price": float(coin['current_price']) if coin['current_price'] else 0,
                    "market_cap": float(coin['market_cap']) if coin['market_cap'] else 0,
                    "total_volume": float(coin['total_volume']) if coin['total_volume'] else 0,
                    "price_change_24h": float(coin.get('price_change_percentage_24h') or 0),
                    "price_change_7d": float(coin.get('price_change_percentage_7d_in_currency') or 0),
                    "ohlc": ohlc_list
                }
                crypto_data['coins'].append(coin_data)
                logger.info(f"  ✓ {coin['symbol'].upper()} saved")
        
        os.makedirs('data', exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(crypto_data, f, indent=2)
        
        logger.info(f"✓ Data collection complete. {len(crypto_data['coins'])} coins saved.")
        return crypto_data
