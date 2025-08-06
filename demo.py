"""
币种走势监测系统演示脚本
"""

import sys
import time
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / 'src'))

def demo_config_manager():
    """演示配置管理器"""
    print("=" * 50)
    print("配置管理器演示")
    print("=" * 50)
    
    try:
        from src.config_manager import ConfigManager
        
        # 加载配置
        config_manager = ConfigManager('config.yaml')
        config = config_manager.get_config()
        
        print("✓ 配置加载成功")
        print(f"监测币种: {config['symbols']}")
        print(f"监测周期: {config['timeframes']}")
        print(f"监测间隔: {config['monitoring_interval']} 秒")
        
        # 显示配置摘要
        print("\n配置摘要:")
        print(config_manager.get_config_summary())
        
        return True
    except Exception as e:
        print(f"✗ 配置管理器演示失败: {e}")
        return False

def demo_alternative_data():
    """演示备用数据源"""
    print("\n" + "=" * 50)
    print("备用数据源演示")
    print("=" * 50)
    
    try:
        from src.alternative_data import AlternativeDataSource
        
        alt_source = AlternativeDataSource()
        
        print("支持的币种:", alt_source.get_supported_symbols())
        
        # 测试连接性
        print("\n测试API连接性...")
        connectivity = alt_source.test_connectivity()
        for api, status in connectivity.items():
            status_text = "✓ 可用" if status else "✗ 不可用"
            print(f"  {api}: {status_text}")
        
        # 尝试获取价格
        print("\n尝试获取BTC价格...")
        price = alt_source.get_current_price_coingecko('BTCUSDT')
        if price:
            print(f"✓ BTC当前价格: ${price:,.2f}")
        else:
            print("⚠ 无法获取价格（可能是网络问题）")
        
        return True
    except Exception as e:
        print(f"✗ 备用数据源演示失败: {e}")
        return False

def demo_trend_analyzer():
    """演示走势分析器"""
    print("\n" + "=" * 50)
    print("走势分析器演示")
    print("=" * 50)
    
    try:
        import pandas as pd
        import numpy as np
        from src.trend_analyzer import TrendAnalyzer, TrendType
        
        # 创建分析器
        config = {
            'bollinger_bands': {'period': 20, 'std_dev': 2},
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'moving_averages': {'short_period': 10, 'long_period': 30},
            'sideways_threshold': 0.02,
            'trend_confirmation_periods': 3
        }
        
        analyzer = TrendAnalyzer(config)
        print("✓ 走势分析器初始化成功")
        
        # 创建模拟数据
        print("\n生成模拟K线数据...")
        dates = pd.date_range('2024-01-01', periods=50, freq='1H')
        np.random.seed(42)
        
        # 模拟上涨趋势
        base_price = 50000
        trend = np.linspace(0, 0.1, 50)  # 10%上涨
        noise = np.random.normal(0, 0.01, 50)  # 1%随机波动
        price_multipliers = 1 + trend + noise
        
        prices = base_price * price_multipliers
        
        test_data = pd.DataFrame({
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, 50))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, 50))),
            'close': prices,
            'volume': np.random.uniform(100, 1000, 50)
        }, index=dates)
        
        print(f"✓ 生成了 {len(test_data)} 条K线数据")
        print(f"价格范围: ${test_data['close'].min():.2f} - ${test_data['close'].max():.2f}")
        
        # 进行技术分析
        print("\n进行技术分析...")
        df_analyzed = analyzer.get_full_analysis(test_data)
        
        # 分析走势
        trend_type, analysis = analyzer.analyze_trend(df_analyzed)
        
        print(f"✓ 分析完成")
        print(f"当前走势: {trend_type.value}")
        print(f"当前价格: ${analysis['price']:.2f}")
        print(f"RSI: {analysis['rsi']:.2f}")
        print(f"布林带位置: {analysis['bb_position']:.2f}")
        print(f"均线差值: {analysis['ma_diff_pct']:.2f}%")
        
        return True
    except Exception as e:
        print(f"✗ 走势分析器演示失败: {e}")
        return False

def demo_alert_system():
    """演示告警系统"""
    print("\n" + "=" * 50)
    print("告警系统演示")
    print("=" * 50)
    
    try:
        from src.alerts import AlertManager
        
        config = {
            'console_output': True,
            'log_file': 'demo_alerts.log',
            'email_notifications': False,
            'webhook_url': None
        }
        
        alert_manager = AlertManager(config)
        print("✓ 告警管理器初始化成功")
        
        # 发送系统告警
        print("\n发送系统告警...")
        alert_manager.send_system_alert('INFO', '这是一个演示系统告警')
        
        # 发送走势变化告警
        print("\n发送走势变化告警...")
        analysis = {
            'price': 52000.0,
            'rsi': 75.5,
            'bb_position': 0.85,
            'bb_width': 0.025,
            'ma_diff_pct': 2.3,
            'volatility': 0.18
        }
        
        alert_manager.send_trend_change_alert(
            symbol='BTCUSDT',
            timeframe='1h',
            previous_trend='震荡',
            current_trend='上涨',
            analysis=analysis,
            price=52000.0
        )
        
        # 获取统计信息
        stats = alert_manager.get_alert_statistics()
        print(f"\n告警统计: {stats}")
        
        return True
    except Exception as e:
        print(f"✗ 告警系统演示失败: {e}")
        return False

def main():
    """主演示函数"""
    print("🚀 币种走势监测系统演示")
    print("本演示将展示系统的主要功能模块\n")
    
    demos = [
        ("配置管理器", demo_config_manager),
        ("备用数据源", demo_alternative_data),
        ("走势分析器", demo_trend_analyzer),
        ("告警系统", demo_alert_system)
    ]
    
    success_count = 0
    
    for name, demo_func in demos:
        try:
            if demo_func():
                success_count += 1
                print(f"✓ {name} 演示成功")
            else:
                print(f"✗ {name} 演示失败")
        except Exception as e:
            print(f"✗ {name} 演示出错: {e}")
        
        time.sleep(1)  # 短暂暂停
    
    print("\n" + "=" * 50)
    print(f"演示完成: {success_count}/{len(demos)} 个模块正常")
    
    if success_count == len(demos):
        print("🎉 所有模块演示成功！")
        print("\n下一步:")
        print("1. 运行 'python main.py --test' 测试API连接")
        print("2. 运行 'python main.py' 启动监测系统")
        print("3. 在交互模式中输入 'help' 查看可用命令")
    else:
        print("⚠ 部分模块可能需要安装额外依赖")
        print("请运行: pip install -r requirements.txt")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
