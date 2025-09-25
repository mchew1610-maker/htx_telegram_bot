#!/usr/bin/env python3
# 简单测试脚本
import os
from dotenv import load_dotenv

print("=" * 50)
print("HTX Bot 配置测试")
print("=" * 50)

# 加载环境变量
load_dotenv()

# 检查配置
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
user_ids = os.getenv('ALLOWED_USER_IDS')
api_key = os.getenv('HTX_ACCESS_KEY')
secret_key = os.getenv('HTX_SECRET_KEY')

print(f"\nBot Token: {'✓ 已配置' if bot_token else '✗ 未配置'}")
print(f"  Token: {bot_token[:20]}..." if bot_token else "")

print(f"\n用户权限: {'✓ 已配置' if user_ids else '✗ 未配置'}")
print(f"  授权ID: {user_ids}")

print(f"\nHTX API: {'✓ 已配置' if api_key and secret_key else '✗ 未配置'}")
print(f"  API Key: {api_key[:20]}..." if api_key else "")

print("\n测试导入...")
try:
    import telebot
    print("  ✓ Telegram库正常")
except:
    print("  ✗ Telegram库缺失")

try:
    import requests
    print("  ✓ Requests库正常")
except:
    print("  ✗ Requests库缺失")

try:
    import websocket
    print("  ✓ WebSocket库正常")
except:
    print("  ✗ WebSocket库缺失")

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    print("  ✓ 调度器正常")
except:
    print("  ✗ 调度器缺失")

try:
    from loguru import logger
    print("  ✓ 日志库正常")
except:
    print("  ✗ 日志库缺失")

print("\n" + "=" * 50)
print("测试完成！如果都是✓，可以运行: python bot.py")
