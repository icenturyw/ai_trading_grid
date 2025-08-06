# 币种走势监测系统 🚀

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/icenturyw/ai_trading_grid.svg)](https://github.com/icenturyw/ai_trading_grid/stargazers)

一个基于多数据源的加密货币走势监测应用，能够监测多个时间周期，识别震荡和单边走势的变化并发出告警。专门针对网络访问限制进行了优化，支持代理和备用数据源。

![Demo](https://via.placeholder.com/800x400/1e1e1e/ffffff?text=Crypto+Trend+Monitor+Demo)

## 📋 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [网络配置](#网络配置)
- [使用方法](#使用方法)
- [配置说明](#配置说明)
- [技术原理](#技术原理)
- [项目结构](#项目结构)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 功能特性

- 🔍 **多币种监测**: 支持同时监测多个加密货币交易对
- ⏰ **多周期分析**: 支持1分钟到1天的多个时间周期
- 📊 **技术指标**: 集成布林带、RSI、移动平均线等技术指标
- 🚨 **智能告警**: 自动识别走势变化并发出告警
- 📝 **日志记录**: 完整的监测和告警日志
- ⚙️ **灵活配置**: 通过配置文件自定义监测参数
- 🌐 **多数据源**: 支持币安API + 备用数据源，确保数据获取稳定性
- 🔧 **代理支持**: 支持HTTP/HTTPS代理，解决网络访问问题
- 🔄 **自动切换**: API失败时自动切换到备用数据源

## 安装和使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置参数

编辑 `config.yaml` 文件，设置要监测的币种、时间周期和告警参数。

**网络访问配置：**

如果你在中国大陆或其他地区无法直接访问币安API，可以：

1. **使用代理**：复制 `config_with_proxy.yaml` 为 `config.yaml`，配置你的代理设置
2. **使用备用数据源**：系统会自动切换到CoinGecko等免费API
3. **多端点重试**：系统会自动尝试多个币安API端点

### 3. 测试连接

```bash
python main.py --test
```

### 4. 运行程序

```bash
python main.py
```

## 配置说明

- `symbols`: 要监测的交易对列表
- `timeframes`: 监测的时间周期
- `analysis`: 技术分析参数
- `alerts`: 告警设置
- `monitoring_interval`: 监测间隔

## 走势识别算法

系统使用多种技术指标来识别走势：

1. **布林带**: 判断价格是否在正常波动范围内
2. **RSI**: 识别超买超卖状态
3. **移动平均线**: 判断趋势方向
4. **价格波动率**: 区分震荡和单边走势

## 告警机制

当检测到以下情况时会发出告警：
- 从震荡走势转为单边上涨
- 从震荡走势转为单边下跌
- 从单边走势转为震荡

## 项目结构

```
ai_trading_grid/
├── main.py              # 主程序入口
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖包列表
├── src/
│   ├── __init__.py
│   ├── binance_api.py   # 币安API接口
│   ├── trend_analyzer.py # 走势分析器
│   ├── monitor.py       # 监测系统
│   └── alerts.py        # 告警系统
└── logs/                # 日志目录

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/icenturyw/ai_trading_grid.git
cd ai_trading_grid

# 安装依赖
pip install -r requirements.txt

# 运行测试
python run_tests.py

# 运行演示
python demo.py
```

## 🐛 问题反馈

如果您遇到任何问题，请：

1. 查看 [使用指南.md](使用指南.md)
2. 检查 [Issues](https://github.com/icenturyw/ai_trading_grid/issues) 中是否有类似问题
3. 创建新的 Issue，请包含：
   - 操作系统信息
   - Python版本
   - 错误日志
   - 复现步骤

## 📈 路线图

- [ ] Web界面支持
- [ ] 更多技术指标
- [ ] 邮件/短信通知
- [ ] 数据库存储
- [ ] 回测功能
- [ ] 策略自定义

## ⭐ Star History

如果这个项目对您有帮助，请给个Star支持一下！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Binance API](https://binance-docs.github.io/apidocs/) - 主要数据源
- [CoinGecko API](https://www.coingecko.com/en/api) - 备用数据源
- [pandas](https://pandas.pydata.org/) - 数据处理
- [colorama](https://pypi.org/project/colorama/) - 彩色输出

## ⚠️ 免责声明

本系统仅用于技术分析和学习目的，不构成投资建议。加密货币投资存在风险，请谨慎决策。

---

<div align="center">
Made with ❤️ by <a href="https://github.com/icenturyw">centuryw</a>
</div>
```
