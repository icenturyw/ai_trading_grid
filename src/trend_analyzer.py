"""
走势分析模块
实现震荡和单边走势的识别算法
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class TrendType(Enum):
    """走势类型枚举"""
    SIDEWAYS = "震荡"
    UPTREND = "上涨"
    DOWNTREND = "下跌"
    UNKNOWN = "未知"


class TrendAnalyzer:
    """走势分析器"""
    
    def __init__(self, config: Dict):
        """
        初始化分析器
        
        Args:
            config: 分析配置参数
        """
        self.config = config
        self.bb_period = config.get('bollinger_bands', {}).get('period', 20)
        self.bb_std = config.get('bollinger_bands', {}).get('std_dev', 2)
        self.rsi_period = config.get('rsi', {}).get('period', 14)
        self.rsi_overbought = config.get('rsi', {}).get('overbought', 70)
        self.rsi_oversold = config.get('rsi', {}).get('oversold', 30)
        self.ma_short = config.get('moving_averages', {}).get('short_period', 10)
        self.ma_long = config.get('moving_averages', {}).get('long_period', 30)
        self.sideways_threshold = config.get('sideways_threshold', 0.02)
        self.trend_confirmation = config.get('trend_confirmation_periods', 3)
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算布林带指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了布林带指标的DataFrame
        """
        df = df.copy()
        
        # 计算移动平均线
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        
        # 计算标准差
        df['bb_std'] = df['close'].rolling(window=self.bb_period).std()
        
        # 计算上下轨
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * self.bb_std)
        
        # 计算布林带宽度（用于判断震荡程度）
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 计算价格在布林带中的位置
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算RSI指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了RSI指标的DataFrame
        """
        df = df.copy()
        
        # 计算价格变化
        delta = df['close'].diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        
        # 计算RS和RSI
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            添加了移动平均线的DataFrame
        """
        df = df.copy()
        
        df['ma_short'] = df['close'].rolling(window=self.ma_short).mean()
        df['ma_long'] = df['close'].rolling(window=self.ma_long).mean()
        
        # 计算均线差值百分比
        df['ma_diff_pct'] = (df['ma_short'] - df['ma_long']) / df['ma_long'] * 100
        
        return df
    
    def calculate_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        计算价格波动率
        
        Args:
            df: 包含价格数据的DataFrame
            period: 计算周期
            
        Returns:
            添加了波动率指标的DataFrame
        """
        df = df.copy()
        
        # 计算收益率
        df['returns'] = df['close'].pct_change()
        
        # 计算滚动波动率
        df['volatility'] = df['returns'].rolling(window=period).std() * np.sqrt(period)
        
        # 计算价格范围百分比
        df['price_range_pct'] = (df['high'] - df['low']) / df['close'] * 100
        
        return df
    
    def analyze_trend(self, df: pd.DataFrame) -> Tuple[TrendType, Dict]:
        """
        分析当前走势
        
        Args:
            df: 包含所有技术指标的DataFrame
            
        Returns:
            走势类型和详细分析结果
        """
        if len(df) < max(self.bb_period, self.rsi_period, self.ma_long):
            return TrendType.UNKNOWN, {"reason": "数据不足"}
        
        latest = df.iloc[-1]
        recent_data = df.tail(self.trend_confirmation)
        
        analysis = {
            "price": latest['close'],
            "bb_position": latest['bb_position'],
            "bb_width": latest['bb_width'],
            "rsi": latest['rsi'],
            "ma_diff_pct": latest['ma_diff_pct'],
            "volatility": latest['volatility'],
            "price_range_pct": latest['price_range_pct']
        }
        
        # 判断走势类型
        trend_type = self._determine_trend_type(recent_data, analysis)
        
        return trend_type, analysis
    
    def _determine_trend_type(self, recent_data: pd.DataFrame, analysis: Dict) -> TrendType:
        """
        确定走势类型
        
        Args:
            recent_data: 最近几个周期的数据
            analysis: 当前分析结果
            
        Returns:
            走势类型
        """
        # 获取最新数据
        bb_position = analysis['bb_position']
        bb_width = analysis['bb_width']
        rsi = analysis['rsi']
        ma_diff_pct = analysis['ma_diff_pct']
        volatility = analysis['volatility']
        
        # 震荡判断条件
        sideways_conditions = [
            # 布林带宽度较小，表示价格波动收敛
            bb_width < self.sideways_threshold,
            # RSI在中性区域
            30 < rsi < 70,
            # 均线差值较小
            abs(ma_diff_pct) < 2,
            # 价格在布林带中间区域
            0.2 < bb_position < 0.8
        ]
        
        # 上涨趋势判断条件
        uptrend_conditions = [
            # 短期均线在长期均线之上
            ma_diff_pct > 1,
            # 价格接近或突破布林带上轨
            bb_position > 0.7,
            # 最近几个周期价格整体上涨
            recent_data['close'].iloc[-1] > recent_data['close'].iloc[0] * (1 + self.sideways_threshold/2)
        ]
        
        # 下跌趋势判断条件
        downtrend_conditions = [
            # 短期均线在长期均线之下
            ma_diff_pct < -1,
            # 价格接近或突破布林带下轨
            bb_position < 0.3,
            # 最近几个周期价格整体下跌
            recent_data['close'].iloc[-1] < recent_data['close'].iloc[0] * (1 - self.sideways_threshold/2)
        ]
        
        # 判断逻辑
        if sum(sideways_conditions) >= 3:
            return TrendType.SIDEWAYS
        elif sum(uptrend_conditions) >= 2:
            return TrendType.UPTREND
        elif sum(downtrend_conditions) >= 2:
            return TrendType.DOWNTREND
        else:
            return TrendType.SIDEWAYS  # 默认为震荡
    
    def detect_trend_change(self, current_trend: TrendType, previous_trend: TrendType) -> bool:
        """
        检测走势变化
        
        Args:
            current_trend: 当前走势
            previous_trend: 之前走势
            
        Returns:
            是否发生了走势变化
        """
        if previous_trend == TrendType.UNKNOWN:
            return False
            
        # 定义需要告警的走势变化
        alert_changes = [
            (TrendType.SIDEWAYS, TrendType.UPTREND),
            (TrendType.SIDEWAYS, TrendType.DOWNTREND),
            (TrendType.UPTREND, TrendType.SIDEWAYS),
            (TrendType.DOWNTREND, TrendType.SIDEWAYS),
            (TrendType.UPTREND, TrendType.DOWNTREND),
            (TrendType.DOWNTREND, TrendType.UPTREND)
        ]
        
        return (previous_trend, current_trend) in alert_changes
    
    def get_full_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        获取完整的技术分析
        
        Args:
            df: 原始K线数据
            
        Returns:
            包含所有技术指标的DataFrame
        """
        # 计算所有技术指标
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_rsi(df)
        df = self.calculate_moving_averages(df)
        df = self.calculate_volatility(df)
        
        return df
