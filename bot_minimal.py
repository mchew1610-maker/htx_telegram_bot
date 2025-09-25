#!/usr/bin/env python3
"""HTX Trading Bot - 最小可运行版本"""

import os
import sys
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 导入telebot
try:
    import telebot
    from telebot import types
except ImportError:
    print("请安装: pip install pyTelegramBotAPI")
    sys.exit(1)

# 获取配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USER_IDS = os.getenv('ALLOWED_USER_IDS', '').split(',')

if not BOT_TOKEN:
    print("请设置 TELEGRAM_BOT_TOKEN")
    sys.exit(1)

# 初始化bot
bot = telebot.TeleBot(BOT_TOKEN)

# 配置类（简化版）
class Config:
    def __init__(self):
        self.htx_access_key = os.getenv('HTX_ACCESS_KEY', '')
        self.htx_secret_key = os.getenv('HTX_SECRET_KEY', '')
        self.htx_rest_url = os.getenv('HTX_REST_URL', 'https://api.huobi.pro')
        self.htx_ws_url = os.getenv('HTX_WS_URL', 'wss://api.huobi.pro/ws/v2')
        self.allowed_user_ids = ALLOWED_USER_IDS
        self.default_symbols = ['btcusdt', 'ethusdt', 'bnbusdt']

config = Config()

# 导入模块
from modules.market.market import MarketModule
from modules.account.account import AccountModule
from modules.trading.trading import TradingModule
from modules.grid.grid import GridModule
from modules.monitor.monitor import MonitorModule
from modules.charts.charts import ChartsModule

# 初始化模块
market = MarketModule(config.htx_access_key, config.htx_secret_key, config.htx_rest_url)
account = AccountModule(config.htx_access_key, config.htx_secret_key, config.htx_rest_url)
trading = TradingModule(config.htx_access_key, config.htx_secret_key, config.htx_rest_url)
grid = GridModule()
monitor = MonitorModule(bot)
charts = ChartsModule()

# 预警回调函数
def send_alert_notification(message, user_id=None):
    """发送预警通知"""
    try:
        if user_id:
            bot.send_message(user_id, f"🔔 预警\n{message}")
        else:
            for uid in ALLOWED_USER_IDS:
                if uid:
                    try:
                        bot.send_message(uid, f"🔔 预警\n{message}")
                    except:
                        pass
    except Exception as e:
        logger.error(f"发送预警失败: {e}")

# 设置预警回调
monitor.set_alert_callback(send_alert_notification)

# 用户状态
user_states = {}

# 权限装饰器
def authorized_only(func):
    def wrapper(message):
        user_id = str(message.from_user.id)
        if ALLOWED_USER_IDS and ALLOWED_USER_IDS[0]:
            if user_id not in ALLOWED_USER_IDS:
                bot.send_message(message.chat.id, "❌ 无权限")
                return
        return func(message)
    return wrapper

# 命令处理
@bot.message_handler(commands=['start'])
@authorized_only
def start_command(message):
    """启动命令"""
    bot.send_message(
        message.chat.id,
        f"🚀 欢迎使用HTX Trading Bot！\n"
        f"您的ID: {message.from_user.id}\n\n"
        f"使用 /help 查看帮助"
    )

@bot.message_handler(commands=['help'])
@authorized_only
def help_command(message):
    """帮助命令"""
    bot.send_message(
        message.chat.id,
        "📚 命令列表:\n"
        "/start - 启动\n"
        "/balance - 查看余额\n"
        "/price <symbol> - 查看价格\n"
        "/help - 帮助"
    )

@bot.message_handler(commands=['balance'])
@authorized_only
def balance_command(message):
    """查看余额"""
    balance = account.get_total_balance()
    text = f"💰 总资产: {balance['total_usdt']:.2f} USDT\n"

    for acc_type, value in balance.get('accounts', {}).items():
        if value > 0:
            text += f"• {acc_type}: {value:.2f} USDT\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['price'])
@authorized_only
def price_command(message):
    """查看价格"""
    parts = message.text.split()
    symbol = parts[1] if len(parts) > 1 else 'btcusdt'

    ticker = market.get_ticker(symbol)
    text = f"📈 {symbol.upper()}\n"
    text += f"价格: ${ticker['close']:.2f}\n"
    text += f"涨跌: {ticker['change']:.2f}%"

    bot.send_message(message.chat.id, text)

# 主函数
def main():
    logger.info("Bot启动...")
    logger.info(f"授权用户: {ALLOWED_USER_IDS}")

    try:
        bot_info = bot.get_me()
        logger.info(f"Bot: @{bot_info.username}")
    except Exception as e:
        logger.error(f"获取bot信息失败: {e}")
        return

    logger.info("开始接收消息...")
    bot.polling(none_stop=True, timeout=60)

if __name__ == '__main__':
    main()
