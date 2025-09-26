#!/usr/bin/env python3
"""
HTX账户诊断脚本
自动尝试所有可能的API找出赚币余额
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import requests
from urllib.parse import urlencode
from datetime import datetime, timezone
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class HTXDiagnostic:
    def __init__(self):
        self.access_key = os.getenv('HTX_ACCESS_KEY')
        self.secret_key = os.getenv('HTX_SECRET_KEY')
        self.rest_url = "https://api.huobi.pro"

        if not self.access_key or not self.secret_key:
            print("❌ 请设置HTX_ACCESS_KEY和HTX_SECRET_KEY")
            sys.exit(1)

        print("=" * 60)
        print("    HTX账户完整诊断")
        print("=" * 60)
        print()

        self.results = {}
        self.total_balance = 0
        self.spot_balance = 0
        self.other_balance = 0

    def _generate_signature(self, method, path, params=None):
        if params is None:
            params = {}

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

        params_to_sign = {
            'AccessKeyId': self.access_key,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp
        }

        if params:
            params_to_sign.update(params)

        sorted_params = sorted(params_to_sign.items())
        encode_params = urlencode(sorted_params)

        host = 'api.huobi.pro'
        payload = f"{method}\n{host}\n{path}\n{encode_params}"

        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        params_to_sign['Signature'] = signature
        return params_to_sign

    def make_request(self, path, params=None):
        try:
            url = f"{self.rest_url}{path}"
            signed_params = self._generate_signature('GET', path, params)
            response = requests.get(url, params=signed_params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def test_accounts(self):
        """测试1: 获取所有账户"""
        print("📊 测试1: 获取所有账户类型")
        print("-" * 40)

        result = self.make_request('/v1/account/accounts')

        if result.get('status') == 'ok':
            accounts = result.get('data', [])
            print(f"✅ 找到 {len(accounts)} 个账户\n")

            for acc in accounts:
                acc_type = acc.get('type')
                acc_id = acc.get('id')
                acc_state = acc.get('state')
                print(f"  • {acc_type}: ID={acc_id}, 状态={acc_state}")

                # 获取每个账户余额
                if acc_state == 'working':
                    balance_result = self.make_request(f'/v1/account/accounts/{acc_id}/balance')
                    if balance_result.get('status') == 'ok':
                        total = 0
                        for item in balance_result.get('data', {}).get('list', []):
                            if item.get('type') == 'trade':
                                bal = float(item.get('balance', 0))
                                curr = item.get('currency', '').upper()
                                if curr == 'USDT':
                                    total += bal

                        if total > 0:
                            print(f"    💰 余额: {total:.4f} USDT")
                            if acc_type == 'spot':
                                self.spot_balance = total
                            else:
                                self.other_balance += total

            return True

        return False

    def test_valuation_apis(self):
        """测试2: 资产估值API"""
        print("\n📊 测试2: 资产估值API")
        print("-" * 40)

        # 尝试不同的API参数
        test_cases = [
            {
                'path': '/v1/account/asset-valuation',
                'params': {'accountType': '1', 'valuationCurrency': 'USDT'},
                'name': '所有账户(accountType=1)'
            },
            {
                'path': '/v1/account/asset-valuation',
                'params': {'accountType': 'spot', 'valuationCurrency': 'USDT'},
                'name': '现货账户'
            },
            {
                'path': '/v1/account/asset-valuation',
                'params': {'accountType': 'savings', 'valuationCurrency': 'USDT'},
                'name': '理财账户'
            },
            {
                'path': '/v2/account/valuation',
                'params': {'accountType': 'spot', 'valuationCurrency': 'USD'},
                'name': 'V2 API'
            },
            {
                'path': '/v2/account/asset-valuation',
                'params': {'accountType': 'total'},
                'name': '总资产估值'
            }
        ]

        max_value = 0

        for test in test_cases:
            print(f"\n尝试: {test['name']}")
            result = self.make_request(test['path'], test['params'])

            if result.get('status') == 'ok' or result.get('code') == 200:
                data = result.get('data', {})
                balance = float(data.get('balance', 0))

                if balance > 0:
                    print(f"  ✅ 成功: {balance:.2f} USDT")
                    max_value = max(max_value, balance)

                    # 显示详细信息
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if key != 'balance':
                                print(f"    • {key}: {value}")
                else:
                    print(f"  ⚠️ 余额为0")
            else:
                err = result.get('err-msg', result.get('message', ''))
                print(f"  ❌ 失败: {err[:50]}")

        if max_value > 0:
            self.total_balance = max_value
            print(f"\n💎 最大总资产: {max_value:.2f} USDT")
            return True

        return False

    def test_earn_apis(self):
        """测试3: 赚币/理财API"""
        print("\n📊 测试3: 赚币/理财产品API")
        print("-" * 40)

        earn_apis = [
            ('/v1/account/history', {'currency': 'usdt', 'size': '10'}, '账户历史'),
            ('/v1/stable-coin/quote', {}, '稳定币理财报价'),
            ('/v1/stable-coin/account', {}, '稳定币账户'),
            ('/v2/account/ledger', {'accountType': 'savings'}, '账本记录'),
            ('/v1/earn/account', {}, '赚币账户'),
            ('/v2/earn/balance', {}, '赚币余额'),
            ('/v1/deposit-withdraw/deposit-address', {'currency': 'usdt'}, '充值地址（测试权限）'),
            ('/v1/c2c/balance', {}, 'C2C余额'),
            ('/v1/savings/balance', {}, '理财余额'),
            ('/v2/point/account', {}, '点卡账户'),
        ]

        found_earn = False

        for path, params, name in earn_apis:
            print(f"\n测试: {name}")
            result = self.make_request(path, params)

            if result.get('status') == 'ok' or result.get('code') == 200:
                data = result.get('data')
                if data:
                    print(f"  ✅ 有响应")

                    # 尝试解析余额
                    if isinstance(data, dict):
                        # 查找balance字段
                        for key in ['balance', 'total', 'amount', 'available']:
                            if key in data:
                                value = float(data[key])
                                if value > 0:
                                    print(f"    💰 {key}: {value}")
                                    found_earn = True

                    elif isinstance(data, list) and data:
                        print(f"    📋 返回了{len(data)}条记录")
                        # 显示第一条记录
                        if data[0]:
                            print(f"    样例: {json.dumps(data[0], indent=2)[:200]}")
                else:
                    print(f"  ⚠️ 无数据")
            else:
                err = result.get('err-msg', result.get('message', ''))
                if 'not found' not in err.lower() and 'invalid' not in err.lower():
                    print(f"  ❌ {err[:50]}")
                else:
                    print(f"  ⚠️ API不可用")

        return found_earn

    def test_alternative_methods(self):
        """测试4: 其他获取余额的方法"""
        print("\n📊 测试4: 其他方法")
        print("-" * 40)

        # 方法1: 获取充值记录
        print("\n尝试: 充值历史")
        deposit_result = self.make_request('/v1/query/deposit-withdraw', {
            'type': 'deposit',
            'currency': 'usdt',
            'size': '10'
        })

        if deposit_result.get('status') == 'ok':
            deposits = deposit_result.get('data', [])
            if deposits:
                print(f"  ✅ 找到{len(deposits)}条充值记录")
                total_deposits = sum(float(d.get('amount', 0)) for d in deposits)
                print(f"    总充值: {total_deposits:.2f} USDT")

        # 方法2: 获取交易历史
        print("\n尝试: 交易历史")
        trade_result = self.make_request('/v1/order/matchresults', {
            'symbol': 'btcusdt',
            'size': '10'
        })

        if trade_result.get('status') == 'ok':
            trades = trade_result.get('data', [])
            if trades:
                print(f"  ✅ 找到{len(trades)}条交易记录")

        # 方法3: 获取财务记录
        print("\n尝试: 财务记录")
        finance_result = self.make_request('/v2/account/ledger', {
            'accountType': 'spot'
        })

        if finance_result.get('code') == 200:
            records = finance_result.get('data', [])
            if records:
                print(f"  ✅ 找到{len(records)}条财务记录")

        return True

    def analyze_results(self):
        """分析诊断结果"""
        print("\n" + "=" * 60)
        print("📋 诊断结果分析")
        print("=" * 60)

        print(f"\n现货余额: {self.spot_balance:.4f} USDT")
        print(f"总资产估值: {self.total_balance:.2f} USDT")

        if self.total_balance > self.spot_balance:
            other = self.total_balance - self.spot_balance
            print(f"其他账户: {other:.2f} USDT")
            print("\n✅ 检测到其他账户余额（可能是赚币）")
            print("\n建议操作：")
            print("1. 登录HTX APP查看【金融账户】")
            print("2. 检查【赚币】中的活期/定期产品")
            print("3. 如需交易，划转到现货账户")
        else:
            print("\n⚠️ 未检测到赚币余额")
            print("\n可能原因：")
            print("1. 赚币资金在独立系统")
            print("2. API权限不足")
            print("3. 需要单独的赚币API密钥")

        # 生成修复代码
        self.generate_fix()

    def generate_fix(self):
        """生成修复代码"""
        print("\n" + "=" * 60)
        print("🔧 生成修复方案")
        print("=" * 60)

        if self.total_balance > self.spot_balance:
            other = self.total_balance - self.spot_balance

            print(f"\n将在account.py中硬编码以下值：")
            print(f"• 现货余额: {self.spot_balance:.4f} USDT")
            print(f"• 赚币余额: {other:.2f} USDT")
            print(f"• 总余额: {self.total_balance:.2f} USDT")

            # 保存配置
            config = {
                'spot_balance': self.spot_balance,
                'earn_balance': other,
                'total_balance': self.total_balance,
                'diagnosed_at': datetime.now().isoformat()
            }

            os.makedirs('data', exist_ok=True)
            with open('data/account_diagnosis.json', 'w') as f:
                json.dump(config, f, indent=2)

            print("\n✅ 诊断结果已保存到 data/account_diagnosis.json")
            print("   账户模块将自动读取此配置")
        else:
            print("\n请手动输入赚币余额")
            try:
                earn = float(input("赚币余额(USDT): "))

                config = {
                    'spot_balance': self.spot_balance,
                    'earn_balance': earn,
                    'total_balance': self.spot_balance + earn,
                    'diagnosed_at': datetime.now().isoformat(),
                    'manual_input': True
                }

                os.makedirs('data', exist_ok=True)
                with open('data/account_diagnosis.json', 'w') as f:
                    json.dump(config, f, indent=2)

                print("\n✅ 配置已保存")

            except:
                print("❌ 输入无效")

    def run(self):
        """运行诊断"""
        print("开始诊断...\n")

        # 运行测试
        self.test_accounts()
        self.test_valuation_apis()
        self.test_earn_apis()
        self.test_alternative_methods()

        # 分析结果
        self.analyze_results()

        print("\n诊断完成！")
        print("\n下一步：")
        print("1. 替换 modules/account/account.py")
        print("2. 重启机器人")
        print("3. 测试 💰 账户 功能")


if __name__ == '__main__':
    diagnostic = HTXDiagnostic()
    diagnostic.run()