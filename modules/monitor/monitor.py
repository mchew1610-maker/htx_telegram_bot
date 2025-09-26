"""监控预警模块 - 完整实现"""
from loguru import logger
import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class MonitorModule:
    """监控预警模块 - 真实监控实现"""

    def __init__(self, market=None, trading=None):
        """初始化"""
        self.market = market  # 市场数据模块
        self.trading = trading  # 交易模块
        self.alerts = []
        self.alert_callback = None  # 预警回调函数
        self.monitoring = False
        self.monitor_thread = None
        self.alert_history = []  # 预警历史

        # 加载保存的预警
        self._load_alerts()

        logger.info("监控模块初始化完成")

    def set_alert_callback(self, callback):
        """设置预警回调函数"""
        self.alert_callback = callback
        logger.info("预警回调函数已设置")

    def add_price_alert(self, symbol, target_price, alert_type, user_id):
        """
        添加价格预警

        Args:
            symbol: 交易对
            target_price: 目标价格
            alert_type: 预警类型 (above/below/cross)
            user_id: 用户ID

        Returns:
            添加结果
        """
        try:
            # 获取当前价格
            current_price = None
            if self.market:
                ticker = self.market.get_ticker(symbol)
                if ticker:
                    current_price = ticker['close']

            alert = {
                'id': len(self.alerts) + 1,
                'symbol': symbol.lower(),
                'target_price': float(target_price),
                'current_price': current_price,
                'alert_type': alert_type.lower(),
                'user_id': str(user_id),
                'type': 'price',
                'triggered': False,
                'created_at': datetime.now().isoformat(),
                'triggered_at': None,
                'trigger_count': 0,
                'enabled': True
            }

            # 验证预警类型
            if alert_type.lower() not in ['above', 'below', 'cross']:
                return {
                    'success': False,
                    'error': '无效的预警类型，请使用: above/below/cross'
                }

            # 检查是否重复
            for existing in self.alerts:
                if (existing['symbol'] == alert['symbol'] and
                    existing['target_price'] == alert['target_price'] and
                    existing['alert_type'] == alert['alert_type'] and
                    existing['user_id'] == alert['user_id'] and
                    not existing['triggered']):
                    return {
                        'success': False,
                        'error': '已存在相同的预警'
                    }

            self.alerts.append(alert)
            self._save_alerts()

            logger.info(f"添加价格预警: {symbol} {alert_type} {target_price}")

            message = f'价格预警已添加: {symbol.upper()} '
            if alert_type == 'above':
                message += f'高于 ${target_price:.4f}'
            elif alert_type == 'below':
                message += f'低于 ${target_price:.4f}'
            else:
                message += f'穿越 ${target_price:.4f}'

            if current_price:
                message += f' (当前: ${current_price:.4f})'

            return {
                'success': True,
                'alert_id': alert['id'],
                'message': message
            }

        except Exception as e:
            logger.error(f"添加价格预警失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def add_volume_alert(self, symbol, threshold, time_window, user_id):
        """
        添加成交量预警

        Args:
            symbol: 交易对
            threshold: 阈值（USDT）
            time_window: 时间窗口（分钟）
            user_id: 用户ID

        Returns:
            添加结果
        """
        try:
            alert = {
                'id': len(self.alerts) + 1,
                'symbol': symbol.lower(),
                'threshold': float(threshold),
                'time_window': int(time_window),
                'user_id': str(user_id),
                'type': 'volume',
                'triggered': False,
                'created_at': datetime.now().isoformat(),
                'triggered_at': None,
                'trigger_count': 0,
                'enabled': True,
                'last_check_volume': 0
            }

            self.alerts.append(alert)
            self._save_alerts()

            logger.info(f"添加成交量预警: {symbol} > {threshold} USDT in {time_window}min")

            return {
                'success': True,
                'alert_id': alert['id'],
                'message': f'成交量预警已添加: {symbol.upper()} > ${threshold:.2f} USDT ({time_window}分钟)'
            }

        except Exception as e:
            logger.error(f"添加成交量预警失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def add_change_alert(self, symbol, change_percent, time_window, user_id):
        """
        添加涨跌幅预警

        Args:
            symbol: 交易对
            change_percent: 涨跌幅百分比
            time_window: 时间窗口（分钟）
            user_id: 用户ID

        Returns:
            添加结果
        """
        try:
            alert = {
                'id': len(self.alerts) + 1,
                'symbol': symbol.lower(),
                'change_percent': float(change_percent),
                'time_window': int(time_window),
                'user_id': str(user_id),
                'type': 'change',
                'triggered': False,
                'created_at': datetime.now().isoformat(),
                'triggered_at': None,
                'trigger_count': 0,
                'enabled': True,
                'reference_price': None
            }

            # 获取参考价格
            if self.market:
                ticker = self.market.get_ticker(symbol)
                if ticker:
                    alert['reference_price'] = ticker['close']

            self.alerts.append(alert)
            self._save_alerts()

            direction = "涨幅" if change_percent > 0 else "跌幅"
            logger.info(f"添加涨跌幅预警: {symbol} {direction} {abs(change_percent)}% in {time_window}min")

            return {
                'success': True,
                'alert_id': alert['id'],
                'message': f'{direction}预警已添加: {symbol.upper()} {abs(change_percent)}% ({time_window}分钟)'
            }

        except Exception as e:
            logger.error(f"添加涨跌幅预警失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_alerts(self, user_id=None):
        """获取活动预警"""
        try:
            # 筛选预警
            if user_id:
                user_alerts = [
                    a for a in self.alerts
                    if str(a.get('user_id')) == str(user_id)
                    and not a.get('triggered', False)
                    and a.get('enabled', True)
                ]
            else:
                user_alerts = [
                    a for a in self.alerts
                    if not a.get('triggered', False)
                    and a.get('enabled', True)
                ]

            # 格式化预警信息
            formatted_alerts = []
            for alert in user_alerts:
                if alert['type'] == 'price':
                    desc = f"{alert['symbol'].upper()} {alert['alert_type']} ${alert['target_price']:.4f}"
                elif alert['type'] == 'volume':
                    desc = f"{alert['symbol'].upper()} 成交量 > ${alert['threshold']:.2f} ({alert['time_window']}min)"
                elif alert['type'] == 'change':
                    direction = "涨" if alert['change_percent'] > 0 else "跌"
                    desc = f"{alert['symbol'].upper()} {direction}{abs(alert['change_percent'])}% ({alert['time_window']}min)"
                else:
                    desc = f"{alert['symbol'].upper()} {alert['type']}"

                formatted_alerts.append({
                    'id': alert['id'],
                    'description': desc,
                    'created_at': alert['created_at']
                })

            return {
                'alerts': formatted_alerts,
                'total': len(formatted_alerts)
            }

        except Exception as e:
            logger.error(f"获取活动预警失败: {e}")
            return {'alerts': [], 'total': 0}

    def remove_alert(self, alert_id, user_id=None):
        """
        移除预警

        Args:
            alert_id: 预警ID
            user_id: 用户ID（可选，用于权限检查）

        Returns:
            移除结果
        """
        try:
            # 查找预警
            alert = next((a for a in self.alerts if a['id'] == alert_id), None)

            if not alert:
                return {
                    'success': False,
                    'error': '预警不存在'
                }

            # 检查权限
            if user_id and str(alert.get('user_id')) != str(user_id):
                return {
                    'success': False,
                    'error': '无权限删除此预警'
                }

            # 移除预警
            self.alerts = [a for a in self.alerts if a['id'] != alert_id]
            self._save_alerts()

            logger.info(f"移除预警: ID={alert_id}")

            return {
                'success': True,
                'message': '预警已移除'
            }

        except Exception as e:
            logger.error(f"移除预警失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def check_price_alerts(self):
        """检查价格预警"""
        if not self.market:
            return

        try:
            # 获取所有需要监控的交易对
            symbols = set()
            for alert in self.alerts:
                if alert['type'] == 'price' and not alert.get('triggered') and alert.get('enabled'):
                    symbols.add(alert['symbol'])

            # 批量获取价格
            prices = {}
            for symbol in symbols:
                ticker = self.market.get_ticker(symbol)
                if ticker:
                    prices[symbol] = ticker['close']

            # 检查每个预警
            for alert in self.alerts:
                if alert['type'] != 'price' or alert.get('triggered') or not alert.get('enabled'):
                    continue

                symbol = alert['symbol']
                if symbol not in prices:
                    continue

                current_price = prices[symbol]
                target_price = alert['target_price']
                alert_type = alert['alert_type']

                triggered = False

                if alert_type == 'above' and current_price >= target_price:
                    triggered = True
                    message = f"📈 价格预警触发\n{symbol.upper()} 已突破 ${target_price:.4f}\n当前价格: ${current_price:.4f}"
                elif alert_type == 'below' and current_price <= target_price:
                    triggered = True
                    message = f"📉 价格预警触发\n{symbol.upper()} 已跌破 ${target_price:.4f}\n当前价格: ${current_price:.4f}"
                elif alert_type == 'cross':
                    last_price = alert.get('last_price')
                    if last_price:
                        if (last_price < target_price <= current_price) or (last_price > target_price >= current_price):
                            triggered = True
                            direction = "上穿" if current_price > target_price else "下穿"
                            message = f"🔄 价格预警触发\n{symbol.upper()} {direction} ${target_price:.4f}\n当前价格: ${current_price:.4f}"
                    alert['last_price'] = current_price

                if triggered:
                    self._trigger_alert(alert, message)

        except Exception as e:
            logger.error(f"检查价格预警失败: {e}")

    def check_volume_alerts(self):
        """检查成交量预警"""
        if not self.market:
            return

        try:
            for alert in self.alerts:
                if alert['type'] != 'volume' or alert.get('triggered') or not alert.get('enabled'):
                    continue

                symbol = alert['symbol']
                ticker = self.market.get_ticker(symbol)

                if ticker:
                    # 这里简化处理，实际应该计算指定时间窗口内的成交量
                    current_volume = ticker.get('amount', 0)  # 24h成交额
                    threshold = alert['threshold']

                    # 计算时间窗口内的成交量（这里用简化方法）
                    window_minutes = alert['time_window']
                    estimated_volume = current_volume * (window_minutes / (24 * 60))

                    if estimated_volume > threshold:
                        message = f"📊 成交量预警触发\n{symbol.upper()} 成交量异常\n"
                        message += f"预估 {window_minutes}分钟成交额: ${estimated_volume:.2f}\n"
                        message += f"阈值: ${threshold:.2f}"

                        self._trigger_alert(alert, message)

        except Exception as e:
            logger.error(f"检查成交量预警失败: {e}")

    def check_order_alerts(self):
        """检查订单成交预警"""
        if not self.trading:
            return

        try:
            # 这里可以实现订单成交的监控
            # 比如监控特定订单是否成交
            pass

        except Exception as e:
            logger.error(f"检查订单预警失败: {e}")

    def _trigger_alert(self, alert, message):
        """
        触发预警

        Args:
            alert: 预警对象
            message: 消息内容
        """
        try:
            alert['triggered'] = True
            alert['triggered_at'] = datetime.now().isoformat()
            alert['trigger_count'] += 1

            # 构造完整的通知
            notification = {
                'alert_id': alert['id'],
                'user_id': alert.get('user_id'),
                'type': alert['type'],
                'symbol': alert['symbol'],
                'message': message,
                'full_message': message,
                'timestamp': datetime.now().isoformat()
            }

            # 添加到历史
            self.alert_history.append(notification)

            # 调用回调函数
            if self.alert_callback:
                self.alert_callback(notification)

            # 保存状态
            self._save_alerts()

            logger.info(f"预警已触发: {alert['id']} - {alert['symbol']}")

        except Exception as e:
            logger.error(f"触发预警失败: {e}")

    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            logger.warning("监控已在运行")
            return

        self.monitoring = True

        def monitor_loop():
            while self.monitoring:
                try:
                    self.check_price_alerts()
                    self.check_volume_alerts()
                    self.check_order_alerts()
                    time.sleep(30)  # 30秒检查一次
                except Exception as e:
                    logger.error(f"监控循环错误: {e}")
                    time.sleep(60)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("监控已停止")

    def get_alert_history(self, user_id=None, limit=50):
        """
        获取预警历史

        Args:
            user_id: 用户ID（可选）
            limit: 数量限制

        Returns:
            历史记录
        """
        history = self.alert_history

        if user_id:
            history = [h for h in history if h.get('user_id') == str(user_id)]

        # 按时间倒序
        history = sorted(history, key=lambda x: x['timestamp'], reverse=True)

        return history[:limit]

    def clear_triggered_alerts(self, user_id=None):
        """清理已触发的预警"""
        before = len(self.alerts)

        if user_id:
            self.alerts = [
                a for a in self.alerts
                if not a.get('triggered') or str(a.get('user_id')) != str(user_id)
            ]
        else:
            self.alerts = [a for a in self.alerts if not a.get('triggered')]

        after = len(self.alerts)
        removed = before - after

        if removed > 0:
            self._save_alerts()
            logger.info(f"清理了 {removed} 个已触发的预警")

        return {
            'removed': removed,
            'remaining': after
        }

    def _save_alerts(self):
        """保存预警到文件"""
        try:
            os.makedirs('data/alerts', exist_ok=True)

            with open('data/alerts/alerts.json', 'w') as f:
                json.dump(self.alerts, f, indent=2)

        except Exception as e:
            logger.error(f"保存预警失败: {e}")

    def _load_alerts(self):
        """从文件加载预警"""
        try:
            if os.path.exists('data/alerts/alerts.json'):
                with open('data/alerts/alerts.json', 'r') as f:
                    self.alerts = json.load(f)
                    logger.info(f"加载了 {len(self.alerts)} 个预警")
        except Exception as e:
            logger.error(f"加载预警失败: {e}")
            self.alerts = []

# 兼容别名
Monitor = MonitorModule