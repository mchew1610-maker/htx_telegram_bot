#!/usr/bin/env python3
"""
HTX (火币) Telegram 交易机器人
主程序入口
"""

import os
import sys
import asyncio
from datetime import datetime, time
import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from functools import wraps

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置和日志
from config.config import config
from utils.logger import logger, trading_logger

# 导入功能模块
from modules.market.market import MarketModule
from modules.account.account import AccountModule
from modules.trading.trading import TradingModule
from modules.grid.grid_trading import GridTradingModule
from modules.monitor.monitor import MonitorModule
from modules.charts.charts import ChartsModule

# 初始化机器人
bot = telebot.TeleBot(config.telegram.bot_token)

# 初始化模块
market = MarketModule(config.htx.access_key, config.htx.secret_key, config.htx.rest_url)
account = AccountModule(config.htx.access_key, config.htx.secret_key, config.htx.rest_url)
trading = TradingModule(config.htx.access_key, config.htx.secret_key, config.htx.rest_url)
monitor = MonitorModule(market, trading)
grid = GridTradingModule(market, trading, monitor)
charts = ChartsModule()


# 设置监控回调
def send_alert_notification(notification):
    """发送预警通知"""
    try:
        chat_id = notification.get('user_id', config.telegram.chat_id)
        if chat_id:
            bot.send_message(chat_id, notification['full_message'])
    except Exception as e:
        logger.error(f"发送通知失败: {e}")


monitor.set_alert_callback(send_alert_notification)

# 定时任务调度器
scheduler = BackgroundScheduler()

# 用户状态管理
user_states = {}
user_data = {}


# 加载授权用户列表
def load_authorized_users():
    """加载授权用户列表"""
    allowed_users = []

    # 从环境变量加载
    env_users = os.getenv('ALLOWED_USER_IDS', '').strip()
    if env_users:
        allowed_users.extend(env_users.split(','))

    # 从文件加载（如果存在）
    try:
        if os.path.exists('data/authorized_users.json'):
            import json
            with open('data/authorized_users.json', 'r') as f:
                data = json.load(f)
                if 'allowed_users' in data:
                    allowed_users.extend(data['allowed_users'])
    except Exception as e:
        logger.error(f"加载授权用户失败: {e}")

    # 去重并过滤空值
    allowed_users = list(set(filter(None, allowed_users)))

    if allowed_users:
        logger.info(f"已加载 {len(allowed_users)} 个授权用户")
    else:
        logger.warning("未设置授权用户，所有用户都可以使用")

    return allowed_users


# 授权用户列表
AUTHORIZED_USERS = load_authorized_users()


def authorized_only(func):
    """装饰器：仅授权用户可使用"""

    @wraps(func)
    def wrapper(message):
        user_id = str(message.from_user.id)
        username = message.from_user.username or "Unknown"

        # 如果没有设置授权用户，允许所有人使用
        if not AUTHORIZED_USERS:
            return func(message)

        # 检查用户权限
        if user_id in AUTHORIZED_USERS:
            logger.info(f"授权用户访问: {username} ({user_id})")
            return func(message)
        else:
            logger.warning(f"未授权访问尝试: {username} ({user_id})")
            bot.send_message(
                message.chat.id,
                "⚠️ *访问被拒绝*\n\n"
                "您没有使用此机器人的权限。\n"
                "请联系管理员获取访问权限。\n\n"
                f"您的用户ID: `{user_id}`",
                parse_mode='Markdown'
            )
            return None

    return wrapper


def authorized_callback(func):
    """装饰器：仅授权用户可使用回调"""

    @wraps(func)
    def wrapper(call):
        user_id = str(call.from_user.id)
        username = call.from_user.username or "Unknown"

        # 如果没有设置授权用户，允许所有人使用
        if not AUTHORIZED_USERS:
            return func(call)

        # 检查用户权限
        if user_id in AUTHORIZED_USERS:
            return func(call)
        else:
            logger.warning(f"未授权回调尝试: {username} ({user_id})")
            bot.answer_callback_query(call.id, "⚠️ 您没有使用权限", show_alert=True)
            return None

    return wrapper


def get_main_keyboard():
    """获取主菜单键盘"""
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)

    buttons = [
        ['💹 行情', '💰 账户', '📊 图表'],
        ['💱 交易', '🎯 网格', '🔔 预警'],
        ['📈 盈亏', '⚙️ 设置', '❓ 帮助']
    ]

    for row in buttons:
        markup.row(*[types.KeyboardButton(btn) for btn in row])

    return markup


def get_market_keyboard():
    """获取行情菜单键盘"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        [
            types.InlineKeyboardButton('BTC/USDT', callback_data='ticker_btcusdt'),
            types.InlineKeyboardButton('ETH/USDT', callback_data='ticker_ethusdt')
        ],
        [
            types.InlineKeyboardButton('BNB/USDT', callback_data='ticker_bnbusdt'),
            types.InlineKeyboardButton('自定义', callback_data='ticker_custom')
        ],
        [
            types.InlineKeyboardButton('24h涨幅榜', callback_data='market_top'),
            types.InlineKeyboardButton('24h跌幅榜', callback_data='market_bottom')
        ],
        [
            types.InlineKeyboardButton('返回主菜单', callback_data='back_main')
        ]
    ]

    for row in buttons:
        markup.row(*row)

    return markup


def get_trading_keyboard():
    """获取交易菜单键盘"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        [
            types.InlineKeyboardButton('限价买入', callback_data='trade_buy_limit'),
            types.InlineKeyboardButton('限价卖出', callback_data='trade_sell_limit')
        ],
        [
            types.InlineKeyboardButton('市价买入', callback_data='trade_buy_market'),
            types.InlineKeyboardButton('市价卖出', callback_data='trade_sell_market')
        ],
        [
            types.InlineKeyboardButton('当前订单', callback_data='trade_open_orders'),
            types.InlineKeyboardButton('撤销所有', callback_data='trade_cancel_all')
        ],
        [
            types.InlineKeyboardButton('交易历史', callback_data='trade_history'),
            types.InlineKeyboardButton('返回主菜单', callback_data='back_main')
        ]
    ]

    for row in buttons:
        markup.row(*row)

    return markup


