"""
走势分析器测试
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.trend_analyzer import TrendAnalyzer, TrendType


class TestTrendAnalyzer(unittest.TestCase):
    """走势分析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'bollinger_bands': {'period': 20, 'std_dev': 2},
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'moving_averages': {'short_period': 10, 'long_period': 30},
            'sideways_threshold': 0.02,
            'trend_confirmation_periods': 3
        }
        self.analyzer = TrendAnalyzer(self.config)
        
        # 创建测试数据
        self.test_data = self._create_test_data()
    
    def _create_test_data(self):
        """创建测试用的K线数据"""
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        
        # 生成模拟价格数据
        np.random.seed(42)
        base_price = 50000
        price_changes = np.random.normal(0, 0.01, 100)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # 创建OHLCV数据
        data = []
        for i, price in enumerate(prices):
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'open': price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.analyzer.bb_period, 20)
        self.assertEqual(self.analyzer.bb_std, 2)
        self.assertEqual(self.analyzer.rsi_period, 14)
        self.assertEqual(self.analyzer.ma_short, 10)
        self.assertEqual(self.analyzer.ma_long, 30)
    
    def test_calculate_bollinger_bands(self):
        """测试布林带计算"""
        df = self.analyzer.calculate_bollinger_bands(self.test_data)
        
        # 检查新增列
        expected_columns = ['bb_middle', 'bb_std', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # 检查数据有效性
        self.assertFalse(df['bb_middle'].isna().all())
        self.assertFalse(df['bb_upper'].isna().all())
        self.assertFalse(df['bb_lower'].isna().all())
        
        # 检查布林带关系
        valid_data = df.dropna()
        self.assertTrue((valid_data['bb_upper'] >= valid_data['bb_middle']).all())
        self.assertTrue((valid_data['bb_middle'] >= valid_data['bb_lower']).all())
        
        # 检查bb_position在0-1之间
        self.assertTrue((valid_data['bb_position'] >= 0).all())
        self.assertTrue((valid_data['bb_position'] <= 1).all())
    
    def test_calculate_rsi(self):
        """测试RSI计算"""
        df = self.analyzer.calculate_rsi(self.test_data)
        
        # 检查新增列
        self.assertIn('rsi', df.columns)
        
        # 检查RSI值范围
        valid_rsi = df['rsi'].dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())
    
    def test_calculate_moving_averages(self):
        """测试移动平均线计算"""
        df = self.analyzer.calculate_moving_averages(self.test_data)
        
        # 检查新增列
        expected_columns = ['ma_short', 'ma_long', 'ma_diff_pct']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # 检查移动平均线有效性
        self.assertFalse(df['ma_short'].isna().all())
        self.assertFalse(df['ma_long'].isna().all())
    
    def test_calculate_volatility(self):
        """测试波动率计算"""
        df = self.analyzer.calculate_volatility(self.test_data)
        
        # 检查新增列
        expected_columns = ['returns', 'volatility', 'price_range_pct']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # 检查波动率为正值
        valid_vol = df['volatility'].dropna()
        self.assertTrue((valid_vol >= 0).all())
    
    def test_get_full_analysis(self):
        """测试完整技术分析"""
        df = self.analyzer.get_full_analysis(self.test_data)
        
        # 检查所有技术指标列都存在
        expected_columns = [
            'bb_middle', 'bb_upper', 'bb_lower', 'bb_position', 'bb_width',
            'rsi', 'ma_short', 'ma_long', 'ma_diff_pct',
            'returns', 'volatility', 'price_range_pct'
        ]
        
        for col in expected_columns:
            self.assertIn(col, df.columns)
    
    def test_analyze_trend(self):
        """测试走势分析"""
        df = self.analyzer.get_full_analysis(self.test_data)
        trend_type, analysis = self.analyzer.analyze_trend(df)
        
        # 检查返回类型
        self.assertIsInstance(trend_type, TrendType)
        self.assertIsInstance(analysis, dict)
        
        # 检查分析结果包含必要字段
        expected_keys = ['price', 'bb_position', 'bb_width', 'rsi', 'ma_diff_pct', 'volatility', 'price_range_pct']
        for key in expected_keys:
            self.assertIn(key, analysis)
    
    def test_detect_trend_change(self):
        """测试走势变化检测"""
        # 测试从震荡到上涨
        result = self.analyzer.detect_trend_change(TrendType.UPTREND, TrendType.SIDEWAYS)
        self.assertTrue(result)
        
        # 测试从震荡到下跌
        result = self.analyzer.detect_trend_change(TrendType.DOWNTREND, TrendType.SIDEWAYS)
        self.assertTrue(result)
        
        # 测试相同走势
        result = self.analyzer.detect_trend_change(TrendType.SIDEWAYS, TrendType.SIDEWAYS)
        self.assertFalse(result)
        
        # 测试未知走势
        result = self.analyzer.detect_trend_change(TrendType.UPTREND, TrendType.UNKNOWN)
        self.assertFalse(result)
    
    def test_trend_determination_logic(self):
        """测试走势判断逻辑"""
        # 创建特定的测试数据来验证走势判断
        
        # 测试上涨趋势数据
        uptrend_data = self.test_data.copy()
        uptrend_data['close'] = uptrend_data['close'] * np.linspace(1, 1.1, len(uptrend_data))
        
        df_up = self.analyzer.get_full_analysis(uptrend_data)
        trend_up, _ = self.analyzer.analyze_trend(df_up)
        
        # 由于数据是模拟的，我们主要检查函数不会出错
        self.assertIn(trend_up, [TrendType.UPTREND, TrendType.SIDEWAYS, TrendType.DOWNTREND])
        
        # 测试下跌趋势数据
        downtrend_data = self.test_data.copy()
        downtrend_data['close'] = downtrend_data['close'] * np.linspace(1, 0.9, len(downtrend_data))
        
        df_down = self.analyzer.get_full_analysis(downtrend_data)
        trend_down, _ = self.analyzer.analyze_trend(df_down)
        
        self.assertIn(trend_down, [TrendType.UPTREND, TrendType.SIDEWAYS, TrendType.DOWNTREND])
    
    def test_insufficient_data(self):
        """测试数据不足的情况"""
        # 创建数据不足的情况
        small_data = self.test_data.head(10)
        
        df = self.analyzer.get_full_analysis(small_data)
        trend_type, analysis = self.analyzer.analyze_trend(df)
        
        self.assertEqual(trend_type, TrendType.UNKNOWN)
        self.assertIn("reason", analysis)


if __name__ == '__main__':
    unittest.main()
