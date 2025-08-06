"""
应用功能测试脚本
"""

import sys
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / 'src'))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    try:
        from src.config_manager import ConfigManager
        from src.binance_api import BinanceAPI
        from src.trend_analyzer import TrendAnalyzer, TrendType
        from src.alerts import AlertManager
        from src.alternative_data import AlternativeDataSource, HybridDataSource
        from src.monitor import TrendMonitor
        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")
    try:
        from src.config_manager import ConfigManager
        
        config_manager = ConfigManager('config.yaml')
        config = config_manager.get_config()
        
        # 检查必要的配置项
        required_keys = ['symbols', 'timeframes', 'analysis', 'alerts', 'api']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"缺少配置项: {key}")
        
        print("✓ 配置管理器测试成功")
        return True, config
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        return False, None

def test_alternative_data_source():
    """测试备用数据源"""
    print("\n测试备用数据源...")
    try:
        from src.alternative_data import AlternativeDataSource
        
        alt_source = AlternativeDataSource()
        
        # 测试连接性
        connectivity = alt_source.test_connectivity()
        print(f"连接测试结果: {connectivity}")
        
        # 测试获取价格
        price = alt_source.get_current_price_coingecko('BTCUSDT')
        if price:
            print(f"✓ 成功获取BTC价格: ${price}")
        else:
            print("⚠ 无法获取价格，但模块正常")
        
        print("✓ 备用数据源测试成功")
        return True
    except Exception as e:
        print(f"✗ 备用数据源测试失败: {e}")
        return False

def test_trend_analyzer():
    """测试走势分析器"""
    print("\n测试走势分析器...")
    try:
        import pandas as pd
        import numpy as np
        from src.trend_analyzer import TrendAnalyzer, TrendType
        
        # 创建测试配置
        config = {
            'bollinger_bands': {'period': 20, 'std_dev': 2},
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'moving_averages': {'short_period': 10, 'long_period': 30},
            'sideways_threshold': 0.02,
            'trend_confirmation_periods': 3
        }
        
        analyzer = TrendAnalyzer(config)
        
        # 创建测试数据
        dates = pd.date_range('2024-01-01', periods=50, freq='1H')
        np.random.seed(42)
        prices = 50000 + np.cumsum(np.random.normal(0, 100, 50))
        
        test_data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.uniform(100, 1000, 50)
        }, index=dates)
        
        # 测试技术分析
        df_analyzed = analyzer.get_full_analysis(test_data)
        trend_type, analysis = analyzer.analyze_trend(df_analyzed)
        
        print(f"✓ 走势分析成功，当前走势: {trend_type.value}")
        print(f"  分析结果: RSI={analysis.get('rsi', 0):.2f}, 价格=${analysis.get('price', 0):.2f}")
        
        return True
    except Exception as e:
        print(f"✗ 走势分析器测试失败: {e}")
        return False

def test_alert_manager():
    """测试告警管理器"""
    print("\n测试告警管理器...")
    try:
        from src.alerts import AlertManager
        
        config = {
            'console_output': True,
            'log_file': 'test_alerts.log',
            'email_notifications': False,
            'webhook_url': None
        }
        
        alert_manager = AlertManager(config)
        
        # 测试系统告警
        alert_manager.send_system_alert('INFO', '测试告警消息')
        
        # 测试走势变化告警
        analysis = {
            'price': 50000.0,
            'rsi': 65.5,
            'bb_position': 0.7,
            'bb_width': 0.02,
            'ma_diff_pct': 1.5,
            'volatility': 0.15
        }
        
        alert_manager.send_trend_change_alert(
            symbol='BTCUSDT',
            timeframe='1h',
            previous_trend='震荡',
            current_trend='上涨',
            analysis=analysis,
            price=50000.0
        )
        
        print("✓ 告警管理器测试成功")
        return True
    except Exception as e:
        print(f"✗ 告警管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("币种走势监测系统 - 功能测试")
    print("=" * 60)
    
    # 测试计数
    total_tests = 5
    passed_tests = 0
    
    # 1. 测试模块导入
    if test_imports():
        passed_tests += 1
    
    # 2. 测试配置管理器
    config_success, config = test_config_manager()
    if config_success:
        passed_tests += 1
    
    # 3. 测试备用数据源
    if test_alternative_data_source():
        passed_tests += 1
    
    # 4. 测试走势分析器
    if test_trend_analyzer():
        passed_tests += 1
    
    # 5. 测试告警管理器
    if test_alert_manager():
        passed_tests += 1
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print(f"测试完成: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！应用可以正常运行")
        
        if config:
            print(f"\n配置摘要:")
            print(f"  监测币种: {len(config['symbols'])} 个")
            print(f"  监测周期: {len(config['timeframes'])} 个")
            print(f"  监测间隔: {config['monitoring_interval']} 秒")
        
        print(f"\n使用方法:")
        print(f"  测试连接: python main.py --test")
        print(f"  启动监测: python main.py")
        
    else:
        print("⚠ 部分测试失败，请检查依赖和配置")
    
    print("=" * 60)
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
