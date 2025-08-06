"""
配置管理模块
处理配置文件的加载、验证和更新
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = {}
        self.default_config = self._get_default_config()
        
        # 加载配置
        self.load_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
            'analysis': {
                'bollinger_bands': {
                    'period': 20,
                    'std_dev': 2
                },
                'rsi': {
                    'period': 14,
                    'overbought': 70,
                    'oversold': 30
                },
                'moving_averages': {
                    'short_period': 10,
                    'long_period': 30
                },
                'sideways_threshold': 0.02,
                'trend_confirmation_periods': 3
            },
            'alerts': {
                'console_output': True,
                'log_file': 'alerts.log',
                'email_notifications': False,
                'webhook_url': None
            },
            'api': {
                'base_url': 'https://api.binance.com',
                'rate_limit': 1200
            },
            'monitoring_interval': 60
        }
    
    def load_config(self) -> Dict:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                
                # 合并默认配置和加载的配置
                self.config = self._merge_configs(self.default_config, loaded_config)
                
                # 验证配置
                self._validate_config()
                
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                logger.warning(f"配置文件不存在，使用默认配置: {self.config_file}")
                self.config = self.default_config.copy()
                self.save_config()  # 保存默认配置到文件
            
            return self.config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
            self.config = self.default_config.copy()
            return self.config
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            logger.info(f"配置文件保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """
        合并默认配置和加载的配置
        
        Args:
            default: 默认配置
            loaded: 加载的配置
            
        Returns:
            合并后的配置
        """
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _validate_config(self):
        """验证配置的有效性"""
        errors = []
        
        # 验证symbols
        if not isinstance(self.config.get('symbols'), list) or not self.config['symbols']:
            errors.append("symbols必须是非空列表")
        
        # 验证timeframes
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        timeframes = self.config.get('timeframes', [])
        if not isinstance(timeframes, list) or not timeframes:
            errors.append("timeframes必须是非空列表")
        else:
            invalid_timeframes = [tf for tf in timeframes if tf not in valid_timeframes]
            if invalid_timeframes:
                errors.append(f"无效的时间周期: {invalid_timeframes}")
        
        # 验证数值参数
        numeric_params = [
            ('analysis.bollinger_bands.period', int, 1, 100),
            ('analysis.bollinger_bands.std_dev', (int, float), 0.1, 5),
            ('analysis.rsi.period', int, 1, 50),
            ('analysis.rsi.overbought', (int, float), 50, 100),
            ('analysis.rsi.oversold', (int, float), 0, 50),
            ('analysis.moving_averages.short_period', int, 1, 50),
            ('analysis.moving_averages.long_period', int, 1, 200),
            ('analysis.sideways_threshold', (int, float), 0.001, 0.1),
            ('analysis.trend_confirmation_periods', int, 1, 10),
            ('monitoring_interval', (int, float), 1, 3600)
        ]
        
        for param_path, param_type, min_val, max_val in numeric_params:
            value = self._get_nested_value(param_path)
            if value is not None:
                if not isinstance(value, param_type):
                    errors.append(f"{param_path}必须是{param_type.__name__}类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"{param_path}必须在{min_val}到{max_val}之间")
        
        # 验证均线周期关系
        ma_short = self._get_nested_value('analysis.moving_averages.short_period')
        ma_long = self._get_nested_value('analysis.moving_averages.long_period')
        if ma_short and ma_long and ma_short >= ma_long:
            errors.append("短期均线周期必须小于长期均线周期")
        
        # 验证RSI参数关系
        rsi_oversold = self._get_nested_value('analysis.rsi.oversold')
        rsi_overbought = self._get_nested_value('analysis.rsi.overbought')
        if rsi_oversold and rsi_overbought and rsi_oversold >= rsi_overbought:
            errors.append("RSI超卖阈值必须小于超买阈值")
        
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("配置验证通过")
    
    def _get_nested_value(self, path: str) -> Any:
        """
        获取嵌套字典中的值
        
        Args:
            path: 点分隔的路径，如 'analysis.rsi.period'
            
        Returns:
            值或None
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def update_config(self, updates: Dict) -> bool:
        """
        更新配置
        
        Args:
            updates: 要更新的配置项
            
        Returns:
            是否更新成功
        """
        try:
            # 备份当前配置
            backup_config = self.config.copy()
            
            # 应用更新
            self.config = self._merge_configs(self.config, updates)
            
            # 验证更新后的配置
            self._validate_config()
            
            # 保存到文件
            if self.save_config():
                logger.info("配置更新成功")
                return True
            else:
                # 恢复备份
                self.config = backup_config
                return False
                
        except Exception as e:
            # 恢复备份
            self.config = backup_config
            logger.error(f"配置更新失败: {e}")
            return False
    
    def get_config(self) -> Dict:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        return self.config.copy()
    
    def get_config_summary(self) -> str:
        """
        获取配置摘要
        
        Returns:
            配置摘要字符串
        """
        summary = f"""
配置摘要:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 监测币种: {len(self.config['symbols'])} 个
   {', '.join(self.config['symbols'])}

⏰ 监测周期: {len(self.config['timeframes'])} 个
   {', '.join(self.config['timeframes'])}

📈 技术分析参数:
   • 布林带周期: {self.config['analysis']['bollinger_bands']['period']}
   • RSI周期: {self.config['analysis']['rsi']['period']}
   • 短期均线: {self.config['analysis']['moving_averages']['short_period']}
   • 长期均线: {self.config['analysis']['moving_averages']['long_period']}
   • 震荡阈值: {self.config['analysis']['sideways_threshold']*100:.1f}%

🚨 告警设置:
   • 控制台输出: {'✓' if self.config['alerts']['console_output'] else '✗'}
   • 日志文件: {self.config['alerts']['log_file']}
   • 邮件通知: {'✓' if self.config['alerts']['email_notifications'] else '✗'}

⚙️ 监测间隔: {self.config['monitoring_interval']} 秒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return summary.strip()
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到指定文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            if export_path.suffix.lower() == '.json':
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            else:
                with open(export_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
            
            logger.info(f"配置导出成功: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"配置导出失败: {e}")
            return False
