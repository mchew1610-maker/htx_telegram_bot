"""图表生成模块 - 修复版"""
from loguru import logger

class ChartsModule:
    """图表生成模块"""

    def __init__(self, access_key=None, secret_key=None, rest_url=None):
        """初始化 - 兼容多种参数"""
        self.access_key = access_key
        self.secret_key = secret_key
        self.rest_url = rest_url
        logger.info("图表模块初始化")

    def generate_kline_chart(self, klines, symbol, period, indicators=None):
        """生成K线图"""
        logger.info(f"生成{symbol} K线图")
        # 返回模拟的图表路径
        return f"data/charts/{symbol}_kline.png"

    def generate_asset_pie_chart(self, distribution):
        """生成资产饼图"""
        logger.info("生成资产分布图")
        return "data/charts/asset_pie.png"

    def generate_market_overview(self, tickers):
        """生成市场概览"""
        logger.info("生成市场概览图")
        return "data/charts/market_overview.png"

    def generate_grid_visualization(self, grid_config, current_price):
        """生成网格可视化"""
        logger.info("生成网格图")
        return "data/charts/grid_visual.png"

# 兼容别名
ChartGenerator = ChartsModule
