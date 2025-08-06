"""
币种走势监测系统主程序
"""

import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from typing import Dict
from colorama import init, Fore, Style

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / 'src'))

from src.config_manager import ConfigManager
from src.monitor import TrendMonitor
from src.binance_api import BinanceAPI
from src.alternative_data import AlternativeDataSource, HybridDataSource

# 初始化colorama
init(autoreset=True)

# 全局变量
monitor = None
config_manager = None


def setup_logging():
    """设置日志系统"""
    # 创建logs目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 配置根logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_dir / 'monitor.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # 设置第三方库日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n{Fore.YELLOW}收到退出信号，正在停止监测...{Style.RESET_ALL}")

    if monitor:
        monitor.stop_monitoring()

    print(f"{Fore.GREEN}程序已安全退出{Style.RESET_ALL}")
    sys.exit(0)


def print_banner():
    """打印程序横幅"""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════╗
║                    币种走势监测系统                          ║
║                  Cryptocurrency Trend Monitor                ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(banner)


def test_api_connection(config: Dict = None):
    """测试API连接"""
    print(f"{Fore.YELLOW}正在测试API连接...{Style.RESET_ALL}")

    try:
        if config:
            api_config = config.get('api', {})

            # 测试币安API
            binance_api = BinanceAPI(
                base_url=api_config.get('base_url'),
                use_proxy=api_config.get('use_proxy', False),
                proxy_config=api_config.get('proxy_config')
            )

            # 测试备用数据源
            alternative_source = AlternativeDataSource()

            # 创建混合数据源
            hybrid_api = HybridDataSource(binance_api, alternative_source)

            # 测试所有连接
            results = hybrid_api.test_connectivity()

            print(f"\n{Fore.CYAN}连接测试结果:{Style.RESET_ALL}")
            success_count = 0
            for source, status in results.items():
                color = Fore.GREEN if status else Fore.RED
                symbol = "✓" if status else "✗"
                print(f"  {color}{symbol} {source.upper()}: {'连接成功' if status else '连接失败'}{Style.RESET_ALL}")
                if status:
                    success_count += 1

            if success_count > 0:
                print(f"\n{Fore.GREEN}✓ 至少有 {success_count} 个数据源可用{Style.RESET_ALL}")
                return True
            else:
                print(f"\n{Fore.RED}✗ 所有数据源都不可用{Style.RESET_ALL}")
                return False
        else:
            # 简单测试
            api = BinanceAPI()
            if api.test_connectivity():
                print(f"{Fore.GREEN}✓ 币安API连接测试成功{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}✗ 币安API连接测试失败{Style.RESET_ALL}")
                return False

    except Exception as e:
        print(f"{Fore.RED}✗ API连接测试出错: {e}{Style.RESET_ALL}")
        return False


def interactive_mode():
    """交互模式"""
    global monitor, config_manager

    print(f"\n{Fore.GREEN}进入交互模式，输入 'help' 查看可用命令{Style.RESET_ALL}")

    while True:
        try:
            command = input(f"\n{Fore.CYAN}monitor> {Style.RESET_ALL}").strip().lower()

            if command == 'help':
                show_help()
            elif command == 'start':
                start_monitoring()
            elif command == 'stop':
                stop_monitoring()
            elif command == 'status':
                show_status()
            elif command == 'config':
                show_config()
            elif command.startswith('add '):
                symbol = command[4:].upper()
                add_symbol(symbol)
            elif command.startswith('remove '):
                symbol = command[7:].upper()
                remove_symbol(symbol)
            elif command.startswith('analyze '):
                parts = command[8:].split()
                if len(parts) >= 2:
                    analyze_symbol(parts[0].upper(), parts[1])
                else:
                    print(f"{Fore.RED}用法: analyze <symbol> <timeframe>{Style.RESET_ALL}")
            elif command == 'stats':
                show_statistics()
            elif command in ['quit', 'exit', 'q']:
                break
            elif command == '':
                continue
            else:
                print(f"{Fore.RED}未知命令: {command}，输入 'help' 查看帮助{Style.RESET_ALL}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Fore.RED}命令执行出错: {e}{Style.RESET_ALL}")

    # 退出前停止监测
    if monitor and monitor.is_monitoring:
        monitor.stop_monitoring()


