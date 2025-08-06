"""
币安API数据获取模块
提供K线数据获取和实时价格监控功能
"""

import requests
import pandas as pd
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BinanceAPI:
    """币安公共API接口类"""

    def __init__(self, base_url: str = None, use_proxy: bool = False, proxy_config: Dict = None):
        # 默认使用国外可访问的API端点
        if base_url is None:
            # 优先使用币安国际版API，如果不可用则尝试其他端点
            self.api_endpoints = [
                "https://data-api.binance.vision"  # 币安数据API，通常更稳定
            ]
            self.base_url = self.api_endpoints[0]
        else:
            self.base_url = base_url
            self.api_endpoints = [base_url]

        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_interval = 0.1  # 100ms between requests

        # 配置代理
        if use_proxy and proxy_config:
            self.session.proxies.update(proxy_config)

        # 设置请求头，模拟浏览器访问
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def _rate_limit(self):
        """实现请求频率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_interval:
            time.sleep(self.rate_limit_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送API请求，支持多个端点重试"""
        self._rate_limit()

        last_exception = None

        # 尝试所有可用的API端点
        for api_url in self.api_endpoints:
            url = f"{api_url}{endpoint}"
            try:
                logger.debug(f"尝试请求: {url}")
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()

                # 如果成功，更新当前使用的base_url
                if self.base_url != api_url:
                    logger.info(f"切换到API端点: {api_url}")
                    self.base_url = api_url

                return response.json()

            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"API端点 {api_url} 请求失败: {e}")
                continue

        # 所有端点都失败
        logger.error(f"所有API端点都无法访问，最后错误: {last_exception}")
        raise last_exception
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号，如 'BTCUSDT'
            interval: 时间间隔，如 '1m', '5m', '1h', '1d'
            limit: 返回数据条数，最大1000
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            
        Returns:
            包含K线数据的DataFrame
        """
        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
            
        try:
            data = self._make_request(endpoint, params)
            
            # 转换为DataFrame
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # 时间戳转换
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # 设置索引
            df.set_index('open_time', inplace=True)
            
            logger.info(f"成功获取 {symbol} {interval} K线数据，共 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {symbol} {interval} - {e}")
            raise
    
    def get_ticker_price(self, symbol: str) -> float:
        """
        获取当前价格
        
        Args:
            symbol: 交易对符号
            
        Returns:
            当前价格
        """
        endpoint = "/api/v3/ticker/price"
        params = {"symbol": symbol}
        
        try:
            data = self._make_request(endpoint, params)
            price = float(data['price'])
            logger.debug(f"{symbol} 当前价格: {price}")
            return price
        except Exception as e:
            logger.error(f"获取价格失败: {symbol} - {e}")
            raise
    
    def get_24hr_ticker(self, symbol: str) -> Dict:
        """
        获取24小时价格变动统计
        
        Args:
            symbol: 交易对符号
            
        Returns:
            24小时统计数据
        """
        endpoint = "/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        
        try:
            data = self._make_request(endpoint, params)
            
            # 转换数值类型
            numeric_fields = ['priceChange', 'priceChangePercent', 'weightedAvgPrice',
                            'prevClosePrice', 'lastPrice', 'bidPrice', 'askPrice',
                            'openPrice', 'highPrice', 'lowPrice', 'volume', 'quoteVolume']
            
            for field in numeric_fields:
                if field in data:
                    data[field] = float(data[field])
            
            logger.debug(f"{symbol} 24小时统计获取成功")
            return data
        except Exception as e:
            logger.error(f"获取24小时统计失败: {symbol} - {e}")
            raise
    
    def get_exchange_info(self, symbol: str = None) -> Dict:
        """
        获取交易规则和交易对信息
        
        Args:
            symbol: 可选，指定交易对
            
        Returns:
            交易所信息
        """
        endpoint = "/api/v3/exchangeInfo"
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        try:
            data = self._make_request(endpoint, params)
            logger.debug("交易所信息获取成功")
            return data
        except Exception as e:
            logger.error(f"获取交易所信息失败: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """
        测试API连接性
        
        Returns:
            连接是否正常
        """
        endpoint = "/api/v3/ping"
        
        try:
            self._make_request(endpoint)
            logger.info("API连接测试成功")
            return True
        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False
