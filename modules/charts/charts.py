"""图表生成模块 - 完整版"""
import os
import time
from datetime import datetime, timedelta
from loguru import logger

class ChartsModule:
    """图表生成模块"""

    def __init__(self, access_key=None, secret_key=None, rest_url=None):
        """初始化"""
        self.access_key = access_key
        self.secret_key = secret_key
        self.rest_url = rest_url
        self.charts_dir = "data/charts"

        # 创建图表目录
        os.makedirs(self.charts_dir, exist_ok=True)

        logger.info("图表模块初始化")

    def cleanup_old_charts(self, max_age_days=1):
        """清理旧图表文件"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60

            cleaned_count = 0

            # 检查图表目录
            if os.path.exists(self.charts_dir):
                for filename in os.listdir(self.charts_dir):
                    file_path = os.path.join(self.charts_dir, filename)

                    # 跳过目录
                    if os.path.isdir(file_path):
                        continue

                    # 检查文件年龄
                    try:
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.debug(f"删除旧图表: {filename}")
                    except Exception as e:
                        logger.error(f"清理文件失败 {filename}: {e}")

            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个旧图表文件")

        except Exception as e:
            logger.error(f"清理图表失败: {e}")

    def generate_kline_chart(self, klines, symbol, period, indicators=None):
        """生成K线图"""
        try:
            # 模拟生成图表
            chart_file = os.path.join(self.charts_dir, f"{symbol}_kline_{int(time.time())}.png")

            # 这里应该生成实际的图表
            # 现在只是创建一个空文件作为示例
            with open(chart_file, 'w') as f:
                f.write("K线图")

            logger.info(f"生成K线图: {symbol}")
            return chart_file

        except Exception as e:
            logger.error(f"生成K线图失败: {e}")
            return None

    def generate_asset_pie_chart(self, distribution):
        """生成资产饼图"""
        try:
            chart_file = os.path.join(self.charts_dir, f"asset_pie_{int(time.time())}.png")

            # 模拟生成
            with open(chart_file, 'w') as f:
                f.write("资产分布图")

            logger.info("生成资产分布图")
            return chart_file

        except Exception as e:
            logger.error(f"生成资产饼图失败: {e}")
            return None

    def generate_market_overview(self, tickers):
        """生成市场概览"""
        try:
            chart_file = os.path.join(self.charts_dir, f"market_{int(time.time())}.png")

            # 模拟生成
            with open(chart_file, 'w') as f:
                f.write("市场概览")

            logger.info("生成市场概览图")
            return chart_file

        except Exception as e:
            logger.error(f"生成市场概览失败: {e}")
            return None

    def generate_grid_visualization(self, grid_config, current_price):
        """生成网格可视化"""
        try:
            chart_file = os.path.join(self.charts_dir, f"grid_{int(time.time())}.png")

            # 模拟生成
            with open(chart_file, 'w') as f:
                f.write("网格图")

            logger.info("生成网格图")
            return chart_file

        except Exception as e:
            logger.error(f"生成网格图失败: {e}")
            return None

    def get_chart_stats(self):
        """获取图表统计"""
        try:
            if os.path.exists(self.charts_dir):
                files = os.listdir(self.charts_dir)
                return {
                    'total': len(files),
                    'directory': self.charts_dir
                }
            return {'total': 0, 'directory': self.charts_dir}
        except Exception as e:
            logger.error(f"获取图表统计失败: {e}")
            return {'total': 0, 'directory': self.charts_dir}

# 兼容别名
ChartGenerator = ChartsModule