def show_help():
    """显示帮助信息"""
    help_text = f"""
{Fore.CYAN}{Style.BRIGHT}可用命令:{Style.RESET_ALL}

{Fore.GREEN}监测控制:{Style.RESET_ALL}
  start                    - 开始监测
  stop                     - 停止监测
  status                   - 显示监测状态

{Fore.GREEN}配置管理:{Style.RESET_ALL}
  config                   - 显示当前配置
  add <symbol>             - 添加监测币种 (如: add ADAUSDT)
  remove <symbol>          - 移除监测币种 (如: remove ADAUSDT)

{Fore.GREEN}分析查询:{Style.RESET_ALL}
  analyze <symbol> <timeframe> - 分析指定币种和周期 (如: analyze BTCUSDT 1h)
  stats                    - 显示告警统计

{Fore.GREEN}系统命令:{Style.RESET_ALL}
  help                     - 显示此帮助信息
  quit/exit/q              - 退出程序
"""
    print(help_text)


def start_monitoring():
    """开始监测"""
    global monitor

    if monitor and monitor.is_monitoring:
        print(f"{Fore.YELLOW}监测已在运行中{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}正在启动监测...{Style.RESET_ALL}")
    monitor.start_monitoring()
    print(f"{Fore.GREEN}✓ 监测已启动{Style.RESET_ALL}")


def stop_monitoring():
    """停止监测"""
    global monitor

    if not monitor or not monitor.is_monitoring:
        print(f"{Fore.YELLOW}监测未在运行{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}正在停止监测...{Style.RESET_ALL}")
    monitor.stop_monitoring()
    print(f"{Fore.GREEN}✓ 监测已停止{Style.RESET_ALL}")


def show_status():
    """显示监测状态"""
    global monitor

    if not monitor:
        print(f"{Fore.RED}监测器未初始化{Style.RESET_ALL}")
        return

    status = monitor.get_current_status()

    print(f"\n{Fore.CYAN}{Style.BRIGHT}监测状态:{Style.RESET_ALL}")
    print(f"运行状态: {'🟢 运行中' if status['is_monitoring'] else '🔴 已停止'}")
    print(f"监测币种: {status['symbols_count']} 个")
    print(f"监测周期: {status['timeframes_count']} 个")
    print(f"总监测对: {status['total_pairs']} 个")

    if status['trend_summary']:
        print(f"\n{Fore.CYAN}当前走势:{Style.RESET_ALL}")
        for symbol, trends in status['trend_summary'].items():
            print(f"  {symbol}:")
            for timeframe, trend in trends.items():
                color = Fore.GREEN if trend == '上涨' else Fore.RED if trend == '下跌' else Fore.YELLOW
                print(f"    {timeframe}: {color}{trend}{Style.RESET_ALL}")

    alert_stats = status['alert_stats']
    print(f"\n{Fore.CYAN}告警统计:{Style.RESET_ALL}")
    print(f"  总告警数: {alert_stats['total_alerts']}")
    print(f"  走势变化: {alert_stats['trend_changes']}")
    print(f"  系统告警: {alert_stats['system_alerts']}")


def show_config():
    """显示配置信息"""
    global config_manager

    if not config_manager:
        print(f"{Fore.RED}配置管理器未初始化{Style.RESET_ALL}")
        return

    print(config_manager.get_config_summary())


def add_symbol(symbol: str):
    """添加监测币种"""
    global monitor

    if not monitor:
        print(f"{Fore.RED}监测器未初始化{Style.RESET_ALL}")
        return

    try:
        monitor.add_symbol(symbol)
        print(f"{Fore.GREEN}✓ 已添加监测币种: {symbol}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}添加币种失败: {e}{Style.RESET_ALL}")


def remove_symbol(symbol: str):
    """移除监测币种"""
    global monitor

    if not monitor:
        print(f"{Fore.RED}监测器未初始化{Style.RESET_ALL}")
        return

    try:
        monitor.remove_symbol(symbol)
        print(f"{Fore.GREEN}✓ 已移除监测币种: {symbol}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}移除币种失败: {e}{Style.RESET_ALL}")


