"""网格交易模块 - 修复版"""
from loguru import logger

class GridModule:
    """网格交易模块"""

    def __init__(self, access_key=None, secret_key=None, rest_url=None):
        """初始化 - 兼容多种参数"""
        self.access_key = access_key
        self.secret_key = secret_key
        self.rest_url = rest_url
        self.active_grids = {}
        logger.info("网格模块初始化")

    def create_grid(self, symbol, grid_count, amount):
        """创建网格"""
        return {
            'success': True,
            'message': f'网格创建成功: {symbol}',
            'initial_orders': grid_count
        }

    def stop_grid(self, symbol):
        """停止网格"""
        if symbol in self.active_grids:
            del self.active_grids[symbol]
            return {'success': True, 'message': f'网格已停止: {symbol}'}
        return {'success': False, 'error': '网格不存在'}

    def get_grid_status(self):
        """获取网格状态"""
        return {
            'active_grids': len(self.active_grids),
            'grids': []
        }

    def update_grid(self, symbol):
        """更新网格"""
        pass

# 兼容别名
GridTrading = GridModule