@bot.message_handler(commands=['start'])
@authorized_only
def start_command(message):
    """处理/start命令"""
    user_id = str(message.from_user.id)

    welcome_text = (
        "🤖 *欢迎使用HTX交易机器人*\n\n"
        "我可以帮您:\n"
        "• 查看实时行情\n"
        "• 管理账户资产\n"
        "• 执行现货交易\n"
        "• 运行网格策略\n"
        "• 设置价格预警\n"
        "• 生成数据图表\n\n"
        "请选择功能开始使用 👇"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

    # 保存用户chat_id
    if not config.telegram.chat_id:
        config.telegram.chat_id = str(message.chat.id)

    logger.info(f"用户 {user_id} 启动机器人")


@bot.message_handler(func=lambda message: message.text == '💹 行情')
@authorized_only
def handle_market(message):
    """处理行情查询"""
    bot.send_message(
        message.chat.id,
        "📊 *选择查询的行情:*",
        parse_mode='Markdown',
        reply_markup=get_market_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == '💰 账户')
@authorized_only
def handle_account(message):
    """处理账户查询 - 显示所有账户总余额（包括赚币）"""
    try:
        bot.send_message(message.chat.id, "⏳ 正在查询所有账户余额...")

        # 初始化总余额
        total_balance_all = {
            'total_usdt': 0,
            'accounts': {},
            'details': []
        }

        # 1. 获取现货账户余额
        try:
            spot_balance = account.get_balance()
            if spot_balance and 'error' not in spot_balance:
                total_balance_all['accounts']['spot'] = spot_balance.get('total_usdt', 0)
                total_balance_all['total_usdt'] += spot_balance.get('total_usdt', 0)
                total_balance_all['details'].append({
                    'type': '现货账户',
                    'value': spot_balance.get('total_usdt', 0),
                    'assets': spot_balance.get('balance_list', [])
                })
        except Exception as e:
            logger.debug(f"获取现货余额失败: {e}")

        # 2. 尝试获取账户总览（包含赚币等其他账户）
        try:
            # 使用账户估值API获取总资产
            import requests
            import hmac
            import hashlib
            import base64
            from urllib.parse import urlencode
            from datetime import datetime

            # 生成签名
            def generate_signature(method, path, params={}):
                timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                params_to_sign = {
                    'AccessKeyId': config.htx_access_key,
                    'SignatureMethod': 'HmacSHA256',
                    'SignatureVersion': '2',
                    'Timestamp': timestamp
                }
                params_to_sign.update(params)

                sorted_params = sorted(params_to_sign.items())
                encode_params = urlencode(sorted_params)

                host = 'api.huobi.pro'
                payload = f"{method}\n{host}\n{path}\n{encode_params}"

                signature = base64.b64encode(
                    hmac.new(
                        config.htx_secret_key.encode('utf-8'),
                        payload.encode('utf-8'),
                        hashlib.sha256
                    ).digest()
                ).decode('utf-8')

                params_to_sign['Signature'] = signature
                return params_to_sign

            # 获取账户总估值
            signed_params = generate_signature('GET', '/v1/account/asset-valuation', 
                                              {'accountType': '1', 'valuationCurrency': 'USDT'})

            response = requests.get(
                'https://api.huobi.pro/v1/account/asset-valuation',
                params=signed_params,
                timeout=10
            )

            result = response.json()

            if result.get('status') == 'ok' and result.get('data'):
                # 总资产估值
                total_valuation = float(result['data'].get('balance', 0))

                # 计算其他账户（赚币等）的余额
                spot_value = total_balance_all['accounts'].get('spot', 0)
                other_value = max(0, total_valuation - spot_value)

                if other_value > 0:
                    total_balance_all['accounts']['other'] = other_value
                    total_balance_all['total_usdt'] = total_valuation
                    total_balance_all['details'].append({
                        'type': '其他账户(含赚币)',
                        'value': other_value,
                        'assets': []
                    })

        except Exception as e:
            logger.debug(f"获取总估值失败: {e}")

        # 3. 如果没有获取到估值，尝试其他API
        if total_balance_all['total_usdt'] <= 0 and 'spot' in total_balance_all['accounts']:
            # 至少显示现货余额
            total_balance_all['total_usdt'] = total_balance_all['accounts'].get('spot', 0)

        # 4. 构建显示文本
        text = "💰 *账户资产*\n"
        text += "━━━━━━━━━━━━━━\n"

        # 显示总价值
        text += f"💎 总价值: *{total_balance_all['total_usdt']:.2f} USDT*\n\n"

        # 显示账户分布
        if total_balance_all.get('details'):
            has_other = False
            for detail in total_balance_all['details']:
                if detail['value'] > 0.01:
                    emoji = "🟢" if detail['value'] > 10 else "🔵"
                    percentage = (detail['value'] / total_balance_all['total_usdt'] * 100) if total_balance_all['total_usdt'] > 0 else 0
                    text += f"{emoji} {detail['type']}: {detail['value']:.2f} USDT ({percentage:.1f}%)\n"

                    if '其他' in detail['type'] or '赚币' in detail['type']:
                        has_other = True

            # 如果有其他账户余额，添加提示
            if has_other:
                text += "\n💡 _包含赚币/理财等其他账户余额_\n"

        # 显示现货资产明细（如果有）
        spot_detail = next((d for d in total_balance_all.get('details', []) if d['type'] == '现货账户'), None)
        if spot_detail and spot_detail.get('assets'):
            text += "\n*现货资产明细:*\n"
            # 按价值排序
            assets_sorted = sorted(spot_detail['assets'], key=lambda x: x.get('value_usdt', 0), reverse=True)

            for asset in assets_sorted[:8]:  # 显示前8个
                if asset.get('value_usdt', 0) > 0.01:
                    emoji = "🟢" if asset['value_usdt'] > 10 else "🔵"
                    percentage = (asset['value_usdt'] / total_balance_all['total_usdt'] * 100) if total_balance_all['total_usdt'] > 0 else 0

                    text += f"{emoji} {asset['currency']}: {asset['balance']:.6f} "
                    text += f"(${asset['value_usdt']:.2f} | {percentage:.1f}%)\n"

        # 添加刷新和功能按钮
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🔄 刷新", callback_data="refresh_balance"),
            types.InlineKeyboardButton("📊 资产分布", callback_data="chart_asset")
        )

        # 只有当检测到其他账户余额时才显示划转按钮
        if total_balance_all.get('accounts', {}).get('other', 0) > 0:
            markup.row(
                types.InlineKeyboardButton("💱 划转到现货", callback_data="transfer_to_spot"),
                types.InlineKeyboardButton("📈 查看赚币", callback_data="view_earn")
            )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode='Markdown',
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"查询账户失败: {e}")

        # 降级处理：只显示现货余额
        try:
            balance = account.get_balance()
            if balance and 'error' not in balance:
                text = "💰 *账户资产（现货）*\n"
                text += "━━━━━━━━━━━━━━\n"
                text += f"总价值: *{balance['total_usdt']:.2f} USDT*\n"
                text += f"资产数: {balance['count']}\n\n"

                text += "*资产明细:*\n"
                for asset in balance['balance_list'][:10]:
                    if asset['value_usdt'] > 0.01:
                        emoji = "🟢" if asset['value_usdt'] > 10 else "🔵"
                        percentage = (asset['value_usdt'] / balance['total_usdt'] * 100) if balance['total_usdt'] > 0 else 0
                        text += f"{emoji} {asset['currency']}: {asset['balance']:.6f} "
                        text += f"(${asset['value_usdt']:.2f} | {percentage:.1f}%)\n"

                text += "\n_💡 提示：如有赚币余额，请在交易所APP查看_"

                bot.send_message(message.chat.id, text, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, "❌ 获取账户信息失败")

        except Exception as e2:
            logger.error(f"降级处理也失败: {e2}")
            bot.send_message(message.chat.id, "❌ 查询失败，请稍后重试")

