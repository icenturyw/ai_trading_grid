"""
币安API模块测试
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.binance_api import BinanceAPI


class TestBinanceAPI(unittest.TestCase):
    """币安API测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.api = BinanceAPI()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.api.base_url, "https://api.binance.com")
        self.assertIsNotNone(self.api.session)
        self.assertEqual(self.api.rate_limit_interval, 0.1)
    
    @patch('src.binance_api.requests.Session.get')
    def test_make_request_success(self, mock_get):
        """测试成功的API请求"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api._make_request("/test")
        
        self.assertEqual(result, {"test": "data"})
        mock_get.assert_called_once()
    
    @patch('src.binance_api.requests.Session.get')
    def test_make_request_failure(self, mock_get):
        """测试失败的API请求"""
        # 模拟请求异常
        mock_get.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception):
            self.api._make_request("/test")
    
    @patch.object(BinanceAPI, '_make_request')
    def test_get_klines(self, mock_request):
        """测试获取K线数据"""
        # 模拟K线数据
        mock_kline_data = [
            [1640995200000, "47000.00", "47500.00", "46800.00", "47200.00", "100.50",
             1640995259999, "4720000.00", 1000, "50.25", "2360000.00", "0"]
        ]
        mock_request.return_value = mock_kline_data
        
        df = self.api.get_klines("BTCUSDT", "1h", limit=1)
        
        # 验证返回的DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn('open', df.columns)
        self.assertIn('high', df.columns)
        self.assertIn('low', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('volume', df.columns)
        
        # 验证数据类型
        self.assertEqual(df['open'].dtype, 'float64')
        self.assertEqual(df['close'].iloc[0], 47200.00)
    
    @patch.object(BinanceAPI, '_make_request')
    def test_get_ticker_price(self, mock_request):
        """测试获取当前价格"""
        mock_request.return_value = {"symbol": "BTCUSDT", "price": "47000.50"}
        
        price = self.api.get_ticker_price("BTCUSDT")
        
        self.assertEqual(price, 47000.50)
        mock_request.assert_called_once_with("/api/v3/ticker/price", {"symbol": "BTCUSDT"})
    
    @patch.object(BinanceAPI, '_make_request')
    def test_get_24hr_ticker(self, mock_request):
        """测试获取24小时统计"""
        mock_data = {
            "symbol": "BTCUSDT",
            "priceChange": "1000.00",
            "priceChangePercent": "2.17",
            "lastPrice": "47000.00",
            "volume": "1000.50"
        }
        mock_request.return_value = mock_data
        
        result = self.api.get_24hr_ticker("BTCUSDT")
        
        self.assertEqual(result['symbol'], "BTCUSDT")
        self.assertEqual(result['priceChange'], 1000.00)
        self.assertEqual(result['priceChangePercent'], 2.17)
        self.assertEqual(result['lastPrice'], 47000.00)
    
    @patch.object(BinanceAPI, '_make_request')
    def test_test_connectivity_success(self, mock_request):
        """测试连接性检查成功"""
        mock_request.return_value = {}
        
        result = self.api.test_connectivity()
        
        self.assertTrue(result)
        mock_request.assert_called_once_with("/api/v3/ping")
    
    @patch.object(BinanceAPI, '_make_request')
    def test_test_connectivity_failure(self, mock_request):
        """测试连接性检查失败"""
        mock_request.side_effect = Exception("Connection failed")
        
        result = self.api.test_connectivity()
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
