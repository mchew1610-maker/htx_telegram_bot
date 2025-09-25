# 🤖 HTX Telegram 自动交易机器人 - 项目总览

## 📁 项目结构
```
htx_telegram_bot/
├── bot.py                  # 主程序入口
├── test_bot.py            # 测试脚本
├── start.sh               # 启动脚本
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量模板
├── Dockerfile            # Docker配置
├── docker-compose.yml    # Docker Compose配置
├── Makefile              # 快捷命令
│
├── config/               # 配置模块
│   └── config.py        # 配置管理
│
├── modules/              # 功能模块
│   ├── __init__.py
│   ├── market/          # 市场数据
│   │   └── market.py
│   ├── account/         # 账户管理
│   │   └── account.py
│   ├── trading/         # 交易功能
│   │   └── trading.py
│   ├── grid/            # 网格交易
│   │   └── grid_trading.py
│   ├── monitor/         # 监控预警
│   │   └── monitor.py
│   └── charts/          # 图表生成
│       └── charts.py
│
├── utils/                # 工具函数
│   ├── logger.py        # 日志管理
│   ├── htx_api_base.py  # API基础类
│   └── websocket_client.py  # WebSocket客户端
│
├── data/                 # 数据存储（自动创建）
│   ├── charts/          # 图表文件
│   ├── grids/           # 网格配置
│   ├── alerts/          # 预警规则
│   └── users/           # 用户设置
│
└── logs/                 # 日志文件（自动创建）
    ├── bot.log          # 主日志
    ├── trading.log      # 交易日志
    └── error.log        # 错误日志
```

## 🚀 快速开始

### 1️⃣ 基础安装
```bash
# 克隆项目后
cd htx_telegram_bot

# 使用Makefile快速设置
make setup    # 初始化项目
make install  # 安装依赖
```

### 2️⃣ 配置API密钥
```bash
# 编辑.env文件
vim .env

# 必须配置的项目：
TELEGRAM_BOT_TOKEN=你的机器人Token
HTX_ACCESS_KEY=你的火币API Key
HTX_SECRET_KEY=你的火币Secret Key
```

### 3️⃣ 测试运行
```bash
# 测试各模块是否正常
make test
# 或
python test_bot.py
```

### 4️⃣ 启动机器人
```bash
# 前台运行
make run

# 后台运行
make run-bg

# 使用Docker
make docker-up
```

## 🎯 核心功能模块

### 1. 市场数据模块 (market)
- 获取实时行情
- K线数据查询
- 深度信息
- 24小时统计
- 4小时K线范围

### 2. 账户管理模块 (account)
- 余额查询
- 资产分布分析
- 每日盈亏统计
- 交易历史
- 充值地址

### 3. 交易模块 (trading)
- 限价/市价订单
- 订单查询
- 批量撤单
- 精度处理
- 订单验证

### 4. 网格交易模块 (grid)
- 基于4小时K线
- 自动计算网格
- 动态补单
- 收益统计
- 状态保存

### 5. 监控预警模块 (monitor)
- 价格预警
- 成交量监控
- 订单成交通知
- 异常检测
- 自定义规则

### 6. 图表生成模块 (charts)
- K线图（含MA指标）
- 资产饼图
- 网格可视化
- 盈亏曲线
- 市场概览

## 💡 使用技巧

### Telegram命令
- `/start` - 启动机器人
- `💹 行情` - 查看市场数据
- `💰 账户` - 管理资产
- `💱 交易` - 执行交易
- `🎯 网格` - 网格策略
- `🔔 预警` - 设置预警
- `📊 图表` - 生成图表
- `📈 盈亏` - 查看收益

### 快捷操作 (Makefile)
```bash
make help        # 查看所有命令
make logs        # 查看日志
make status      # 检查状态
make stop        # 停止运行
make clean       # 清理文件
make backup      # 备份数据
```

## 🔧 常用配置

### 网格交易配置
- 默认10个网格
- 每格0.001 BTC
- 基于4小时K线
- 0.5%利润间隔

### 监控配置
- 60秒检查间隔
- 5%价格预警阈值
- 自动订单通知
- 4小时K线提醒

## 📊 数据管理

### 数据持久化
- 网格配置自动保存
- 预警规则持久化
- 用户设置保存
- 昨日余额记录

### 日志管理
- 分级日志记录
- 自动轮转归档
- 交易日志分离
- 错误单独记录

## 🛡️ 安全措施

### API安全
- ✅ 不开启提现权限
- ✅ 使用环境变量
- ✅ 签名验证
- ✅ 错误处理

### 交易安全
- ✅ 精度自动处理
- ✅ 最小订单检查
- ✅ 余额验证
- ✅ 状态检查

## 🎉 项目特色

1. **模块化设计** - 各功能独立，易于维护
2. **完整的错误处理** - 稳定可靠
3. **丰富的图表** - 数据可视化
4. **智能网格** - 基于K线自动调整
5. **实时推送** - WebSocket支持
6. **Docker支持** - 一键部署
7. **完善的日志** - 便于调试
8. **Telegram界面** - 操作便捷

## 📝 注意事项

1. 首次运行前必须配置API密钥
2. 建议先在测试环境验证
3. 合理设置交易参数
4. 定期备份数据文件
5. 注意API调用限制
6. 保护好API密钥安全

## 🆘 问题解决

如遇到问题，请按以下步骤排查：

1. 运行测试脚本 `make test`
2. 查看日志文件 `make logs`
3. 检查API配置 `.env`
4. 验证网络连接
5. 查看错误日志 `logs/error.log`

---

**开始使用**: 配置好`.env`后，运行`make test`测试，然后`make run`启动机器人！

祝您交易愉快！ 🚀