# 添加刷新余额的回调处理
@bot.callback_query_handler(func=lambda call: call.data == 'refresh_balance')
@authorized_callback
def handle_refresh_balance(call):
    """刷新账户余额"""
    try:
        bot.answer_callback_query(call.id, "正在刷新...")

        # 重新调用handle_account的逻辑
        # 为了避免代码重复，发送一个虚拟的账户消息
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = '💰 账户'

        fake_msg = FakeMessage(call.message.chat.id, call.from_user)
        handle_account(fake_msg)

        # 删除原消息
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    except Exception as e:
        logger.error(f"刷新余额失败: {e}")
        bot.answer_callback_query(call.id, "刷新失败", show_alert=True)

# 添加划转到现货的回调处理
@bot.callback_query_handler(func=lambda call: call.data == 'transfer_to_spot')
@authorized_callback  
def handle_transfer_to_spot(call):
    """显示划转指引"""
    try:
        bot.answer_callback_query(call.id)

        text = "💱 *资金划转指引*\n"
        text += "━━━━━━━━━━━━━━\n\n"
        text += "检测到您有资金在其他账户（如赚币）\n\n"
        text += "*划转步骤：*\n"
        text += "1. 登录HTX交易所APP或网页\n"
        text += "2. 进入【资产】页面\n"
        text += "3. 找到【划转】功能\n"
        text += "4. 选择：赚币账户 → 现货账户\n"
        text += "5. 输入划转金额\n"
        text += "6. 确认划转\n\n"
        text += "_划转是即时的，无手续费_\n\n"
        text += "完成后点击刷新查看最新余额"

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🔄 刷新余额", callback_data="refresh_balance"),
            types.InlineKeyboardButton("返回", callback_data="back_account")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"显示划转指引失败: {e}")
        bot.answer_callback_query(call.id, "操作失败", show_alert=True)

# 添加查看赚币详情的回调处理
@bot.callback_query_handler(func=lambda call: call.data == 'view_earn')
@authorized_callback
def handle_view_earn(call):
    """显示赚币账户信息"""
    try:
        bot.answer_callback_query(call.id)

        text = "💎 *赚币账户说明*\n"
        text += "━━━━━━━━━━━━━━\n\n"
        text += "您的部分资金在HTX赚币产品中\n\n"
        text += "*常见赚币产品：*\n"
        text += "• 活期宝 - 随存随取，灵活理财\n"
        text += "• 定期宝 - 锁定期限，收益更高\n"
        text += "• 锁仓挖矿 - 锁仓获得奖励\n"
        text += "• 流动性挖矿 - 提供流动性赚取手续费\n\n"
        text += "*查看详情：*\n"
        text += "请登录HTX APP → 金融账户 → 赚币\n\n"
        text += "*提示：*\n"
        text += "如需交易，请先将资金划转到现货账户"

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("💱 划转指引", callback_data="transfer_to_spot"),
            types.InlineKeyboardButton("🔄 刷新余额", callback_data="refresh_balance")
        )
        markup.row(
            types.InlineKeyboardButton("返回", callback_data="back_account")
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"显示赚币信息失败: {e}")
        bot.answer_callback_query(call.id, "操作失败", show_alert=True)

