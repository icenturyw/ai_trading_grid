"""
备用数据源模块
当币安API不可用时，使用其他免费的加密货币数据API
"""

import requests
import pandas as pd
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlternativeDataSource:
    """备用数据源类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 免费的加密货币API端点
        self.apis = {
            'coingecko': {
                'base_url': 'https://api.coingecko.com/api/v3',
                'rate_limit': 1.0  # 1秒间隔
            },
            'coinapi': {
                'base_url': 'https://rest.coinapi.io/v1',
                'rate_limit': 1.0
            },
            'cryptocompare': {
                'base_url': 'https://min-api.cryptocompare.com/data',
                'rate_limit': 1.0
            }
        }
        
        self.last_request_time = 0
        
        # 币种映射（币安格式 -> 其他API格式）
        self.symbol_mapping = {
            'BTCUSDT': {'coingecko': 'bitcoin', 'symbol': 'BTC'},
            'ETHUSDT': {'coingecko': 'ethereum', 'symbol': 'ETH'},
            'BNBUSDT': {'coingecko': 'binancecoin', 'symbol': 'BNB'},
            'ADAUSDT': {'coingecko': 'cardano', 'symbol': 'ADA'},
            'DOTUSDT': {'coingecko': 'polkadot', 'symbol': 'DOT'},
            'LINKUSDT': {'coingecko': 'chainlink', 'symbol': 'LINK'},
            'LTCUSDT': {'coingecko': 'litecoin', 'symbol': 'LTC'},
            'XRPUSDT': {'coingecko': 'ripple', 'symbol': 'XRP'}
        }
    
    def _rate_limit(self, api_name: str):
        """实现请求频率限制"""
        rate_limit = self.apis[api_name]['rate_limit']
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < rate_limit:
            time.sleep(rate_limit - time_since_last)
        self.last_request_time = time.time()
    
    def get_current_price_coingecko(self, symbol: str) -> Optional[float]:
        """
        从CoinGecko获取当前价格
        
        Args:
            symbol: 币安格式的交易对符号
            
        Returns:
            当前价格或None
        """
        try:
            if symbol not in self.symbol_mapping:
                logger.warning(f"不支持的币种: {symbol}")
                return None
            
            coin_id = self.symbol_mapping[symbol]['coingecko']
            self._rate_limit('coingecko')
            
            url = f"{self.apis['coingecko']['base_url']}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = data[coin_id]['usd']
            
            logger.debug(f"CoinGecko价格 {symbol}: ${price}")
            return float(price)
            
        except Exception as e:
            logger.error(f"CoinGecko获取价格失败 {symbol}: {e}")
            return None
    
    def get_historical_data_coingecko(self, symbol: str, days: int = 1) -> Optional[pd.DataFrame]:
        """
        从CoinGecko获取历史数据
        
        Args:
            symbol: 币安格式的交易对符号
            days: 获取天数
            
        Returns:
            历史数据DataFrame或None
        """
        try:
            if symbol not in self.symbol_mapping:
                logger.warning(f"不支持的币种: {symbol}")
                return None
            
            coin_id = self.symbol_mapping[symbol]['coingecko']
            self._rate_limit('coingecko')
            
            url = f"{self.apis['coingecko']['base_url']}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 1 else 'daily'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # 转换数据格式
            prices = data['prices']
            volumes = data['total_volumes']
            
            df_data = []
            for i, (timestamp, price) in enumerate(prices):
                volume = volumes[i][1] if i < len(volumes) else 0
                
                df_data.append({
                    'timestamp': pd.to_datetime(timestamp, unit='ms'),
                    'open': price,  # CoinGecko不提供OHLC，使用价格作为近似
                    'high': price * 1.01,  # 模拟高点
                    'low': price * 0.99,   # 模拟低点
                    'close': price,
                    'volume': volume
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"CoinGecko历史数据 {symbol}: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"CoinGecko获取历史数据失败 {symbol}: {e}")
            return None
    
    def get_klines_alternative(self, symbol: str, interval: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        获取K线数据（备用方案）
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔
            limit: 数据条数
            
        Returns:
            K线数据DataFrame或None
        """
        # 将时间间隔转换为天数
        interval_to_days = {
            '1m': 0.1,
            '5m': 0.2,
            '15m': 0.5,
            '1h': 1,
            '4h': 2,
            '1d': 7
        }
        
        days = interval_to_days.get(interval, 1)
        
        # 首先尝试CoinGecko
        df = self.get_historical_data_coingecko(symbol, days)
        
        if df is not None and len(df) > 0:
            # 根据需要的数据条数截取
            if len(df) > limit:
                df = df.tail(limit)
            
            # 重命名列以匹配币安API格式
            df = df.rename(columns={'timestamp': 'open_time'})
            df['close_time'] = df.index + pd.Timedelta(hours=1)
            
            return df
        
        return None
    
    def test_connectivity(self) -> Dict[str, bool]:
        """
        测试各个备用API的连接性
        
        Returns:
            各API的连接状态
        """
        results = {}
        
        # 测试CoinGecko
        try:
            url = f"{self.apis['coingecko']['base_url']}/ping"
            response = self.session.get(url, timeout=10)
            results['coingecko'] = response.status_code == 200
        except:
            results['coingecko'] = False
        
        # 测试CryptoCompare
        try:
            url = f"{self.apis['cryptocompare']['base_url']}/price"
            params = {'fsym': 'BTC', 'tsyms': 'USD'}
            response = self.session.get(url, params=params, timeout=10)
            results['cryptocompare'] = response.status_code == 200
        except:
            results['cryptocompare'] = False
        
        logger.info(f"备用API连接测试结果: {results}")
        return results
    
    def get_supported_symbols(self) -> List[str]:
        """
        获取支持的交易对列表
        
        Returns:
            支持的交易对列表
        """
        return list(self.symbol_mapping.keys())


