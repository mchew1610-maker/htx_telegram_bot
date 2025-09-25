# HTX (火币) Telegram 自动交易机器人

## 📋 功能清单

### ✅ 已实现功能
- ✅ 实时行情监控（REST API + WebSocket）
- ✅ 账户余额和资产分布查询
- ✅ 现货交易（限价/市价）
- ✅ 基于4小时K线的网格交易策略
- ✅ 价格和成交量预警
- ✅ K线图和资产分布图生成
- ✅ 当日盈亏统计
- ✅ 订单管理和查询
- ✅ Telegram按钮交互界面
- ✅ 多用户配置管理

### ⚠️ 限制说明
- API速率限制：遵循HTX官方限制
- WebSocket订阅上限：100个主题
- 批量操作需分批执行
- 高频交易受限制
- 依赖交易所API可用性

## 🚀 快速部署

### 1. 环境要求
- Python 3.9+
- Linux/MacOS/Windows
- 2GB+ RAM
- 稳定网络连接

### 2. 获取API密钥

#### Telegram Bot Token
1. 在Telegram搜索 @BotFather
2. 发送 `/newbot` 创建机器人
3. 设置机器人名称和用户名
4. 获取Bot Token

#### HTX API密钥
1. 登录HTX交易所
2. 进入API管理页面
3. 创建新的API密钥
4. 设置权限：读取、交易（不要开启提现）
5. 保存Access Key和Secret Key

### 3. 安装部署

#### 方法一：直接运行
```bash
# 克隆项目
git clone <repository_url>
cd htx_telegram_bot

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入API密钥

# 运行测试
python test_bot.py

# 启动机器人
python bot.py
# 或使用启动脚本
chmod +x start.sh
./start.sh
```

#### 方法二：Docker部署
```bash
# 配置环境变量
cp .env.example .env
vim .env  # 填入API密钥

# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f htx-bot

# 停止服务
docker-compose down
```

## 📱 使用指南

### 基础操作
1. 在Telegram中搜索你的机器人
2. 发送 `/start` 启动
3. 使用底部按钮菜单操作

### 功能说明

#### 💹 行情查询
- 查看主流币种实时价格
- 24小时涨跌幅排行
- 自定义交易对查询
- 深度和成交记录

#### 💰 账户管理
- 查看总资产价值
- 资产分布饼图
- 各币种余额明细
- 充值地址查询

#### 💱 现货交易
- 限价买入/卖出
- 市价买入/卖出
- 查看未成交订单
- 一键撤销所有订单
- 交易历史查询

#### 🎯 网格交易
- 基于4小时K线自动设置网格
- 手动设置价格区间
- 自动补单策略
- 实时收益统计
- 一键停止网格

#### 🔔 监控预警
- 价格穿越/突破预警
- 成交量异常预警
- 订单成交通知
- 4小时K线更新通知

#### 📊 数据图表
- K线图（支持MA指标）
- 资产分布饼图
- 网格可视化
- 盈亏曲线图
- 市场概览图

## ⚙️ 高级配置

### 网格交易参数
```python
# .env文件
GRID_DEFAULT_COUNT=10        # 默认网格数量
GRID_DEFAULT_AMOUNT=0.001    # 每格交易量
```

### 监控参数
```python
MONITOR_INTERVAL=60           # 监控间隔(秒)
PRICE_ALERT_THRESHOLD=0.05    # 价格预警阈值5%
```

### 时区设置
```python
TIMEZONE=Asia/Shanghai        # 时区设置
```

## 🛠️ 故障排除

### 常见问题

#### 1. API认证失败
- 检查API密钥是否正确
- 确认API权限设置
- 检查服务器时间同步

#### 2. 无法连接WebSocket
- 检查网络连接
- 确认防火墙设置
- 尝试更换API地址

#### 3. 订单创建失败
- 检查余额是否充足
- 确认交易对状态
- 验证订单参数精度

#### 4. 图表生成失败
- 安装kaleido: `pip install kaleido`
- 检查data/charts目录权限
- 确认依赖包版本

### 日志查看
```bash
# 查看主日志
tail -f logs/bot.log

# 查看交易日志
tail -f logs/trading.log

# 查看错误日志
tail -f logs/error.log
```

## 📊 性能优化

### 建议配置
- 监控交易对不超过10个
- 网格数量10-20个
- 监控间隔60秒以上
- 使用Redis缓存数据

### 资源占用
- CPU: < 5%
- 内存: 200-500MB
- 网络: 10-50KB/s
- 存储: 100MB+

## 🔒 安全建议

### API密钥安全
- ❌ 不要开启提现权限
- ❌ 不要分享API密钥
- ✅ 定期更换密钥
- ✅ 设置IP白名单

### 交易安全
- 设置合理的单笔限额
- 启用价格偏差保护
- 定期检查订单状态
- 保留交易日志

## 📝 更新日志

### v1.0.0 (2024-01)
- 初始版本发布
- 完整功能实现
- Telegram界面优化

## 🤝 技术支持

### 问题反馈
- 提交Issue到GitHub
- 查看logs目录下的日志
- 提供详细错误信息

### 功能建议
- 欢迎提交Pull Request
- 讨论新功能需求
- 分享使用经验

## ⚠️ 免责声明

本机器人仅供学习交流使用，不构成投资建议。加密货币交易存在风险，请谨慎操作。使用本软件造成的任何损失，开发者不承担责任。

## 📄 许可证

MIT License

---

**提示**: 首次使用请先运行 `python test_bot.py` 测试各模块是否正常工作。
