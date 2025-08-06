"""
告警系统模块
实现走势变化的告警机制
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from colorama import Fore, Back, Style, init
from pathlib import Path

# 初始化colorama
init(autoreset=True)

logger = logging.getLogger(__name__)


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: Dict):
        """
        初始化告警管理器
        
        Args:
            config: 告警配置
        """
        self.config = config
        self.console_output = config.get('console_output', True)
        self.log_file = config.get('log_file', 'alerts.log')
        self.email_notifications = config.get('email_notifications', False)
        self.webhook_url = config.get('webhook_url')
        
        # 设置日志文件
        self._setup_alert_logger()
    
    def _setup_alert_logger(self):
        """设置告警日志记录器"""
        # 创建logs目录
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 配置告警专用logger
        self.alert_logger = logging.getLogger('alerts')
        self.alert_logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not self.alert_logger.handlers:
            # 文件handler
            file_handler = logging.FileHandler(
                log_dir / self.log_file, 
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.alert_logger.addHandler(file_handler)
    
    def send_trend_change_alert(self, symbol: str, timeframe: str, 
                              previous_trend: str, current_trend: str,
                              analysis: Dict, price: float):
        """
        发送走势变化告警
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            previous_trend: 之前的走势
            current_trend: 当前走势
            analysis: 分析数据
            price: 当前价格
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建告警消息
        alert_data = {
            'timestamp': timestamp,
            'symbol': symbol,
            'timeframe': timeframe,
            'previous_trend': previous_trend,
            'current_trend': current_trend,
            'price': price,
            'analysis': analysis
        }
        
        message = self._format_alert_message(alert_data)
        
        # 发送告警
        if self.console_output:
            self._send_console_alert(alert_data, message)
        
        # 记录到日志文件
        self._log_alert(alert_data, message)
        
        # 发送webhook通知
        if self.webhook_url:
            self._send_webhook_alert(alert_data)
        
        logger.info(f"告警已发送: {symbol} {timeframe} {previous_trend} -> {current_trend}")
    
    def _format_alert_message(self, alert_data: Dict) -> str:
        """
        格式化告警消息
        
        Args:
            alert_data: 告警数据
            
        Returns:
            格式化的消息
        """
        symbol = alert_data['symbol']
        timeframe = alert_data['timeframe']
        previous_trend = alert_data['previous_trend']
        current_trend = alert_data['current_trend']
        price = alert_data['price']
        analysis = alert_data['analysis']
        
        # 判断告警类型和重要性
        alert_type = self._get_alert_type(previous_trend, current_trend)
        
        message = f"""
🚨 走势变化告警 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 交易对: {symbol}
⏰ 周期: {timeframe}
💰 价格: ${price:.4f}
📈 走势变化: {previous_trend} ➜ {current_trend}
🔍 告警类型: {alert_type}

📋 技术分析:
• RSI: {analysis.get('rsi', 0):.2f}
• 布林带位置: {analysis.get('bb_position', 0):.2f}
• 布林带宽度: {analysis.get('bb_width', 0):.4f}
• 均线差值: {analysis.get('ma_diff_pct', 0):.2f}%
• 波动率: {analysis.get('volatility', 0):.4f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return message.strip()
    
    def _get_alert_type(self, previous_trend: str, current_trend: str) -> str:
        """
        获取告警类型
        
        Args:
            previous_trend: 之前走势
            current_trend: 当前走势
            
        Returns:
            告警类型描述
        """
        if previous_trend == "震荡" and current_trend == "上涨":
            return "突破上涨 🚀"
        elif previous_trend == "震荡" and current_trend == "下跌":
            return "突破下跌 📉"
        elif previous_trend == "上涨" and current_trend == "震荡":
            return "上涨转震荡 ⏸️"
        elif previous_trend == "下跌" and current_trend == "震荡":
            return "下跌转震荡 ⏸️"
        elif previous_trend == "上涨" and current_trend == "下跌":
            return "趋势反转 🔄"
        elif previous_trend == "下跌" and current_trend == "上涨":
            return "趋势反转 🔄"
        else:
            return "走势变化 📊"
    
    def _send_console_alert(self, alert_data: Dict, message: str):
        """
        发送控制台告警
        
        Args:
            alert_data: 告警数据
            message: 告警消息
        """
        current_trend = alert_data['current_trend']
        previous_trend = alert_data['previous_trend']
        
        # 根据走势类型选择颜色
        if current_trend == "上涨":
            color = Fore.GREEN
            bg_color = Back.BLACK
        elif current_trend == "下跌":
            color = Fore.RED
            bg_color = Back.BLACK
        else:
            color = Fore.YELLOW
            bg_color = Back.BLACK
        
        # 打印彩色告警
        print(f"\n{bg_color}{color}{Style.BRIGHT}")
        print("=" * 60)
        print(message)
        print("=" * 60)
        print(f"{Style.RESET_ALL}")
    
    def _log_alert(self, alert_data: Dict, message: str):
        """
        记录告警到日志文件
        
        Args:
            alert_data: 告警数据
            message: 告警消息
        """
        # 记录结构化数据
        log_entry = {
            'type': 'trend_change_alert',
            'data': alert_data
        }
        
        self.alert_logger.info(f"ALERT: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # 记录可读消息
        self.alert_logger.info(f"MESSAGE:\n{message}")
    
    def _send_webhook_alert(self, alert_data: Dict):
        """
        发送webhook告警
        
        Args:
            alert_data: 告警数据
        """
        try:
            payload = {
                'type': 'trend_change_alert',
                'data': alert_data,
                'message': self._format_alert_message(alert_data)
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Webhook告警发送成功: {alert_data['symbol']}")
            
        except Exception as e:
            logger.error(f"Webhook告警发送失败: {e}")
    
    def send_system_alert(self, level: str, message: str, details: Dict = None):
        """
        发送系统告警
        
        Args:
            level: 告警级别 (INFO, WARNING, ERROR)
            message: 告警消息
            details: 详细信息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        alert_data = {
            'timestamp': timestamp,
            'type': 'system_alert',
            'level': level,
            'message': message,
            'details': details or {}
        }
        
        # 控制台输出
        if self.console_output:
            color = Fore.WHITE
            if level == 'WARNING':
                color = Fore.YELLOW
            elif level == 'ERROR':
                color = Fore.RED
            
            print(f"{color}[{level}] {timestamp}: {message}{Style.RESET_ALL}")
        
        # 记录日志
        log_message = f"SYSTEM_ALERT: {json.dumps(alert_data, ensure_ascii=False)}"
        
        if level == 'ERROR':
            self.alert_logger.error(log_message)
        elif level == 'WARNING':
            self.alert_logger.warning(log_message)
        else:
            self.alert_logger.info(log_message)
    
    def get_alert_statistics(self) -> Dict:
        """
        获取告警统计信息
        
        Returns:
            告警统计数据
        """
        try:
            log_file_path = Path('logs') / self.log_file
            if not log_file_path.exists():
                return {'total_alerts': 0, 'trend_changes': 0, 'system_alerts': 0}
            
            total_alerts = 0
            trend_changes = 0
            system_alerts = 0
            
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'ALERT:' in line:
                        total_alerts += 1
                        if 'trend_change_alert' in line:
                            trend_changes += 1
                    elif 'SYSTEM_ALERT:' in line:
                        system_alerts += 1
            
            return {
                'total_alerts': total_alerts,
                'trend_changes': trend_changes,
                'system_alerts': system_alerts
            }
            
        except Exception as e:
            logger.error(f"获取告警统计失败: {e}")
            return {'total_alerts': 0, 'trend_changes': 0, 'system_alerts': 0}