# 添加返回账户的回调处理
@bot.callback_query_handler(func=lambda call: call.data == 'back_account')
@authorized_callback
def handle_back_account(call):
    """返回账户主页"""
    try:
        bot.answer_callback_query(call.id)

        # 重新显示账户信息
        class FakeMessage:
            def __init__(self, chat_id, from_user):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = from_user
                self.text = '💰 账户'

        fake_msg = FakeMessage(call.message.chat.id, call.from_user)

        # 删除当前消息
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        # 重新显示账户
        handle_account(fake_msg)

    except Exception as e:
        logger.error(f"返回账户失败: {e}")
        bot.answer_callback_query(call.id, "操作失败", show_alert=True)
@bot.message_handler(func=lambda message: message.text == '💱 交易')
@authorized_only
def handle_trading(message):
    """处理交易功能"""
    bot.send_message(
        message.chat.id,
        "💱 *选择交易操作:*",
        parse_mode='Markdown',
        reply_markup=get_trading_keyboard()
    )


@bot.message_handler(func=lambda message: message.text == '🎯 网格')
@authorized_only
def handle_grid(message):
    """处理网格交易"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    # 获取网格状态
    status = grid.get_grid_status()

    text = "🎯 *网格交易管理*\n"
    text += f"━━━━━━━━━━━━━━\n"
    text += f"总网格: {status['total_grids']}\n"
    text += f"活动网格: {status['active_grids']}\n\n"

    if status['grids']:
        text += "*网格列表:*\n"
        for g in status['grids']:
            status_icon = "🟢" if g['active'] else "🔴"
            text += f"{status_icon} {g['symbol'].upper()}: "
            text += f"成交{g['completed_trades']}单, "
            text += f"利润{g['total_profit']:.4f}\n"

    buttons = [
        [
            types.InlineKeyboardButton('创建网格', callback_data='grid_create'),
            types.InlineKeyboardButton('停止网格', callback_data='grid_stop')
        ],
        [
            types.InlineKeyboardButton('网格状态', callback_data='grid_status'),
            types.InlineKeyboardButton('返回主菜单', callback_data='back_main')
        ]
    ]

    for row in buttons:
        markup.row(*row)

    bot.send_message(
        message.chat.id,
        text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '🔔 预警')
@authorized_only
def handle_monitor(message):
    """处理监控预警"""
    user_id = str(message.from_user.id)

    # 获取活动预警
    alerts = monitor.get_active_alerts(user_id)

    text = "🔔 *预警管理*\n"
    text += f"━━━━━━━━━━━━━━\n"
    text += f"活动预警: {alerts['total']}\n\n"

    if alerts['alerts']:
        text += "*预警列表:*\n"
        for alert in alerts['alerts'][:10]:
            if alert['type'] == 'price':
                text += f"💹 {alert['symbol'].upper()}: "
                text += f"{alert['alert_type']} {alert['target_price']:.4f}\n"
            elif alert['type'] == 'volume':
                text += f"📊 {alert['symbol'].upper()}: "
                text += f"成交量>{alert['threshold']:.2f} ({alert['time_window']}min)\n"

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        [
            types.InlineKeyboardButton('添加价格预警', callback_data='alert_add_price'),
            types.InlineKeyboardButton('添加成交量预警', callback_data='alert_add_volume')
        ],
        [
            types.InlineKeyboardButton('查看所有预警', callback_data='alert_list'),
            types.InlineKeyboardButton('清除所有预警', callback_data='alert_clear')
        ],
        [
            types.InlineKeyboardButton('返回主菜单', callback_data='back_main')
        ]
    ]

    for row in buttons:
        markup.row(*row)

    bot.send_message(
        message.chat.id,
        text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '📈 盈亏')
@authorized_only
def handle_pnl(message):
    """处理盈亏查询"""
    try:
        pnl_info = account.get_daily_pnl()

        if 'error' in pnl_info:
            bot.send_message(message.chat.id, f"❌ {pnl_info.get('message', pnl_info['error'])}")
            return

        # 构建消息
        emoji = "📈" if pnl_info['is_profit'] else "📉"
        color = "🟢" if pnl_info['is_profit'] else "🔴"

        text = f"{emoji} *今日盈亏*\n"
        text += f"━━━━━━━━━━━━━━\n"
        text += f"昨日余额: {pnl_info['yesterday_balance']:.2f} USDT\n"
        text += f"当前余额: {pnl_info['current_balance']:.2f} USDT\n"
        text += f"{color} 盈亏金额: *{pnl_info['pnl']:+.2f} USDT*\n"
        text += f"{color} 盈亏比例: *{pnl_info['pnl_percent']:+.2f}%*\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"查询盈亏失败: {e}")
        bot.send_message(message.chat.id, "❌ 查询盈亏失败，请稍后重试")


@bot.message_handler(func=lambda message: message.text == '📊 图表')
@authorized_only
def handle_charts(message):
    """处理图表生成"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        [
            types.InlineKeyboardButton('BTC K线图', callback_data='chart_kline_btcusdt'),
            types.InlineKeyboardButton('ETH K线图', callback_data='chart_kline_ethusdt')
        ],
        [
            types.InlineKeyboardButton('资产分布', callback_data='chart_asset'),
            types.InlineKeyboardButton('市场概览', callback_data='chart_market')
        ],
        [
            types.InlineKeyboardButton('网格可视化', callback_data='chart_grid'),
            types.InlineKeyboardButton('返回主菜单', callback_data='back_main')
        ]
    ]

    for row in buttons:
        markup.row(*row)

    bot.send_message(
        message.chat.id,
        "📊 *选择要生成的图表:*",
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '⚙️ 设置')
@authorized_only
def handle_settings(message):
    """处理设置功能"""
    user_id = str(message.from_user.id)
    settings = config.load_user_settings(user_id)

    text = "⚙️ *用户设置*\n"
    text += f"━━━━━━━━━━━━━━\n"
    text += f"监控交易对: {', '.join(settings['symbols'])}\n"
    text += f"网格交易: {'开启' if settings['grid_enabled'] else '关闭'}\n"
    text += f"价格监控: {'开启' if settings['monitor_enabled'] else '关闭'}\n\n"
    text += "*通知设置:*\n"
    text += f"价格变化: {'✅' if settings['alert_settings']['price_change'] else '❌'}\n"
    text += f"订单成交: {'✅' if settings['alert_settings']['order_filled'] else '❌'}\n"
    text += f"网格更新: {'✅' if settings['alert_settings']['grid_update'] else '❌'}\n"

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        [
            types.InlineKeyboardButton('修改交易对', callback_data='settings_symbols'),
            types.InlineKeyboardButton('通知设置', callback_data='settings_alerts')
        ],
        [
            types.InlineKeyboardButton('导出配置', callback_data='settings_export'),
            types.InlineKeyboardButton('返回主菜单', callback_data='back_main')
        ]
    ]

    for row in buttons:
        markup.row(*row)

    bot.send_message(
        message.chat.id,
        text,
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '❓ 帮助')
@authorized_only
def handle_help(message):
    """处理帮助信息"""
    help_text = (
        "❓ *使用帮助*\n\n"
        "*基础功能:*\n"
        "💹 行情 - 查看实时价格和涨跌幅\n"
        "💰 账户 - 查看资产余额和分布\n"
        "📊 图表 - 生成K线和分析图表\n\n"
        "*交易功能:*\n"
        "💱 交易 - 执行买卖订单\n"
        "🎯 网格 - 自动网格交易策略\n"
        "🔔 预警 - 设置价格和成交量预警\n\n"
        "*其他功能:*\n"
        "📈 盈亏 - 查看今日盈亏情况\n"
        "⚙️ 设置 - 配置个人偏好\n\n"
        "*快捷命令:*\n"
        "/start - 启动机器人\n"
        "/help - 显示帮助信息\n"
        "/status - 查看系统状态\n\n"
        "💡 提示: 点击底部按钮快速访问功能"
    )

    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


