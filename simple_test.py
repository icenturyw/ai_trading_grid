"""
简单测试脚本
"""

print("开始测试...")

try:
    import requests
    print("✓ requests 模块可用")
except ImportError:
    print("✗ requests 模块不可用")

try:
    import pandas as pd
    print("✓ pandas 模块可用")
except ImportError:
    print("✗ pandas 模块不可用")

try:
    import numpy as np
    print("✓ numpy 模块可用")
except ImportError:
    print("✗ numpy 模块不可用")

try:
    import yaml
    print("✓ yaml 模块可用")
except ImportError:
    print("✗ yaml 模块不可用")

try:
    from colorama import Fore, Style
    print("✓ colorama 模块可用")
except ImportError:
    print("✗ colorama 模块不可用")

# 测试基本功能
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent / 'src'))
    
    from src.config_manager import ConfigManager
    print("✓ 配置管理器导入成功")
    
    config_manager = ConfigManager('config.yaml')
    config = config_manager.get_config()
    print(f"✓ 配置加载成功，监测 {len(config['symbols'])} 个币种")
    
except Exception as e:
    print(f"✗ 配置测试失败: {e}")

print("测试完成")
