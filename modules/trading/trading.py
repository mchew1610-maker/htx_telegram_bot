"""交易管理模块 - 完整实现"""
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from loguru import logger
from utils.htx_api_base import HTXApiBase

class TradingModule(HTXApiBase):
    """交易管理模块 - 真实交易实现"""

    def __init__(self, access_key, secret_key, rest_url="https://api.huobi.pro"):
        """初始化"""
        super().__init__(access_key, secret_key, rest_url)
        self.account_id = None
        self.symbol_info = {}
        self._ensure_account_id()
        self._load_symbol_info()
        logger.info("交易模块初始化完成")

    def _ensure_account_id(self):
        """确保获取到账户ID"""
        if not self.account_id:
            accounts = self.get_accounts()
            for acc in accounts:
                if acc.get('type') == 'spot' and acc.get('state') == 'working':
                    self.account_id = acc['id']
                    logger.info(f"获取到现货账户ID: {self.account_id}")
                    break

    def _load_symbol_info(self):
        """加载交易对信息（精度等）"""
        try:
            symbols = self.get_symbols()
            for symbol in symbols:
                self.symbol_info[symbol['symbol']] = {
                    'price_precision': symbol.get('price-precision', 2),
                    'amount_precision': symbol.get('amount-precision', 2),
                    'value_precision': symbol.get('value-precision', 8),
                    'min_order_amt': float(symbol.get('min-order-amt', 0.0001)),
                    'min_order_value': float(symbol.get('min-order-value', 1)),
                    'state': symbol.get('state', 'offline')
                }
            logger.info(f"加载了 {len(self.symbol_info)} 个交易对信息")
        except Exception as e:
            logger.error(f"加载交易对信息失败: {e}")

    def get_symbol_info(self, symbol):
        """获取交易对信息"""
        if symbol.lower() in self.symbol_info:
            return self.symbol_info[symbol.lower()]

        # 如果没有缓存，重新加载
        self._load_symbol_info()
        return self.symbol_info.get(symbol.lower())

    def _format_amount(self, symbol, amount):
        """格式化数量（根据交易对精度）"""
        info = self.get_symbol_info(symbol)
        if info:
            precision = info['amount_precision']
            return float(Decimal(str(amount)).quantize(
                Decimal(10) ** -precision,
                rounding=ROUND_DOWN
            ))
        return amount

    def _format_price(self, symbol, price):
        """格式化价格（根据交易对精度）"""
        info = self.get_symbol_info(symbol)
        if info:
            precision = info['price_precision']
            return float(Decimal(str(price)).quantize(
                Decimal(10) ** -precision,
                rounding=ROUND_DOWN
            ))
        return price

    def buy_limit(self, symbol, price, amount):
        """
        限价买入

        Args:
            symbol: 交易对
            price: 价格
            amount: 数量

        Returns:
            订单结果
        """
        try:
            if not self.account_id:
                self._ensure_account_id()

            # 格式化参数
            formatted_price = self._format_price(symbol, price)
            formatted_amount = self._format_amount(symbol, amount)

            # 检查最小订单
            info = self.get_symbol_info(symbol)
            if info:
                if formatted_amount < info['min_order_amt']:
                    return {
                        'success': False,
                        'error': f"数量低于最小值: {info['min_order_amt']}"
                    }

                order_value = formatted_price * formatted_amount
                if order_value < info['min_order_value']:
                    return {
                        'success': False,
                        'error': f"订单价值低于最小值: {info['min_order_value']} USDT"
                    }

            # 下单
            order_id = self.place_order(
                self.account_id,
                symbol,
                'buy-limit',
                formatted_amount,
                formatted_price
            )

            if order_id:
                logger.info(f"限价买单创建成功: {symbol} @ {formatted_price} x {formatted_amount}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': symbol,
                    'price': formatted_price,
                    'amount': formatted_amount,
                    'message': '买单创建成功'
                }
            else:
                return {
                    'success': False,
                    'error': '下单失败'
                }

        except Exception as e:
            logger.error(f"限价买入失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def sell_limit(self, symbol, price, amount):
        """
        限价卖出

        Args:
            symbol: 交易对
            price: 价格
            amount: 数量

        Returns:
            订单结果
        """
        try:
            if not self.account_id:
                self._ensure_account_id()

            # 格式化参数
            formatted_price = self._format_price(symbol, price)
            formatted_amount = self._format_amount(symbol, amount)

            # 检查最小订单
            info = self.get_symbol_info(symbol)
            if info:
                if formatted_amount < info['min_order_amt']:
                    return {
                        'success': False,
                        'error': f"数量低于最小值: {info['min_order_amt']}"
                    }

            # 下单
            order_id = self.place_order(
                self.account_id,
                symbol,
                'sell-limit',
                formatted_amount,
                formatted_price
            )

            if order_id:
                logger.info(f"限价卖单创建成功: {symbol} @ {formatted_price} x {formatted_amount}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': symbol,
                    'price': formatted_price,
                    'amount': formatted_amount,
                    'message': '卖单创建成功'
                }
            else:
                return {
                    'success': False,
                    'error': '下单失败'
                }

        except Exception as e:
            logger.error(f"限价卖出失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def buy_market(self, symbol, amount):
        """
        市价买入（按金额）

        Args:
            symbol: 交易对
            amount: 买入金额（USDT）

        Returns:
            订单结果
        """
        try:
            if not self.account_id:
                self._ensure_account_id()

            # 市价买入使用金额
            order_id = self.place_order(
                self.account_id,
                symbol,
                'buy-market',
                amount  # 市价买入传入的是金额
            )

            if order_id:
                logger.info(f"市价买单创建成功: {symbol} 金额: {amount} USDT")
                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': symbol,
                    'amount': amount,
                    'message': '市价买单创建成功'
                }
            else:
                return {
                    'success': False,
                    'error': '下单失败'
                }

        except Exception as e:
            logger.error(f"市价买入失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def sell_market(self, symbol, amount):
        """
        市价卖出（按数量）

        Args:
            symbol: 交易对
            amount: 卖出数量

        Returns:
            订单结果
        """
        try:
            if not self.account_id:
                self._ensure_account_id()

            # 格式化数量
            formatted_amount = self._format_amount(symbol, amount)

            # 市价卖出使用数量
            order_id = self.place_order(
                self.account_id,
                symbol,
                'sell-market',
                formatted_amount  # 市价卖出传入的是数量
            )

            if order_id:
                logger.info(f"市价卖单创建成功: {symbol} 数量: {formatted_amount}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': symbol,
                    'amount': formatted_amount,
                    'message': '市价卖单创建成功'
                }
            else:
                return {
                    'success': False,
                    'error': '下单失败'
                }

        except Exception as e:
            logger.error(f"市价卖出失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_open_orders(self, symbol=None):
        """
        获取未成交订单

        Args:
            symbol: 交易对（可选）

        Returns:
            订单列表
        """
        try:
            if not self.account_id:
                self._ensure_account_id()

            orders = super().get_open_orders(self.account_id, symbol)

            # 格式化订单数据
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'order_id': order.get('id'),
                    'symbol': order.get('symbol'),
                    'type': order.get('type'),  # buy-limit, sell-limit等
                    'price': float(order.get('price', 0)),
                    'amount': float(order.get('amount', 0)),
                    'filled_amount': float(order.get('filled-amount', 0)),
                    'filled_cash': float(order.get('filled-cash-amount', 0)),
                    'filled_fees': float(order.get('filled-fees', 0)),
                    'state': order.get('state'),
                    'created_at': datetime.fromtimestamp(order.get('created-at', 0) / 1000).isoformat()
                })

            return formatted_orders

        except Exception as e:
            logger.error(f"获取未成交订单失败: {e}")
            return []

    def cancel_all_orders(self, symbol=None):
        """
        撤销所有订单

        Args:
            symbol: 交易对（可选）

        Returns:
            撤销结果
        """
        try:
            orders = self.get_open_orders(symbol)

            if not orders:
                return {
                    'success': True,
                    'message': '没有未成交订单',
                    'cancelled_count': 0
                }

            cancelled_count = 0
            failed_count = 0

            for order in orders:
                if self.cancel_order(order['order_id']):
                    cancelled_count += 1
                else:
                    failed_count += 1

            return {
                'success': True,
                'message': f'撤销了 {cancelled_count} 个订单',
                'cancelled_count': cancelled_count,
                'failed_count': failed_count
            }

        except Exception as e:
            logger.error(f"撤销所有订单失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'cancelled_count': 0
            }

    def get_order_history(self, symbol=None, size=50):
        """
        获取订单历史

        Args:
            symbol: 交易对（可选）
            size: 数量

        Returns:
            订单列表
        """
        try:
            path = '/v1/order/orders'
            params = {
                'states': 'filled,partial-canceled,canceled',
                'size': size
            }

            if symbol:
                params['symbol'] = symbol.lower()

            result = self.request('GET', path, params)

            if result and result.get('status') == 'ok':
                orders = result.get('data', [])

                # 格式化订单数据
                formatted_orders = []
                for order in orders:
                    formatted_orders.append({
                        'order_id': order.get('id'),
                        'symbol': order.get('symbol'),
                        'type': order.get('type'),
                        'price': float(order.get('price', 0)),
                        'amount': float(order.get('amount', 0)),
                        'filled_amount': float(order.get('filled-amount', 0)),
                        'filled_cash': float(order.get('filled-cash-amount', 0)),
                        'filled_fees': float(order.get('filled-fees', 0)),
                        'state': order.get('state'),
                        'created_at': datetime.fromtimestamp(order.get('created-at', 0) / 1000).isoformat(),
                        'finished_at': datetime.fromtimestamp(order.get('finished-at', 0) / 1000).isoformat() if order.get('finished-at') else None
                    })

                return formatted_orders

            return []

        except Exception as e:
            logger.error(f"获取订单历史失败: {e}")
            return []

    def get_order_detail(self, order_id):
        """
        获取订单详情

        Args:
            order_id: 订单ID

        Returns:
            订单详情
        """
        try:
            order = super().get_order_detail(order_id)

            if order:
                return {
                    'order_id': order.get('id'),
                    'symbol': order.get('symbol'),
                    'account_id': order.get('account-id'),
                    'type': order.get('type'),
                    'price': float(order.get('price', 0)),
                    'amount': float(order.get('amount', 0)),
                    'filled_amount': float(order.get('filled-amount', 0)),
                    'filled_cash': float(order.get('filled-cash-amount', 0)),
                    'filled_fees': float(order.get('filled-fees', 0)),
                    'state': order.get('state'),
                    'source': order.get('source'),
                    'created_at': datetime.fromtimestamp(order.get('created-at', 0) / 1000).isoformat(),
                    'finished_at': datetime.fromtimestamp(order.get('finished-at', 0) / 1000).isoformat() if order.get('finished-at') else None
                }

            return None

        except Exception as e:
            logger.error(f"获取订单详情失败: {e}")
            return None

    def get_trade_fee(self, symbols):
        """
        获取交易手续费率

        Args:
            symbols: 交易对列表

        Returns:
            手续费信息
        """
        try:
            path = '/v2/reference/transact-fee-rate'
            params = {
                'symbols': ','.join(symbols) if isinstance(symbols, list) else symbols
            }

            result = self.request('GET', path, params)

            if result and result.get('code') == 200:
                return result.get('data', [])

            return []

        except Exception as e:
            logger.error(f"获取手续费率失败: {e}")
            return []

# 兼容别名
TradingManager = TradingModule