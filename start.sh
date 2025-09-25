#!/bin/bash

# HTX Telegram Bot 启动脚本

echo "========================================="
echo "   HTX Telegram Trading Bot Launcher    "
echo "========================================="

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ 错误: Python版本必须 >= 3.9 (当前: $python_version)"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装/更新依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt -q

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件，从模板创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件配置API密钥"
    echo "   vim .env"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p data/charts data/grids data/alerts data/users logs

# 检查API密钥配置
if grep -q "your_telegram_bot_token_here" .env; then
    echo "❌ 错误: 请先配置Telegram Bot Token"
    echo "   编辑 .env 文件并设置 TELEGRAM_BOT_TOKEN"
    exit 1
fi

if grep -q "your_htx_access_key_here" .env; then
    echo "❌ 错误: 请先配置HTX API密钥"
    echo "   编辑 .env 文件并设置 HTX_ACCESS_KEY 和 HTX_SECRET_KEY"
    exit 1
fi

# 运行机器人
echo "========================================="
echo "🚀 启动HTX交易机器人..."
echo "========================================="
echo ""
echo "📊 日志文件: logs/bot.log"
echo "🛑 停止运行: Ctrl+C"
echo ""

# 使用nohup在后台运行（可选）
# nohup python bot.py > logs/console.log 2>&1 &
# echo "✅ 机器人已在后台运行 (PID: $!)"
# echo "   查看日志: tail -f logs/bot.log"

# 直接运行（推荐开发时使用）
python bot.py
