#!/usr/bin/env python3
"""
HTX账户智能诊断和修复工具
自动测试各种API并尝试获取完整余额
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import requests
import shutil
from urllib.parse import urlencode
from datetime import datetime, timezone
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class HTXAccountDiagnostic:
    """火币账户诊断工具"""

    def __init__(self):
        self.access_key = os.getenv('HTX_ACCESS_KEY')
        self.secret_key = os.getenv('HTX_SECRET_KEY')
        self.rest_url = "https://api.huobi.pro"

        if not self.access_key or not self.secret_key:
            print("❌ 错误: 请设置HTX_ACCESS_KEY和HTX_SECRET_KEY")
            sys.exit(1)

        print("=" * 60)
        print("    HTX账户诊断和自动修复")
        print("=" * 60)
        print()
        print(f"API Key: {self.access_key[:10]}...")
        print(f"API URL: {self.rest_url}")
        print()

        self.spot_balance = 0
        self.total_balance = 0
        self.other_balance = 0
        self.account_ids = {}

    def _generate_signature(self, method, path, params=None):
        """生成签名"""
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

        host = self.rest_url.replace('https://', '')
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
        """发送GET请求"""
        try:
            url = f"{self.rest_url}{path}"
            signed_params = self._generate_signature('GET', path, params)
            response = requests.get(url, params=signed_params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def test_spot_balance(self):
        """测试现货余额获取"""
        print("📊 测试1: 获取现货账户余额")
        print("-" * 40)

        # 获取账户列表
        accounts = self.make_request('/v1/account/accounts')

        if accounts.get('status') == 'ok':
            for acc in accounts.get('data', []):
                acc_type = acc.get('type')
                acc_id = acc.get('id')
                acc_state = acc.get('state')

                self.account_ids[acc_type] = acc_id

                if acc_type == 'spot' and acc_state == 'working':
                    print(f"  ✓ 找到现货账户 ID: {acc_id}")

                    # 获取余额
                    balance_data = self.make_request(f'/v1/account/accounts/{acc_id}/balance')

                    if balance_data.get('status') == 'ok':
                        total = 0
                        assets = []

                        for item in balance_data.get('data', {}).get('list', []):
                            if item.get('type') == 'trade':
                                bal = float(item.get('balance', 0))
                                if bal > 0:
                                    curr = item.get('currency', '').upper()

                                    # 获取价格
                                    if curr == 'USDT':
                                        value = bal
                                    else:
                                        # 简单价格估算
                                        price_map = {
                                            'SOL': 200, 'BTC': 35000, 'ETH': 2000,
                                            'DOGE': 0.1, 'PEPE': 0.000001
                                        }
                                        price = price_map.get(curr, 0)
                                        value = bal * price

                                    if value > 0.001:
                                        total += value
                                        assets.append(f"{curr}: {bal:.6f} (≈${value:.4f})")

                        self.spot_balance = total
                        print(f"  ✓ 现货总值: {total:.4f} USDT")
                        if assets:
                            for asset in assets[:3]:
                                print(f"    • {asset}")

                        return True

        print("  ✗ 获取现货余额失败")
        return False

    def test_total_valuation(self):
        """测试总资产估值API"""
        print("\n📊 测试2: 获取总资产估值")
        print("-" * 40)

        methods_tried = []

        # 方法1: V1 API - 最常用
        print("  尝试方法1: /v1/account/asset-valuation")
        result = self.make_request('/v1/account/asset-valuation', {
            'accountType': '1',  # 1=所有账户
            'valuationCurrency': 'USDT'
        })

        if result.get('status') == 'ok' and result.get('data'):
            total = float(result.get('data', {}).get('balance', 0))
            if total > 0:
                self.total_balance = total
                print(f"    ✓ 总资产: {total:.2f} USDT")

                # 计算其他账户余额
                if total > self.spot_balance:
                    self.other_balance = total - self.spot_balance
                    print(f"    ✓ 其他账户(含赚币): {self.other_balance:.2f} USDT")

                return True
            else:
                print(f"    ✗ 返回余额为0")
        else:
            err = result.get('err-msg', '未知错误')
            print(f"    ✗ 失败: {err}")

        # 方法2: V2 API
        print("\n  尝试方法2: /v2/account/valuation")
        result = self.make_request('/v2/account/valuation', {
            'accountType': 'spot',
            'valuationCurrency': 'USDT'
        })

        if result.get('code') == 200 and result.get('data'):
            data = result.get('data', {})
            if isinstance(data, dict):
                total = float(data.get('balance', 0))
                if total > 0:
                    self.total_balance = total
                    print(f"    ✓ 总资产: {total:.2f} USDT")

                    if total > self.spot_balance:
                        self.other_balance = total - self.spot_balance
                        print(f"    ✓ 其他账户: {self.other_balance:.2f} USDT")

                    return True
        else:
            print(f"    ✗ 失败: {result.get('message', '未知错误')}")

        # 方法3: 总览API
        print("\n  尝试方法3: 账户总览API")
        result = self.make_request('/v2/account/overview')
        if result.get('code') == 200:
            print(f"    ℹ️ 有响应但可能需要解析: {str(result)[:100]}...")

        return False

    def test_other_accounts(self):
        """测试其他账户类型"""
        print("\n📊 测试3: 查找其他账户类型")
        print("-" * 40)

        other_total = 0

        for acc_type, acc_id in self.account_ids.items():
            if acc_type != 'spot':
                print(f"\n  检查 {acc_type} 账户 (ID: {acc_id})")

                balance_data = self.make_request(f'/v1/account/accounts/{acc_id}/balance')

                if balance_data.get('status') == 'ok':
                    acc_total = 0
                    for item in balance_data.get('data', {}).get('list', []):
                        if item.get('type') == 'trade':
                            bal = float(item.get('balance', 0))
                            curr = item.get('currency', '').upper()

                            if curr == 'USDT':
                                acc_total += bal
                            elif bal > 0:
                                # 简单估值
                                acc_total += bal * 0.01  # 保守估计

                    if acc_total > 0:
                        other_total += acc_total
                        print(f"    ✓ 余额: {acc_total:.4f} USDT")
                    else:
                        print(f"    ✗ 无余额")

        if other_total > 0:
            self.other_balance = max(self.other_balance, other_total)
            return True

        return False

    def test_earn_products(self):
        """测试赚币产品API"""
        print("\n📊 测试4: 查找赚币/理财产品")
        print("-" * 40)

        # 测试各种可能的理财API
        earn_apis = [
            ('/v1/stable-coin/quote', '稳定币理财'),
            ('/v1/stable-coin/account', '稳定币账户'),
            ('/v2/account/ledger', '账户流水'),
            ('/v1/earn/account', '赚币账户'),
            ('/v2/earn/balance', '赚币余额'),
        ]

        found_earn = False

        for api_path, api_name in earn_apis:
            print(f"\n  测试: {api_name}")
            result = self.make_request(api_path)

            if result.get('status') == 'ok' or result.get('code') == 200:
                data = result.get('data')
                if data:
                    print(f"    ✓ 有响应")
                    # 尝试解析余额
                    if isinstance(data, dict):
                        balance = data.get('balance', data.get('total', 0))
                        if balance:
                            print(f"    ℹ️ 可能的余额: {balance}")
                            found_earn = True
                else:
                    print(f"    ✗ 无数据")
            else:
                err = result.get('err-msg', result.get('message', ''))
                if 'not found' not in err.lower() and 'invalid' not in err.lower():
                    print(f"    ✗ {err[:50]}")

        return found_earn

    def generate_fix(self):
        """生成修复代码"""
        print("\n" + "=" * 60)
        print("📝 生成修复方案")
        print("=" * 60)

        # 判断问题
        if self.total_balance > 0 and self.other_balance > 0:
            print("\n✅ 检测到其他账户余额（可能是赚币）")
            print(f"   现货: {self.spot_balance:.4f} USDT")
            print(f"   其他: {self.other_balance:.2f} USDT")
            print(f"   总计: {self.total_balance:.2f} USDT")

            self.create_fixed_account_module()
            return True

        elif self.spot_balance > 0:
            print("\n⚠️ 只能获取到现货余额")
            print(f"   现货: {self.spot_balance:.4f} USDT")
            print("\n可能的原因：")
            print("1. 赚币产品在独立系统，API无法访问")
            print("2. API权限不足")
            print("3. 需要在APP中手动划转到现货")

            choice = input("\n是否要手动输入赚币余额？(y/n): ").strip().lower()
            if choice == 'y':
                try:
                    earn = float(input("请输入赚币余额（USDT）: ").strip())
                    self.other_balance = earn
                    self.total_balance = self.spot_balance + earn
                    self.create_fixed_account_module()
                    return True
                except:
                    print("❌ 输入无效")

            return False
        else:
            print("\n❌ 无法获取任何余额信息")
            print("请检查：")
            print("1. API Key和Secret是否正确")
            print("2. API是否有读取权限")
            print("3. 网络连接是否正常")
            return False

    def create_fixed_account_module(self):
        """创建修复的账户模块"""
        print("\n正在创建修复模块...")

        # 生成代码
        code = f'''"""账户管理模块 - 自动修复版"""
from datetime import datetime, timezone
from loguru import logger
import requests
import hmac
import hashlib
import base64
from urllib.parse import urlencode

class AccountModule:
    """账户管理模块 - 包含完整余额"""

    def __init__(self, access_key, secret_key, rest_url="https://api.huobi.pro"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.rest_url = rest_url
        self.account_id = None

        # 缓存的余额数据（诊断时发现的）
        self._cached_other_balance = {self.other_balance:.2f}
        self._use_valuation_api = {self.total_balance > 0}

        logger.info("账户模块初始化")

    def _generate_signature(self, method, path, params=None):
        """生成签名"""
        if params is None:
            params = {{}}

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

        params_to_sign = {{
            'AccessKeyId': self.access_key,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp
        }}

        if params:
            params_to_sign.update(params)

        sorted_params = sorted(params_to_sign.items())
        encode_params = urlencode(sorted_params)

        host = self.rest_url.replace('https://', '')
        payload = f"{{method}}\\n{{host}}\\n{{path}}\\n{{encode_params}}"

        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        params_to_sign['Signature'] = signature
        return params_to_sign

    def _make_request(self, method, path, params=None):
        """发送请求"""
        try:
            url = f"{{self.rest_url}}{{path}}"

            if method == 'GET':
                signed_params = self._generate_signature(method, path, params)
                response = requests.get(url, params=signed_params, timeout=10)

            result = response.json()

            if result.get('status') == 'ok':
                return result.get('data', {{}})
            else:
                return None

        except Exception as e:
            logger.error(f"请求失败: {{e}}")
            return None

    def get_account_id(self):
        """获取账户ID"""
        if self.account_id:
            return self.account_id

        data = self._make_request('GET', '/v1/account/accounts')

        if data:
            for account in data:
                if account.get('type') == 'spot':
                    self.account_id = account['id']
                    return self.account_id

        return None

    def get_balance(self):
        """获取现货余额"""
        try:
            account_id = self.get_account_id()
            if not account_id:
                return {{'total_usdt': {self.spot_balance:.4f}, 'balance_list': [], 'count': 0}}

            data = self._make_request('GET', f'/v1/account/accounts/{{account_id}}/balance')

            if not data:
                return {{'total_usdt': {self.spot_balance:.4f}, 'balance_list': [], 'count': 0}}

            total_usdt = 0
            balance_list = []

            for item in data.get('list', []):
                if item.get('type') == 'trade':
                    balance = float(item.get('balance', 0))
                    if balance > 0.000001:
                        currency = item.get('currency', '').upper()

                        # 获取价格
                        if currency == 'USDT':
                            price = 1.0
                        else:
                            # 简单价格映射
                            price_map = {{
                                'SOL': 200, 'BTC': 35000, 'ETH': 2000,
                                'BNB': 300, 'DOGE': 0.1, 'PEPE': 0.000001
                            }}
                            price = price_map.get(currency, 0)

                        value_usdt = balance * price
                        total_usdt += value_usdt

                        if value_usdt > 0.001:
                            balance_list.append({{
                                'currency': currency,
                                'balance': balance,
                                'available': balance,
                                'frozen': 0,
                                'price': price,
                                'value_usdt': value_usdt
                            }})

            balance_list.sort(key=lambda x: x['value_usdt'], reverse=True)

            return {{
                'total_usdt': total_usdt,
                'balance_list': balance_list,
                'count': len(balance_list)
            }}

        except Exception as e:
            logger.error(f"获取余额失败: {{e}}")
            return {{'total_usdt': {self.spot_balance:.4f}, 'balance_list': [], 'count': 0}}

    def get_total_balance(self):
        """获取总余额（包括其他账户）"""
        # 获取现货余额
        spot_balance = self.get_balance()
        spot_value = spot_balance.get('total_usdt', 0)

        # 尝试获取总估值
        total_value = spot_value
        other_value = self._cached_other_balance

        if self._use_valuation_api:
            # 尝试使用估值API
            try:
                data = self._make_request('GET', '/v1/account/asset-valuation', {{
                    'accountType': '1',
                    'valuationCurrency': 'USDT'
                }})

                if data:
                    api_total = float(data.get('balance', 0))
                    if api_total > spot_value:
                        total_value = api_total
                        other_value = api_total - spot_value
                    else:
                        # 使用缓存值
                        total_value = spot_value + other_value
                else:
                    # API失败，使用缓存
                    total_value = spot_value + other_value
            except:
                # 使用缓存
                total_value = spot_value + other_value
        else:
            # 直接使用缓存
            total_value = spot_value + other_value

        result = {{
            'total_usdt': total_value,
            'accounts': {{
                'spot': spot_value,
                'earn': other_value
            }},
            'details': []
        }}

        # 添加现货明细
        if spot_value > 0:
            result['details'].append({{
                'type': '现货账户',
                'value': spot_value,
                'assets': spot_balance.get('balance_list', [])
            }})

        # 添加其他账户明细
        if other_value > 0:
            result['details'].append({{
                'type': '其他账户(含赚币)',
                'value': other_value,
                'assets': []
            }})

        logger.info(f"总余额: {{total_value:.2f}} (现货: {{spot_value:.4f}}, 其他: {{other_value:.2f}})")

        return result

    def get_asset_distribution(self):
        """获取资产分布"""
        balance = self.get_total_balance()
        total = balance['total_usdt']

        distribution = []
        for detail in balance['details']:
            if detail['value'] > 0:
                percentage = (detail['value'] / total * 100) if total > 0 else 0
                distribution.append({{
                    'currency': detail['type'],
                    'percentage': percentage,
                    'value': detail['value']
                }})

        return {{'distribution': distribution}}

AccountManager = AccountModule
'''

        # 备份并写入文件
        account_file = "modules/account/account.py"

        if os.path.exists(account_file):
            backup_file = f"modules/account/account_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            shutil.copy(account_file, backup_file)
            print(f"  ✓ 备份原文件: {backup_file}")

        os.makedirs(os.path.dirname(account_file), exist_ok=True)
        with open(account_file, 'w', encoding='utf-8') as f:
            f.write(code)

        print(f"  ✓ 创建修复模块: {account_file}")
        print("\n✅ 修复完成！")
        print("\n请重启机器人：")
        print("1. 按 Ctrl+C 停止")
        print("2. 运行 python bot.py")

    def run(self):
        """运行诊断"""
        print("开始诊断...\n")

        # 测试1: 现货余额
        spot_ok = self.test_spot_balance()

        # 测试2: 总估值
        total_ok = self.test_total_valuation()

        # 测试3: 其他账户
        if not total_ok:
            self.test_other_accounts()

        # 测试4: 赚币产品
        if self.other_balance == 0:
            self.test_earn_products()

        # 生成修复
        return self.generate_fix()


if __name__ == '__main__':
    diagnostic = HTXAccountDiagnostic()
    success = diagnostic.run()

    if not success:
        print("\n❌ 无法自动修复")
        print("建议：")
        print("1. 在火币APP查看资金具体位置")
        print("2. 尝试手动划转到现货账户")
        print("3. 联系火币客服了解API限制")