# HTX (火币) Telegram 交易机器人

## 项目概述
一个功能完善的自动化交易系统，集成火币(HTX)交易所API，通过Telegram提供便捷的交易操作界面。

## 核心功能
- 💹 实时行情监控
- 💰 账户管理
- 🎯 网格交易（基于4小时K线）
- 💱 现货交易
- 🔔 价格预警
- 📊 数据可视化

## 项目结构
```
htx_telegram_bot/
├── config/          # 配置文件
├── modules/         # 功能模块
│   ├── market/     # 市场数据模块
│   ├── account/    # 账户管理模块
│   ├── trading/    # 交易模块
│   ├── grid/       # 网格交易模块
│   ├── monitor/    # 监控预警模块
│   └── charts/     # 图表生成模块
├── utils/          # 工具函数
├── data/          # 数据存储
├── logs/          # 日志文件
├── bot.py         # 主程序
└── requirements.txt
```

## 安装部署
1. 安装依赖：`pip install -r requirements.txt`
2. 配置API密钥和Token
3. 运行机器人：`python bot.py`

## 使用说明
1. 在Telegram中搜索机器人
2. 发送 /start 开始使用
3. 使用按钮菜单选择功能