def analyze_symbol(symbol: str, timeframe: str):
    """分析指定币种和周期"""
    global monitor

    if not monitor:
        print(f"{Fore.RED}监测器未初始化{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}正在分析 {symbol} {timeframe}...{Style.RESET_ALL}")

    try:
        analysis = monitor.get_symbol_analysis(symbol, timeframe)

        if not analysis:
            print(f"{Fore.RED}获取分析数据失败{Style.RESET_ALL}")
            return

        trend_color = Fore.GREEN if analysis['current_trend'] == '上涨' else Fore.RED if analysis['current_trend'] == '下跌' else Fore.YELLOW

        print(f"\n{Fore.CYAN}{Style.BRIGHT}分析结果:{Style.RESET_ALL}")
        print(f"交易对: {analysis['symbol']}")
        print(f"周期: {analysis['timeframe']}")
        print(f"当前价格: ${analysis['price']:.4f}")
        print(f"当前走势: {trend_color}{analysis['current_trend']}{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}技术指标:{Style.RESET_ALL}")
        indicators = analysis['technical_indicators']
        print(f"  RSI: {indicators['rsi']:.2f}")
        print(f"  布林带上轨: ${indicators['bb_upper']:.4f}")
        print(f"  布林带中轨: ${indicators['bb_middle']:.4f}")
        print(f"  布林带下轨: ${indicators['bb_lower']:.4f}")
        print(f"  短期均线: ${indicators['ma_short']:.4f}")
        print(f"  长期均线: ${indicators['ma_long']:.4f}")
        print(f"  成交量: {indicators['volume']:.2f}")

    except Exception as e:
        print(f"{Fore.RED}分析失败: {e}{Style.RESET_ALL}")


def show_statistics():
    """显示统计信息"""
    global monitor

    if not monitor:
        print(f"{Fore.RED}监测器未初始化{Style.RESET_ALL}")
        return

    status = monitor.get_current_status()
    alert_stats = status['alert_stats']

    print(f"\n{Fore.CYAN}{Style.BRIGHT}系统统计:{Style.RESET_ALL}")
    print(f"监测币种数: {status['symbols_count']}")
    print(f"监测周期数: {status['timeframes_count']}")
    print(f"总监测对数: {status['total_pairs']}")
    print(f"运行状态: {'运行中' if status['is_monitoring'] else '已停止'}")

    print(f"\n{Fore.CYAN}告警统计:{Style.RESET_ALL}")
    print(f"总告警数: {alert_stats['total_alerts']}")
    print(f"走势变化告警: {alert_stats['trend_changes']}")
    print(f"系统告警: {alert_stats['system_alerts']}")


def main():
    """主函数"""
    global monitor, config_manager

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='币种走势监测系统')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    parser.add_argument('--daemon', '-d', action='store_true', help='后台运行模式')
    parser.add_argument('--test', '-t', action='store_true', help='仅测试API连接')
    args = parser.parse_args()

    # 设置日志
    setup_logging()

    # 打印横幅
    if not args.daemon:
        print_banner()

    try:
        # 初始化配置管理器
        print(f"{Fore.YELLOW}正在加载配置...{Style.RESET_ALL}")
        config_manager = ConfigManager(args.config)
        config = config_manager.get_config()
        print(f"{Fore.GREEN}✓ 配置加载成功{Style.RESET_ALL}")

        # 测试API连接
        if not test_api_connection(config):
            print(f"{Fore.RED}所有API连接失败，请检查网络连接或代理设置{Style.RESET_ALL}")
            if args.test:
                return 1
            print(f"{Fore.YELLOW}继续运行可能会遇到问题{Style.RESET_ALL}")

        if args.test:
            print(f"{Fore.GREEN}API连接测试完成{Style.RESET_ALL}")
            return 0

        # 初始化监测器
        print(f"{Fore.YELLOW}正在初始化监测器...{Style.RESET_ALL}")
        monitor = TrendMonitor(config)
        print(f"{Fore.GREEN}✓ 监测器初始化成功{Style.RESET_ALL}")

        if args.daemon:
            # 后台运行模式
            print(f"{Fore.GREEN}启动后台监测模式{Style.RESET_ALL}")
            monitor.start_monitoring()

            # 保持运行
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        else:
            # 交互模式
            interactive_mode()

    except Exception as e:
        print(f"{Fore.RED}程序启动失败: {e}{Style.RESET_ALL}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())