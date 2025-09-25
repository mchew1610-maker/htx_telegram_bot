#!/usr/bin/env python3
"""HTX Trading Bot - 稳定版"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 导入必要的库
try:
    import telebot
    from telebot import types
except ImportError:
    print("请安装: pip install pyTelegramBotAPI")
    sys.exit(1)

# 配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USER_IDS = os.getenv('ALLOWED_USER_IDS', '').split(',')
HTX_ACCESS_KEY = os.getenv('HTX_ACCESS_KEY', '')
HTX_SECRET_KEY = os.getenv('HTX_SECRET_KEY', '')

if not BOT_TOKEN:
    print("错误: 请设置 TELEGRAM_BOT_TOKEN")
    sys.exit(1)

print(f"Bot Token: {BOT_TOKEN[:20]}...")
print(f"授权用户: {ALLOWED_USER_IDS}")

# 初始化bot
bot = telebot.TeleBot(BOT_TOKEN)

# 导入模块（安全导入）
try:
    from modules.market.market import MarketModule
    from modules.account.account import AccountModule
    from modules.trading.trading import TradingModule
    from modules.grid.grid import GridModule
    from modules.monitor.monitor import MonitorModule
    from modules.charts.charts import ChartsModule

    # 初始化模块
    market = MarketModule(HTX_ACCESS_KEY, HTX_SECRET_KEY)
    account = AccountModule(HTX_ACCESS_KEY, HTX_SECRET_KEY)
    trading = TradingModule(HTX_ACCESS_KEY, HTX_SECRET_KEY)
    grid = GridModule()
    monitor = MonitorModule(bot)
    charts = ChartsModule()

    # 设置预警回调
    def send_alert(msg, uid=None):
        try:
            if uid:
                bot.send_message(uid, f"🔔 {msg}")
            else:
                for user_id in ALLOWED_USER_IDS:
                    if user_id:
                        bot.send_message(user_id, f"🔔 {msg}")
        except Exception as e:
            logger.error(f"发送预警失败: {e}")

    monitor.set_alert_callback(send_alert)

except Exception as e:
    print(f"模块导入失败: {e}")
    print("将以基础模式运行")
    market = None
    account = None

# 用户状态
user_states = {}

# 权限检查
def authorized_only(func):
    def wrapper(message):
        user_id = str(message.from_user.id)
        username = message.from_user.username or "Unknown"

        if ALLOWED_USER_IDS and ALLOWED_USER_IDS[0]:
            if user_id not in ALLOWED_USER_IDS:
                logger.warning(f"未授权访问: {username} ({user_id})")
                bot.send_message(message.chat.id, "❌ 您没有权限使用此机器人")
                return

        logger.info(f"授权访问: {username} ({user_id})")
        return func(message)
    return wrapper

# 创建键盘
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        types.KeyboardButton("💰 账户"),
        types.KeyboardButton("💹 行情"),
        types.KeyboardButton("💱 交易"),
        types.KeyboardButton("🎯 网格"),
        types.KeyboardButton("🔔 预警"),
        types.KeyboardButton("📊 图表"),
        types.KeyboardButton("❓ 帮助")
    ]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    return keyboard

# 命令处理
@bot.message_handler(commands=['start'])
@authorized_only
def start_command(message):
    """启动命令"""
    user = message.from_user
    text = f"""
🚀 **欢迎使用HTX Trading Bot!**

您好 {user.first_name}!
您的ID: `{user.id}`
状态: ✅ 已授权

使用下方按钮开始操作
    """
    bot.send_message(
        message.chat.id, 
        text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == '💰 账户')
@authorized_only
def handle_account(message):
    """查看账户"""
    if account:
        try:
            balance = account.get_total_balance()

            text = f"💰 **账户资产**\n"
            text += f"━━━━━━━━━━━━━━\n"
            text += f"💎 总价值: **{balance['total_usdt']:.2f} USDT**\n\n"

            # 显示各账户
            accounts = balance.get('accounts', {})
            if accounts.get('spot', 0) > 0:
                text += f"• 现货: {accounts['spot']:.2f} USDT\n"
            if accounts.get('earn', 0) > 0:
                text += f"• 赚币: {accounts['earn']:.2f} USDT\n"

            # 显示明细
            details = balance.get('details', [])
            for detail in details:
                if detail['value'] > 0.01:
                    text += f"\n**{detail['type']}**: {detail['value']:.2f} USDT"

                    # 显示资产
                    if detail.get('assets'):
                        for asset in detail['assets'][:3]:
                            if asset.get('value_usdt', 0) > 0.01:
                                text += f"\n  • {asset['currency']}: {asset['balance']:.6f}"

            bot.send_message(message.chat.id, text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"获取账户失败: {e}")
            bot.send_message(message.chat.id, "❌ 获取账户信息失败")
    else:
        bot.send_message(message.chat.id, "⚠️ 账户模块未加载")

@bot.message_handler(func=lambda m: m.text == '💹 行情')
@authorized_only
def handle_market(message):
    """查看行情"""
    if market:
        try:
            # 获取主要币种行情
            symbols = ['btcusdt', 'ethusdt', 'bnbusdt']
            text = "💹 **实时行情**\n━━━━━━━━━━━━━━\n"

            for symbol in symbols:
                ticker = market.get_ticker(symbol)
                emoji = "📈" if ticker['change'] > 0 else "📉"
                text += f"\n{emoji} **{symbol.upper()}**\n"
                text += f"  价格: ${ticker['close']:.2f}\n"
                text += f"  涨跌: {ticker['change']:+.2f}%\n"

            bot.send_message(message.chat.id, text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            bot.send_message(message.chat.id, "❌ 获取行情失败")
    else:
        bot.send_message(message.chat.id, "⚠️ 市场模块未加载")

@bot.message_handler(func=lambda m: m.text == '❓ 帮助')
@authorized_only
def handle_help(message):
    """帮助"""
    text = """
❓ **使用帮助**

**基础命令:**
/start - 启动机器人
/help - 显示帮助

**功能按钮:**
💰 账户 - 查看总资产(含赚币)
💹 行情 - 查看实时价格
💱 交易 - 买入/卖出
🎯 网格 - 自动交易策略
🔔 预警 - 价格提醒
📊 图表 - 数据图表

**您的信息:**
"""
    text += f"用户ID: `{message.from_user.id}`\n"
    text += f"权限: ✅ 已授权"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# 处理其他消息
@bot.message_handler(func=lambda m: True)
@authorized_only
def handle_other(message):
    """处理其他消息"""
    bot.send_message(
        message.chat.id,
        "请使用菜单按钮选择功能",
        reply_markup=get_main_keyboard()
    )

# 主函数
def main():
    print("=" * 60)
    print("HTX Trading Bot 启动")
    print("=" * 60)

    try:
        # 获取bot信息
        bot_info = bot.get_me()
        print(f"Bot用户名: @{bot_info.username}")
        print(f"Bot ID: {bot_info.id}")

    except Exception as e:
        print(f"错误: 无法连接到Telegram - {e}")
        print("请检查:")
        print("1. Bot Token是否正确")
        print("2. 网络连接是否正常")
        return

    print("\n开始接收消息...")
    print("按 Ctrl+C 停止\n")

    # 开始轮询
    try:
        bot.polling(none_stop=True, timeout=60)
    except KeyboardInterrupt:
        print("\n机器人已停止")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    main()
