#!/usr/bin/env python3
"""
HTX交易机器人测试脚本
测试各个模块功能是否正常
"""

import os
import sys
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import config
from utils.logger import logger
from modules.market.market import MarketModule
from modules.account.account import AccountModule
from modules.trading.trading import TradingModule

def test_config():
    """测试配置"""
    print("\n" + "="*50)
    print("📋 测试配置加载")
    print("="*50)
    
    try:
        assert config.telegram.bot_token, "Telegram Bot Token未配置"
        print("✅ Telegram配置正常")
        
        assert config.htx.access_key, "HTX Access Key未配置"
        assert config.htx.secret_key, "HTX Secret Key未配置"
        print("✅ HTX API配置正常")
        
        print(f"📝 默认交易对: {', '.join(config.default_symbols)}")
        print(f"📝 时区设置: {config.timezone}")
        print(f"📝 日志级别: {config.log_level}")
        
        return True
    except AssertionError as e:
        print(f"❌ 配置错误: {e}")
        return False

def test_market_module():
    """测试市场数据模块"""
    print("\n" + "="*50)
    print("💹 测试市场数据模块")
    print("="*50)
    
    try:
        market = MarketModule(
            config.htx.access_key,
            config.htx.secret_key,
            config.htx.rest_url
        )
        
        # 测试获取交易对
        print("🔍 获取交易对列表...")
        symbols = market.get_symbols()
        if symbols:
            print(f"✅ 获取到 {len(symbols)} 个交易对")
        else:
            print("⚠️  未获取到交易对")
        
        # 测试获取行情
        print("\n🔍 测试BTC/USDT行情...")
        ticker = market.get_ticker('btcusdt')
        if ticker:
            print(f"✅ BTC/USDT")
            print(f"   当前价: {ticker['close']:.2f}")
            print(f"   24h涨跌: {ticker['change']:+.2f}%")
            print(f"   24h成交量: {ticker['volume']:.2f}")
        else:
            print("❌ 获取行情失败")
        
        # 测试获取K线
        print("\n🔍 获取K线数据...")
        klines = market.get_klines('btcusdt', '1day', 10)
        if klines:
            print(f"✅ 获取到 {len(klines)} 根K线")
        else:
            print("❌ 获取K线失败")
        
        # 测试获取深度
        print("\n🔍 获取深度数据...")
        depth = market.get_depth('btcusdt', 5)
        if depth:
            print(f"✅ 获取深度成功")
            print(f"   买盘深度: {len(depth['bids'])}")
            print(f"   卖盘深度: {len(depth['asks'])}")
        else:
            print("❌ 获取深度失败")
        
        return True
    except Exception as e:
        print(f"❌ 市场模块测试失败: {e}")
        return False

def test_account_module():
    """测试账户模块"""
    print("\n" + "="*50)
    print("💰 测试账户管理模块")
    print("="*50)
    
    try:
        account = AccountModule(
            config.htx.access_key,
            config.htx.secret_key,
            config.htx.rest_url
        )
        
        # 测试获取账户ID
        if account.account_id:
            print(f"✅ 账户ID: {account.account_id}")
        else:
            print("❌ 获取账户ID失败")
            return False
        
        # 测试获取余额
        print("\n🔍 获取账户余额...")
        balance = account.get_balance()
        if 'error' not in balance:
            print(f"✅ 总价值: {balance['total_usdt']:.2f} USDT")
            print(f"   资产数: {len(balance['assets'])}")
            
            # 显示前3个资产
            for asset in balance['assets'][:3]:
                print(f"   {asset['currency'].upper()}: {asset['balance']:.6f}")
        else:
            print(f"❌ 获取余额失败: {balance['error']}")
        
        # 测试资产分布
        print("\n🔍 获取资产分布...")
        distribution = account.get_asset_distribution()
        if 'error' not in distribution:
            print(f"✅ 资产分布获取成功")
            for asset in distribution['distribution'][:3]:
                print(f"   {asset['currency'].upper()}: {asset['percentage']:.2f}%")
        else:
            print("❌ 获取资产分布失败")
        
        return True
    except Exception as e:
        print(f"❌ 账户模块测试失败: {e}")
        return False

def test_trading_module():
    """测试交易模块"""
    print("\n" + "="*50)
    print("💱 测试交易模块")
    print("="*50)
    
    try:
        trading = TradingModule(
            config.htx.access_key,
            config.htx.secret_key,
            config.htx.rest_url
        )
        
        # 测试获取交易对信息
        print("🔍 获取交易对信息...")
        symbol_info = trading.get_symbol_info('btcusdt')
        if symbol_info:
            print(f"✅ BTC/USDT交易对信息")
            print(f"   价格精度: {symbol_info['price_precision']}")
            print(f"   数量精度: {symbol_info['amount_precision']}")
            print(f"   最小订单: {symbol_info['min_order_amount']}")
            print(f"   最小价值: {symbol_info['min_order_value']} USDT")
        else:
            print("❌ 获取交易对信息失败")
        
        # 测试获取未成交订单
        print("\n🔍 获取未成交订单...")
        open_orders = trading.get_open_orders()
        print(f"✅ 未成交订单: {len(open_orders)} 个")
        
        # 测试获取历史订单
        print("\n🔍 获取历史订单...")
        history_orders = trading.get_order_history(size=10)
        print(f"✅ 历史订单: {len(history_orders)} 个")
        
        print("\n⚠️  注意: 未测试实际下单功能（避免真实交易）")
        
        return True
    except Exception as e:
        print(f"❌ 交易模块测试失败: {e}")
        return False

def test_websocket():
    """测试WebSocket连接"""
    print("\n" + "="*50)
    print("🌐 测试WebSocket连接")
    print("="*50)
    
    try:
        from utils.websocket_client import HTXWebSocketClient
        
        ws_client = HTXWebSocketClient()
        
        # 定义回调函数
        def on_ticker(data):
            print(f"📊 收到行情推送: {data.get('ch', 'unknown')}")
        
        # 连接并订阅
        print("🔄 连接WebSocket...")
        ws_client.connect()
        time.sleep(2)
        
        # 订阅BTC行情
        print("📡 订阅BTC/USDT行情...")
        ws_client.subscribe_ticker('btcusdt', on_ticker)
        
        # 等待推送
        print("⏳ 等待数据推送 (10秒)...")
        time.sleep(10)
        
        # 关闭连接
        ws_client.close()
        print("✅ WebSocket测试完成")
        
        return True
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

def run_tests():
    """运行所有测试"""
    print("\n" + "🚀 HTX交易机器人测试开始 🚀")
    print("="*50)
    
    results = {
        '配置': test_config(),
        '市场数据': test_market_module(),
        '账户管理': test_account_module(),
        '交易功能': test_trading_module(),
        'WebSocket': test_websocket()
    }
    
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    for module, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{module}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "="*50)
    if passed == total:
        print(f"🎉 所有测试通过 ({passed}/{total})")
    else:
        print(f"⚠️  部分测试失败 ({passed}/{total})")
    print("="*50)

if __name__ == "__main__":
    run_tests()