# 添加/status命令
@bot.message_handler(commands=['status'])
@authorized_only
def status_command(message):
    """查看系统状态"""
    try:
        # 获取账户信息
        balance = account.get_balance()
        balance_ok = 'error' not in balance

        # 获取网格状态
        grid_status = grid.get_grid_status()

        # 获取预警状态
        alerts = monitor.get_active_alerts()

        text = "🔍 *系统状态*\n"
        text += "━━━━━━━━━━━━━━\n"
        text += f"✅ 机器人: 运行中\n"
        text += f"{'✅' if balance_ok else '❌'} API连接: {'正常' if balance_ok else '异常'}\n"
        text += f"📊 活动网格: {grid_status['active_grids']}\n"
        text += f"🔔 活动预警: {alerts['total']}\n"
        text += f"⏰ 服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        if balance_ok:
            text += f"\n💰 总资产: {balance['total_usdt']:.2f} USDT"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        bot.send_message(message.chat.id, "❌ 获取状态失败")


# 添加/help命令
@bot.message_handler(commands=['help'])
@authorized_only
def help_command(message):
    """帮助命令"""
    handle_help(message)


# 回调处理函数
@bot.callback_query_handler(func=lambda call: call.data.startswith('ticker_'))
@authorized_callback
def handle_ticker_callback(call):
    """处理行情查询回调"""
    try:
        symbol = call.data.replace('ticker_', '')

        if symbol == 'custom':
            bot.answer_callback_query(call.id, "请输入交易对 (如: btcusdt)")
            bot.send_message(call.message.chat.id, "请输入要查询的交易对（如: btcusdt）:")
            user_states[str(call.from_user.id)] = 'waiting_symbol'
        else:
            ticker = market.get_ticker(symbol)
            if ticker:
                emoji = "📈" if ticker['change'] > 0 else "📉"
                text = f"{emoji} *{symbol.upper()}*\n"
                text += f"━━━━━━━━━━━━━━\n"
                text += f"当前价: {ticker['close']:.4f}\n"
                text += f"24h涨跌: {ticker['change']:+.2f}%\n"
                text += f"24h最高: {ticker['high']:.4f}\n"
                text += f"24h最低: {ticker['low']:.4f}\n"
                text += f"24h成交量: {ticker['volume']:.2f}\n"
                text += f"买一: {ticker['bid']:.4f} ({ticker['bid_size']:.4f})\n"
                text += f"卖一: {ticker['ask']:.4f} ({ticker['ask_size']:.4f})\n"

                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown',
                    reply_markup=get_market_keyboard()
                )
            else:
                bot.answer_callback_query(call.id, "获取行情失败", show_alert=True)

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"处理行情回调失败: {e}")
        bot.answer_callback_query(call.id, "处理失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('market_'))
def handle_market_callback(call):
    """处理市场查询回调"""
    try:
        action = call.data.replace('market_', '')

        if action == 'top':
            # 获取涨幅榜
            tickers = market.get_all_tickers()
            sorted_tickers = sorted(tickers, key=lambda x: x['change'], reverse=True)[:10]

            text = "📈 *24小时涨幅榜*\n"
            text += "━━━━━━━━━━━━━━\n"
            for i, ticker in enumerate(sorted_tickers, 1):
                text += f"{i}. {ticker['symbol'].upper()}: +{ticker['change']:.2f}%\n"

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=get_market_keyboard()
            )

        elif action == 'bottom':
            # 获取跌幅榜
            tickers = market.get_all_tickers()
            sorted_tickers = sorted(tickers, key=lambda x: x['change'])[:10]

            text = "📉 *24小时跌幅榜*\n"
            text += "━━━━━━━━━━━━━━\n"
            for i, ticker in enumerate(sorted_tickers, 1):
                text += f"{i}. {ticker['symbol'].upper()}: {ticker['change']:.2f}%\n"

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=get_market_keyboard()
            )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"处理市场回调失败: {e}")
        bot.answer_callback_query(call.id, "处理失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('trade_'))
def handle_trade_callback(call):
    """处理交易回调"""
    try:
        user_id = str(call.from_user.id)
        action = call.data.replace('trade_', '')

        if action == 'buy_limit':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入限价买入参数，格式:\n"
                "交易对 价格 数量\n"
                "例如: btcusdt 50000 0.001"
            )
            user_states[user_id] = 'trade_buy_limit'

        elif action == 'sell_limit':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入限价卖出参数，格式:\n"
                "交易对 价格 数量\n"
                "例如: btcusdt 60000 0.001"
            )
            user_states[user_id] = 'trade_sell_limit'

        elif action == 'buy_market':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入市价买入参数，格式:\n"
                "交易对 金额(USDT)\n"
                "例如: btcusdt 100"
            )
            user_states[user_id] = 'trade_buy_market'

        elif action == 'sell_market':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入市价卖出参数，格式:\n"
                "交易对 数量\n"
                "例如: btcusdt 0.001"
            )
            user_states[user_id] = 'trade_sell_market'

        elif action == 'open_orders':
            # 获取未成交订单
            orders = trading.get_open_orders()

            if orders:
                text = "📋 *未成交订单*\n"
                text += "━━━━━━━━━━━━━━\n"
                for order in orders[:10]:
                    order_type = '买入' if 'buy' in order['type'] else '卖出'
                    text += f"• {order['symbol'].upper()} {order_type}\n"
                    text += f"  价格: {order['price']:.4f}\n"
                    text += f"  数量: {order['amount']:.6f}\n"
                    text += f"  ID: {order['order_id']}\n\n"
            else:
                text = "没有未成交订单"

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=get_trading_keyboard()
            )

        elif action == 'cancel_all':
            result = trading.cancel_all_orders()
            bot.answer_callback_query(call.id, result['message'], show_alert=True)

        elif action == 'history':
            history = trading.get_order_history(size=10)
            if history:
                text = "📜 *交易历史*\n━━━━━━━━━━━━━━\n"
                for order in history[:5]:
                    order_type = '买入' if 'buy' in order['type'] else '卖出'
                    text += f"• {order['symbol'].upper()}: {order_type}\n"
                    text += f"  价格: {order['price']:.4f}\n"
                    text += f"  成交额: {order['filled_cash']:.2f} USDT\n"
                    text += f"  手续费: {order['filled_fees']:.6f}\n\n"
            else:
                text = "暂无交易历史"

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=get_trading_keyboard()
            )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"处理交易回调失败: {e}")
        bot.answer_callback_query(call.id, "处理失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('grid_'))
@authorized_callback
def handle_grid_callback(call):
    """处理网格交易回调"""
    try:
        user_id = str(call.from_user.id)
        action = call.data.replace('grid_', '')

        if action == 'create':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入网格参数，格式：交易对 网格数量 每格数量\n"
                "例如：btcusdt 10 0.001\n"
                "将自动使用4小时K线高低点作为网格范围"
            )
            user_states[user_id] = 'waiting_grid_params'

        elif action == 'stop':
            status = grid.get_grid_status()
            if status['active_grids'] > 0:
                markup = types.InlineKeyboardMarkup()
                for g in status['grids']:
                    if g['active']:
                        btn = types.InlineKeyboardButton(
                            f"停止 {g['symbol'].upper()}",
                            callback_data=f"stop_grid_{g['symbol']}"
                        )
                        markup.add(btn)
                markup.add(types.InlineKeyboardButton('返回', callback_data='back_grid'))

                bot.edit_message_text(
                    "选择要停止的网格:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
            else:
                bot.answer_callback_query(call.id, "没有活动的网格", show_alert=True)

        elif action == 'status':
            status = grid.get_grid_status()
            text = "📊 *网格状态详情*\n━━━━━━━━━━━━━━\n"

            if status['grids']:
                for g in status['grids']:
                    status_icon = "🟢" if g['active'] else "🔴"
                    text += f"\n{status_icon} *{g['symbol'].upper()}*\n"
                    text += f"成交订单: {g['completed_trades']}\n"
                    text += f"总利润: {g['total_profit']:.4f} USDT\n"
                    text += f"活动订单: {g['active_orders']}\n"
            else:
                text += "暂无网格交易"

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"处理网格回调失败: {e}")
        bot.answer_callback_query(call.id, "处理失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_grid_'))
@authorized_callback
def handle_stop_grid(call):
    """停止特定网格"""
    try:
        symbol = call.data.replace('stop_grid_', '')
        result = grid.stop_grid(symbol)

        if result.get('success'):
            bot.answer_callback_query(call.id, result['message'], show_alert=True)
            handle_grid(call.message)  # 返回网格菜单
        else:
            bot.answer_callback_query(call.id, result.get('error', '停止失败'), show_alert=True)

    except Exception as e:
        logger.error(f"停止网格失败: {e}")
        bot.answer_callback_query(call.id, "停止失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('alert_'))
@authorized_callback
def handle_alert_callback(call):
    """处理预警回调"""
    try:
        user_id = str(call.from_user.id)
        action = call.data.replace('alert_', '')

        if action == 'add_price':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入价格预警，格式：交易对 目标价格 类型\n"
                "类型: cross(穿越) above(高于) below(低于)\n"
                "例如：btcusdt 35000 above"
            )
            user_states[user_id] = 'waiting_price_alert'

        elif action == 'add_volume':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "请输入成交量预警，格式：交易对 成交量阈值 时间窗口(分钟)\n"
                "例如：btcusdt 1000 60"
            )
            user_states[user_id] = 'waiting_volume_alert'

        elif action == 'list':
            alerts = monitor.get_active_alerts(user_id)
            text = "📋 *活动预警列表*\n━━━━━━━━━━━━━━\n"

            if alerts['alerts']:
                for alert in alerts['alerts']:
                    if alert['type'] == 'price':
                        text += f"💹 {alert['symbol'].upper()}: {alert['alert_type']} {alert['target_price']:.4f}\n"
                    elif alert['type'] == 'volume':
                        text += f"📊 {alert['symbol'].upper()}: >{alert['threshold']:.2f} ({alert['time_window']}min)\n"
            else:
                text += "暂无活动预警"

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )

        elif action == 'clear':
            alerts = monitor.get_active_alerts(user_id)
            cleared = 0
            for alert in alerts['alerts']:
                monitor.remove_alert(alert['id'])
                cleared += 1

            bot.answer_callback_query(call.id, f"已清除 {cleared} 个预警", show_alert=True)

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"处理预警回调失败: {e}")
        bot.answer_callback_query(call.id, "处理失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('chart_'))
@authorized_callback
def handle_chart_callback(call):
    """处理图表生成回调"""
    try:
        action = call.data.replace('chart_', '')

        if action.startswith('kline_'):
            symbol = action.replace('kline_', '')
            klines = market.get_klines(symbol, '1day', 100)
            if klines:
                chart_path = charts.generate_kline_chart(
                    klines,
                    symbol,
                    '1day',
                    indicators=['ma5', 'ma10', 'ma20', 'volume']
                )

                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, 'rb') as photo:
                        bot.send_photo(call.message.chat.id, photo)
                    bot.answer_callback_query(call.id, "K线图已生成")
                else:
                    bot.answer_callback_query(call.id, "生成失败", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "获取数据失败", show_alert=True)

        elif action == 'asset':
            distribution = account.get_asset_distribution()
            if 'error' not in distribution:
                chart_path = charts.generate_asset_pie_chart(distribution['distribution'])

                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, 'rb') as photo:
                        bot.send_photo(call.message.chat.id, photo)
                    bot.answer_callback_query(call.id, "资产分布图已生成")
                else:
                    bot.answer_callback_query(call.id, "生成失败", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "获取数据失败", show_alert=True)

        elif action == 'market':
            symbols = config.default_symbols
            tickers = []
            for symbol in symbols:
                ticker = market.get_ticker(symbol)
                if ticker:
                    tickers.append(ticker)

            if tickers:
                chart_path = charts.generate_market_overview(tickers)

                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, 'rb') as photo:
                        bot.send_photo(call.message.chat.id, photo)
                    bot.answer_callback_query(call.id, "市场概览图已生成")
                else:
                    bot.answer_callback_query(call.id, "生成失败", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "获取数据失败", show_alert=True)

        elif action == 'grid':
            status = grid.get_grid_status()
            if status['active_grids'] > 0:
                for symbol, config_grid in grid.active_grids.items():
                    ticker = market.get_ticker(symbol)
                    if ticker:
                        chart_path = charts.generate_grid_visualization(
                            config_grid,
                            ticker['close']
                        )

                        if chart_path and os.path.exists(chart_path):
                            with open(chart_path, 'rb') as photo:
                                bot.send_photo(call.message.chat.id, photo)
                        break

                bot.answer_callback_query(call.id, "网格图已生成")
            else:
                bot.answer_callback_query(call.id, "没有活动网格", show_alert=True)

        bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"生成图表失败: {e}")
        bot.answer_callback_query(call.id, "生成失败", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
@authorized_callback
def handle_back_main(call):
    """返回主菜单"""
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "请选择功能:",
        reply_markup=get_main_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'back_grid')
