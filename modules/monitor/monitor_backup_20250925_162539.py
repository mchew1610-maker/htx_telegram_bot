"""监控预警模块 - 修复版"""
from loguru import logger

class MonitorModule:
    """监控预警模块"""

    def __init__(self, bot=None, access_key=None, secret_key=None):
        """初始化 - 兼容多种参数"""
        self.bot = bot
        self.access_key = access_key
        self.secret_key = secret_key
        self.alerts = []
        logger.info("监控模块初始化")

    def add_price_alert(self, symbol, target_price, alert_type, user_id):
        """添加价格预警"""
        alert = {
            'id': len(self.alerts) + 1,
            'symbol': symbol,
            'target_price': target_price,
            'alert_type': alert_type,
            'user_id': user_id,
            'type': 'price'
        }
        self.alerts.append(alert)
        return {
            'success': True,
            'message': f'价格预警已添加: {symbol} {alert_type} {target_price}'
        }

    def add_volume_alert(self, symbol, threshold, time_window, user_id):
        """添加成交量预警"""
        alert = {
            'id': len(self.alerts) + 1,
            'symbol': symbol,
            'threshold': threshold,
            'time_window': time_window,
            'user_id': user_id,
            'type': 'volume'
        }
        self.alerts.append(alert)
        return {
            'success': True,
            'message': f'成交量预警已添加: {symbol}'
        }

    def get_active_alerts(self, user_id=None):
        """获取活动预警"""
        if user_id:
            user_alerts = [a for a in self.alerts if str(a.get('user_id')) == str(user_id)]
        else:
            user_alerts = self.alerts

        return {
            'alerts': user_alerts,
            'total': len(user_alerts)
        }

    def remove_alert(self, alert_id):
        """移除预警"""
        self.alerts = [a for a in self.alerts if a['id'] != alert_id]

    def check_price_alerts(self):
        """检查价格预警"""
        pass

    def check_volume_alerts(self):
        """检查成交量预警"""
        pass

    def check_order_alerts(self):
        """检查订单预警"""
        pass

# 兼容别名
Monitor = MonitorModule
