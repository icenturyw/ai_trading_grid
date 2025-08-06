"""
多周期监测系统
实现对多个时间周期的同时监测功能
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from .binance_api import BinanceAPI
from .trend_analyzer import TrendAnalyzer, TrendType
from .alerts import AlertManager
from .alternative_data import AlternativeDataSource, HybridDataSource

logger = logging.getLogger(__name__)


class TrendMonitor:
    """走势监测器"""
    
    def __init__(self, config: Dict):
        """
        初始化监测器
        
        Args:
            config: 配置参数
        """
        self.config = config
        self.symbols = config.get('symbols', [])
        self.timeframes = config.get('timeframes', [])
        self.monitoring_interval = config.get('monitoring_interval', 60)
        
        # 初始化组件
        api_config = config.get('api', {})

        # 初始化币安API
        binance_api = BinanceAPI(
            base_url=api_config.get('base_url'),
            use_proxy=api_config.get('use_proxy', False),
            proxy_config=api_config.get('proxy_config')
        )

        # 初始化备用数据源
        alternative_source = AlternativeDataSource()

        # 使用混合数据源
        self.api = HybridDataSource(binance_api, alternative_source)

        self.analyzer = TrendAnalyzer(config.get('analysis', {}))
        self.alert_manager = AlertManager(config.get('alerts', {}))
        
        # 存储历史走势数据
        self.trend_history = {}
        
        # 监测状态
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 线程锁
        self.lock = threading.Lock()
        
        logger.info(f"监测器初始化完成 - 币种: {len(self.symbols)}, 周期: {len(self.timeframes)}")
    
    def start_monitoring(self):
        """开始监测"""
        if self.is_monitoring:
            logger.warning("监测已在运行中")
            return
        
        # 测试API连接
        if not self.api.test_connectivity():
            self.alert_manager.send_system_alert('ERROR', 'API连接测试失败，无法开始监测')
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.alert_manager.send_system_alert('INFO', '走势监测已开始')
        logger.info("走势监测已开始")
    
    def stop_monitoring(self):
        """停止监测"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.alert_manager.send_system_alert('INFO', '走势监测已停止')
        logger.info("走势监测已停止")
    
    def _monitoring_loop(self):
        """监测主循环"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # 执行一轮监测
                self._perform_monitoring_round()
                
                # 计算下次监测时间
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - elapsed_time)
                
                logger.debug(f"监测轮次完成，耗时: {elapsed_time:.2f}s，等待: {sleep_time:.2f}s")
                
                # 等待下次监测
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"监测循环出错: {e}")
                self.alert_manager.send_system_alert('ERROR', f'监测循环出错: {str(e)}')
                time.sleep(10)  # 出错后等待10秒再继续
    
    def _perform_monitoring_round(self):
        """执行一轮监测"""
        logger.info("开始新的监测轮次")
        
        # 使用线程池并行处理多个监测任务
        with ThreadPoolExecutor(max_workers=min(10, len(self.symbols) * len(self.timeframes))) as executor:
            # 提交所有监测任务
            futures = []
            for symbol in self.symbols:
                for timeframe in self.timeframes:
                    future = executor.submit(self._monitor_symbol_timeframe, symbol, timeframe)
                    futures.append(future)
            
            # 等待所有任务完成
            completed_count = 0
            error_count = 0
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        completed_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"监测任务执行失败: {e}")
        
        logger.info(f"监测轮次完成 - 成功: {completed_count}, 失败: {error_count}")
    
    def _monitor_symbol_timeframe(self, symbol: str, timeframe: str) -> bool:
        """
        监测单个币种的单个时间周期
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            
        Returns:
            是否成功
        """
        try:
            # 获取K线数据
            df = self.api.get_klines(symbol, timeframe, limit=100)
            
            if df.empty:
                logger.warning(f"获取K线数据为空: {symbol} {timeframe}")
                return False
            
            # 进行技术分析
            df_analyzed = self.analyzer.get_full_analysis(df)
            
            # 分析当前走势
            current_trend, analysis = self.analyzer.analyze_trend(df_analyzed)
            
            # 获取历史走势
            key = f"{symbol}_{timeframe}"
            with self.lock:
                previous_trend = self.trend_history.get(key, TrendType.UNKNOWN)
                self.trend_history[key] = current_trend
            
            # 检测走势变化
            if self.analyzer.detect_trend_change(current_trend, previous_trend):
                # 发送告警
                self.alert_manager.send_trend_change_alert(
                    symbol=symbol,
                    timeframe=timeframe,
                    previous_trend=previous_trend.value,
                    current_trend=current_trend.value,
                    analysis=analysis,
                    price=analysis['price']
                )
            
            logger.debug(f"监测完成: {symbol} {timeframe} - {current_trend.value}")
            return True
            
        except Exception as e:
            logger.error(f"监测失败: {symbol} {timeframe} - {e}")
            return False
    
    def get_current_status(self) -> Dict:
        """
        获取当前监测状态
        
        Returns:
            监测状态信息
        """
        with self.lock:
            trend_summary = {}
            for key, trend in self.trend_history.items():
                symbol, timeframe = key.split('_')
                if symbol not in trend_summary:
                    trend_summary[symbol] = {}
                trend_summary[symbol][timeframe] = trend.value
        
        return {
            'is_monitoring': self.is_monitoring,
            'symbols_count': len(self.symbols),
            'timeframes_count': len(self.timeframes),
            'total_pairs': len(self.symbols) * len(self.timeframes),
            'trend_summary': trend_summary,
            'alert_stats': self.alert_manager.get_alert_statistics()
        }
    
    def get_symbol_analysis(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        获取指定币种和周期的详细分析
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            
        Returns:
            详细分析结果
        """
        try:
            # 获取K线数据
            df = self.api.get_klines(symbol, timeframe, limit=100)
            
            if df.empty:
                return None
            
            # 进行技术分析
            df_analyzed = self.analyzer.get_full_analysis(df)
            
            # 分析当前走势
            current_trend, analysis = self.analyzer.analyze_trend(df_analyzed)
            
            # 获取最新的技术指标
            latest = df_analyzed.iloc[-1]
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_trend': current_trend.value,
                'price': latest['close'],
                'analysis': analysis,
                'technical_indicators': {
                    'bb_upper': latest['bb_upper'],
                    'bb_middle': latest['bb_middle'],
                    'bb_lower': latest['bb_lower'],
                    'bb_position': latest['bb_position'],
                    'bb_width': latest['bb_width'],
                    'rsi': latest['rsi'],
                    'ma_short': latest['ma_short'],
                    'ma_long': latest['ma_long'],
                    'ma_diff_pct': latest['ma_diff_pct'],
                    'volatility': latest['volatility'],
                    'volume': latest['volume']
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取分析失败: {symbol} {timeframe} - {e}")
            return None
    
    def add_symbol(self, symbol: str):
        """
        添加监测币种
        
        Args:
            symbol: 交易对符号
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"添加监测币种: {symbol}")
            self.alert_manager.send_system_alert('INFO', f'添加监测币种: {symbol}')
    
    def remove_symbol(self, symbol: str):
        """
        移除监测币种
        
        Args:
            symbol: 交易对符号
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            
            # 清理历史数据
            with self.lock:
                keys_to_remove = [key for key in self.trend_history.keys() if key.startswith(f"{symbol}_")]
                for key in keys_to_remove:
                    del self.trend_history[key]
            
            logger.info(f"移除监测币种: {symbol}")
            self.alert_manager.send_system_alert('INFO', f'移除监测币种: {symbol}')
    
    def update_config(self, new_config: Dict):
        """
        更新配置
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        
        # 更新组件配置
        if 'analysis' in new_config:
            self.analyzer = TrendAnalyzer(new_config['analysis'])
        
        if 'alerts' in new_config:
            self.alert_manager = AlertManager(new_config['alerts'])
        
        if 'monitoring_interval' in new_config:
            self.monitoring_interval = new_config['monitoring_interval']
        
        logger.info("配置已更新")
        self.alert_manager.send_system_alert('INFO', '监测配置已更新')