@authorized_callback
def handle_back_grid(call):
    """返回网格菜单"""
    bot.answer_callback_query(call.id)
    handle_grid(call.message)


# 处理文字消息（等待用户输入状态）
@bot.message_handler(func=lambda message: str(message.from_user.id) in user_states)
@authorized_only
def handle_user_input(message):
    """处理用户输入"""
    user_id = str(message.from_user.id)
    state = user_states.get(user_id)

    try:
        if state == 'waiting_symbol':
            symbol = message.text.lower().strip()
            ticker = market.get_ticker(symbol)

            if ticker:
                emoji = "📈" if ticker['change'] > 0 else "📉"
                text = f"{emoji} *{symbol.upper()}*\n"
                text += f"━━━━━━━━━━━━━━\n"
                text += f"当前价: {ticker['close']:.4f}\n"
                text += f"24h涨跌: {ticker['change']:+.2f}%\n"
                text += f"24h最高: {ticker['high']:.4f}\n"
                text += f"24h最低: {ticker['low']:.4f}\n"

                bot.send_message(message.chat.id, text, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, "❌ 无效的交易对或获取失败")

            del user_states[user_id]

        elif state == 'waiting_buy_limit':
            parts = message.text.split()
            if len(parts) == 4 and parts[0] == '买入':
                symbol = parts[1].lower()
                price = float(parts[2])
                amount = float(parts[3])

                result = trading.buy_limit(symbol, price, amount)
                if result.get('success'):
                    bot.send_message(
                        message.chat.id,
                        f"✅ 买单创建成功\n"
                        f"订单ID: {result['order_id']}\n"
                        f"交易对: {symbol.upper()}\n"
                        f"价格: {price:.4f}\n"
                        f"数量: {amount:.6f}"
                    )
                else:
                    bot.send_message(message.chat.id, f"❌ {result.get('error', '创建失败')}")
            else:
                bot.send_message(message.chat.id, "❌ 格式错误，请重新输入")

            del user_states[user_id]

        elif state == 'waiting_sell_limit':
            parts = message.text.split()
            if len(parts) == 4 and parts[0] == '卖出':
                symbol = parts[1].lower()
                price = float(parts[2])
                amount = float(parts[3])

                result = trading.sell_limit(symbol, price, amount)
                if result.get('success'):
                    bot.send_message(
                        message.chat.id,
                        f"✅ 卖单创建成功\n"
                        f"订单ID: {result['order_id']}\n"
                        f"交易对: {symbol.upper()}\n"
                        f"价格: {price:.4f}\n"
                        f"数量: {amount:.6f}"
                    )
                else:
                    bot.send_message(message.chat.id, f"❌ {result.get('error', '创建失败')}")
            else:
                bot.send_message(message.chat.id, "❌ 格式错误，请重新输入")

            del user_states[user_id]

        elif state == 'waiting_grid_params':
            parts = message.text.split()
            if len(parts) == 3:
                symbol = parts[0].lower()
                grid_count = int(parts[1])
                amount = float(parts[2])

                result = grid.create_grid(symbol, grid_count, amount)
                if result.get('success'):
                    bot.send_message(
                        message.chat.id,
                        f"✅ 网格创建成功\n"
                        f"交易对: {symbol.upper()}\n"
                        f"网格数: {grid_count}\n"
                        f"每格数量: {amount:.6f}\n"
                        f"初始订单: {result['initial_orders']}"
                    )
                else:
                    bot.send_message(message.chat.id, f"❌ {result.get('error', '创建失败')}")
            else:
                bot.send_message(message.chat.id, "❌ 格式错误，请重新输入")

            del user_states[user_id]

        elif state == 'waiting_price_alert':
            parts = message.text.split()
            if len(parts) == 3:
                symbol = parts[0].lower()
                target_price = float(parts[1])
                alert_type = parts[2].lower()

                result = monitor.add_price_alert(symbol, target_price, alert_type, user_id)
                if result.get('success'):
                    bot.send_message(message.chat.id, f"✅ {result['message']}")
                else:
                    bot.send_message(message.chat.id, f"❌ {result.get('error', '添加失败')}")
            else:
                bot.send_message(message.chat.id, "❌ 格式错误，请重新输入")

            del user_states[user_id]

        elif state == 'waiting_volume_alert':
            parts = message.text.split()
            if len(parts) == 3:
                symbol = parts[0].lower()
                threshold = float(parts[1])
                time_window = int(parts[2])

                result = monitor.add_volume_alert(symbol, threshold, time_window, user_id)
                if result.get('success'):
                    bot.send_message(message.chat.id, f"✅ {result['message']}")
                else:
                    bot.send_message(message.chat.id, f"❌ {result.get('error', '添加失败')}")
            else:
                bot.send_message(message.chat.id, "❌ 格式错误，请重新输入")

            del user_states[user_id]

    except Exception as e:
        logger.error(f"处理用户输入失败: {e}")
        bot.send_message(message.chat.id, "❌ 处理失败，请重试")
        if user_id in user_states:
            del user_states[user_id]