class HybridDataSource:
    """混合数据源，优先使用币安API，失败时使用备用源"""
    
    def __init__(self, binance_api, alternative_source):
        self.binance_api = binance_api
        self.alternative_source = alternative_source
        self.use_alternative = False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        获取K线数据，自动切换数据源
        
        Args:
            symbol: 交易对符号
            interval: 时间间隔
            limit: 数据条数
            
        Returns:
            K线数据DataFrame或None
        """
        if not self.use_alternative:
            try:
                # 首先尝试币安API
                df = self.binance_api.get_klines(symbol, interval, limit)
                if df is not None and len(df) > 0:
                    return df
            except Exception as e:
                logger.warning(f"币安API失败，切换到备用数据源: {e}")
                self.use_alternative = True
        
        # 使用备用数据源
        logger.info(f"使用备用数据源获取 {symbol} {interval} 数据")
        return self.alternative_source.get_klines_alternative(symbol, interval, limit)
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格，自动切换数据源
        
        Args:
            symbol: 交易对符号
            
        Returns:
            当前价格或None
        """
        if not self.use_alternative:
            try:
                # 首先尝试币安API
                price = self.binance_api.get_ticker_price(symbol)
                if price is not None:
                    return price
            except Exception as e:
                logger.warning(f"币安API失败，切换到备用数据源: {e}")
                self.use_alternative = True
        
        # 使用备用数据源
        return self.alternative_source.get_current_price_coingecko(symbol)
    
    def test_connectivity(self) -> Dict[str, bool]:
        """
        测试所有数据源的连接性
        
        Returns:
            连接状态字典
        """
        results = {}
        
        # 测试币安API
        try:
            results['binance'] = self.binance_api.test_connectivity()
        except:
            results['binance'] = False
        
        # 测试备用数据源
        alt_results = self.alternative_source.test_connectivity()
        results.update(alt_results)
        
        return results