# 定时任务
def check_monitors():
    """检查监控预警"""
    try:
        # 检查价格预警
        monitor.check_price_alerts()

        # 检查成交量预警
        monitor.check_volume_alerts()

        # 检查订单成交
        monitor.check_order_alerts()

        # 检查网格更新
        for symbol in grid.active_grids:
            grid.update_grid(symbol)

    except Exception as e:
        logger.error(f"监控检查失败: {e}")


def check_4hour_update():
    """检查4小时K线更新"""
    try:
        result = grid.check_4hour_update()

        for notification in result['notifications']:
            text = f"📊 *4小时K线更新*\n"
            text += f"交易对: {notification['symbol'].upper()}\n"
            text += f"当前范围: {notification['current_range']}\n"
            text += f"新范围: {notification['new_range']}\n"
            text += f"变化幅度: {notification['change_percent']:.2f}%\n"
            text += f"{notification['message']}"

            if config.telegram.chat_id:
                bot.send_message(config.telegram.chat_id, text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"4小时检查失败: {e}")


def save_daily_balance():
    """保存每日余额"""
    try:
        account.save_yesterday_balance()
        logger.info("每日余额已保存")
    except Exception as e:
        logger.error(f"保存每日余额失败: {e}")


def main():
    """主函数"""
    logger.info("HTX Telegram Bot 启动中...")

    # 添加定时任务
    scheduler.add_job(
        check_monitors,
        'interval',
        seconds=config.monitor.interval,
        id='monitor_check'
    )

    scheduler.add_job(
        check_4hour_update,
        CronTrigger(hour='*/4'),
        id='4hour_check'
    )

    scheduler.add_job(
        save_daily_balance,
        CronTrigger(hour=0, minute=0, timezone=config.timezone),
        id='daily_balance'
    )

    scheduler.add_job(
        charts.cleanup_old_charts,
        CronTrigger(hour=2, minute=0),
        id='cleanup_charts'
    )

    # 启动调度器
    scheduler.start()
    logger.info("定时任务已启动")

    # 启动机器人
    logger.info("机器人开始运行...")
    bot.polling(none_stop=True, timeout=60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("机器人停止运行")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"机器人运行出错: {e}")
        scheduler.shutdown()