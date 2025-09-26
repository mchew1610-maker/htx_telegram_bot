"""图表生成模块 - 完整实现"""
import os
import time
from datetime import datetime, timedelta
from loguru import logger
import json

# 尝试导入图表库
try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非GUI后端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import rcParams
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib未安装，图表功能将受限")

class ChartsModule:
    """图表生成模块 - 真实图表实现"""

    def __init__(self, access_key=None, secret_key=None, rest_url=None):
        """初始化"""
        self.access_key = access_key
        self.secret_key = secret_key
        self.rest_url = rest_url
        self.charts_dir = "data/charts"

        # 创建图表目录
        os.makedirs(self.charts_dir, exist_ok=True)

        # 设置matplotlib中文支持
        if HAS_MATPLOTLIB:
            try:
                # 尝试设置中文字体
                rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
                rcParams['axes.unicode_minus'] = False
            except:
                pass

        logger.info("图表模块初始化完成")

    def cleanup_old_charts(self, max_age_days=1):
        """清理旧图表文件"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            cleaned_count = 0

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
        """
        生成K线图

        Args:
            klines: K线数据列表
            symbol: 交易对
            period: 周期
            indicators: 指标（如MA）

        Returns:
            图表文件路径
        """
        try:
            if not HAS_MATPLOTLIB:
                return self._generate_placeholder_chart("K线图")

            if not klines:
                logger.warning("K线数据为空")
                return None

            # 准备数据
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []

            for kline in klines:
                if isinstance(kline, dict):
                    dates.append(datetime.fromtimestamp(kline.get('id', 0)))
                    opens.append(float(kline.get('open', 0)))
                    highs.append(float(kline.get('high', 0)))
                    lows.append(float(kline.get('low', 0)))
                    closes.append(float(kline.get('close', 0)))
                    volumes.append(float(kline.get('volume', 0)))

            if not dates:
                return None

            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})

            # K线图
            ax1.set_title(f'{symbol.upper()} - {period}', fontsize=14, fontweight='bold')

            # 绘制蜡烛图
            for i in range(len(dates)):
                color = 'green' if closes[i] >= opens[i] else 'red'
                # 绘制影线
                ax1.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=1)
                # 绘制实体
                height = abs(closes[i] - opens[i])
                bottom = min(closes[i], opens[i])
                ax1.bar(dates[i], height, bottom=bottom, color=color, width=0.0005, alpha=0.8)

            # 添加移动平均线
            if indicators and 'MA' in indicators:
                ma_periods = indicators.get('MA', [5, 10, 20])
                colors = ['blue', 'orange', 'purple']

                for idx, period_ma in enumerate(ma_periods):
                    if len(closes) >= period_ma:
                        ma_values = self._calculate_ma(closes, period_ma)
                        if ma_values:
                            ax1.plot(dates[-len(ma_values):], ma_values,
                                   label=f'MA{period_ma}', color=colors[idx % len(colors)], linewidth=1.5)

            ax1.set_ylabel('Price', fontsize=10)
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')

            # 成交量图
            ax2.bar(dates, volumes, color=['green' if closes[i] >= opens[i] else 'red' for i in range(len(closes))], alpha=0.5)
            ax2.set_ylabel('Volume', fontsize=10)
            ax2.set_xlabel('Time', fontsize=10)
            ax2.grid(True, alpha=0.3)

            # 格式化x轴
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

            # 调整布局
            plt.tight_layout()

            # 保存图表
            chart_file = os.path.join(self.charts_dir, f"{symbol}_kline_{int(time.time())}.png")
            plt.savefig(chart_file, dpi=100, bbox_inches='tight')
            plt.close()

            logger.info(f"生成K线图: {symbol}")
            return chart_file

        except Exception as e:
            logger.error(f"生成K线图失败: {e}")
            return None

    def generate_asset_pie_chart(self, distribution):
        """
        生成资产饼图

        Args:
            distribution: 资产分布数据

        Returns:
            图表文件路径
        """
        try:
            if not HAS_MATPLOTLIB:
                return self._generate_placeholder_chart("资产分布图")

            if not distribution or not distribution.get('distribution'):
                logger.warning("资产分布数据为空")
                return None

            # 准备数据
            assets = distribution['distribution']

            # 只显示前10个资产
            if len(assets) > 10:
                other_value = sum(a['value'] for a in assets[10:])
                assets = assets[:10]
                if other_value > 0:
                    assets.append({
                        'currency': 'Others',
                        'value': other_value,
                        'percentage': (other_value / distribution.get('total_value_usdt', 1)) * 100
                    })

            labels = []
            values = []

            for asset in assets:
                labels.append(f"{asset['currency']} ({asset['percentage']:.1f}%)")
                values.append(asset['value'])

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 8))

            # 绘制饼图
            colors = plt.cm.Set3(range(len(values)))
            wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors,
                                              autopct='%1.1f%%', startangle=90)

            # 设置标题
            total_value = distribution.get('total_value_usdt', 0)
            ax.set_title(f'Asset Distribution\nTotal: ${total_value:.2f} USDT',
                        fontsize=14, fontweight='bold')

            # 优化文本显示
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_color('white')
                autotext.set_weight('bold')

            # 保存图表
            chart_file = os.path.join(self.charts_dir, f"asset_pie_{int(time.time())}.png")
            plt.savefig(chart_file, dpi=100, bbox_inches='tight')
            plt.close()

            logger.info("生成资产分布图")
            return chart_file

        except Exception as e:
            logger.error(f"生成资产饼图失败: {e}")
            return None

    def generate_market_overview(self, tickers):
        """
        生成市场概览图

        Args:
            tickers: 行情数据列表

        Returns:
            图表文件路径
        """
        try:
            if not HAS_MATPLOTLIB:
                return self._generate_placeholder_chart("市场概览")

            if not tickers:
                logger.warning("行情数据为空")
                return None

            # 准备数据（取前20个）
            tickers = tickers[:20]
            symbols = [t['symbol'].replace('usdt', '').upper() for t in tickers]
            changes = [t['change'] for t in tickers]

            # 创建图表
            fig, ax = plt.subplots(figsize=(12, 6))

            # 设置颜色（涨绿跌红）
            colors = ['green' if c >= 0 else 'red' for c in changes]

            # 绘制条形图
            bars = ax.bar(range(len(symbols)), changes, color=colors, alpha=0.8)

            # 设置标题和标签
            ax.set_title('Market Overview - 24h Change %', fontsize=14, fontweight='bold')
            ax.set_xlabel('Symbol', fontsize=10)
            ax.set_ylabel('Change %', fontsize=10)

            # 设置x轴标签
            ax.set_xticks(range(len(symbols)))
            ax.set_xticklabels(symbols, rotation=45, ha='right')

            # 添加网格
            ax.grid(True, alpha=0.3, axis='y')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

            # 添加数值标签
            for bar, change in zip(bars, changes):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{change:.1f}%',
                       ha='center', va='bottom' if height >= 0 else 'top',
                       fontsize=8)

            # 调整布局
            plt.tight_layout()

            # 保存图表
            chart_file = os.path.join(self.charts_dir, f"market_{int(time.time())}.png")
            plt.savefig(chart_file, dpi=100, bbox_inches='tight')
            plt.close()

            logger.info("生成市场概览图")
            return chart_file

        except Exception as e:
            logger.error(f"生成市场概览失败: {e}")
            return None

    def generate_grid_visualization(self, grid_config, current_price):
        """
        生成网格可视化图

        Args:
            grid_config: 网格配置
            current_price: 当前价格

        Returns:
            图表文件路径
        """
        try:
            if not HAS_MATPLOTLIB:
                return self._generate_placeholder_chart("网格图")

            if not grid_config:
                logger.warning("网格配置为空")
                return None

            # 准备数据
            grid_prices = grid_config.get('grid_prices', [])
            if not grid_prices:
                return None

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 8))

            # 绘制网格线
            for i, price in enumerate(grid_prices):
                ax.axhline(y=price, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
                # 标记价格
                ax.text(0.02, price, f'${price:.2f}', transform=ax.get_yaxis_transform(),
                       fontsize=8, va='center')

            # 标记当前价格
            ax.axhline(y=current_price, color='blue', linestyle='-', linewidth=2, label='Current Price')

            # 标记上下限
            ax.axhline(y=grid_config['price_upper'], color='red', linestyle='-', linewidth=1.5, label='Upper Limit')
            ax.axhline(y=grid_config['price_lower'], color='green', linestyle='-', linewidth=1.5, label='Lower Limit')

            # 填充网格区域
            ax.fill_between([0, 1], grid_config['price_lower'], grid_config['price_upper'],
                          alpha=0.1, color='blue', transform=ax.get_xaxis_transform())

            # 设置标题和标签
            symbol = grid_config.get('symbol', 'Unknown').upper()
            ax.set_title(f'{symbol} Grid Trading Visualization\nGrids: {len(grid_prices)-1}',
                        fontsize=14, fontweight='bold')
            ax.set_ylabel('Price (USDT)', fontsize=10)

            # 设置y轴范围
            price_margin = (grid_config['price_upper'] - grid_config['price_lower']) * 0.1
            ax.set_ylim(grid_config['price_lower'] - price_margin,
                       grid_config['price_upper'] + price_margin)

            # 隐藏x轴
            ax.set_xticks([])

            # 添加图例
            ax.legend(loc='upper right')

            # 添加统计信息
            info_text = f"Range: ${grid_config['price_lower']:.2f} - ${grid_config['price_upper']:.2f}\n"
            info_text += f"Grid Count: {grid_config.get('grid_count', 0)}\n"
            info_text += f"Amount per Grid: {grid_config.get('amount_per_grid', 0):.6f}\n"
            info_text += f"Completed Trades: {grid_config.get('completed_trades', 0)}\n"
            info_text += f"Total Profit: ${grid_config.get('total_profit', 0):.2f}"

            ax.text(0.98, 0.02, info_text, transform=ax.transAxes,
                   fontsize=9, va='bottom', ha='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            # 调整布局
            plt.tight_layout()

            # 保存图表
            chart_file = os.path.join(self.charts_dir, f"grid_{int(time.time())}.png")
            plt.savefig(chart_file, dpi=100, bbox_inches='tight')
            plt.close()

            logger.info(f"生成网格图: {symbol}")
            return chart_file

        except Exception as e:
            logger.error(f"生成网格图失败: {e}")
            return None

    def generate_pnl_chart(self, history_data):
        """
        生成盈亏曲线图

        Args:
            history_data: 历史余额数据

        Returns:
            图表文件路径
        """
        try:
            if not HAS_MATPLOTLIB:
                return self._generate_placeholder_chart("盈亏曲线")

            if not history_data:
                logger.warning("历史数据为空")
                return None

            # 准备数据
            dates = []
            values = []

            for date_str, data in sorted(history_data.items()):
                dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
                values.append(data.get('total_usdt', 0))

            if len(dates) < 2:
                return None

            # 计算日收益
            daily_pnl = [0]
            for i in range(1, len(values)):
                daily_pnl.append(values[i] - values[i-1])

            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})

            # 余额曲线
            ax1.plot(dates, values, marker='o', linewidth=2, markersize=5, color='blue')
            ax1.fill_between(dates, values, alpha=0.3, color='blue')
            ax1.set_title('Balance History', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Balance (USDT)', fontsize=10)
            ax1.grid(True, alpha=0.3)

            # 标记最高和最低点
            max_idx = values.index(max(values))
            min_idx = values.index(min(values))
            ax1.annotate(f'Max: ${values[max_idx]:.2f}',
                        xy=(dates[max_idx], values[max_idx]),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            ax1.annotate(f'Min: ${values[min_idx]:.2f}',
                        xy=(dates[min_idx], values[min_idx]),
                        xytext=(10, -20), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', fc='orange', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

            # 日收益条形图
            colors = ['green' if p >= 0 else 'red' for p in daily_pnl]
            ax2.bar(dates, daily_pnl, color=colors, alpha=0.7)
            ax2.set_title('Daily P&L', fontsize=12)
            ax2.set_ylabel('P&L (USDT)', fontsize=10)
            ax2.set_xlabel('Date', fontsize=10)
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

            # 格式化x轴
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

            # 添加统计信息
            total_pnl = values[-1] - values[0]
            total_pnl_pct = (total_pnl / values[0] * 100) if values[0] > 0 else 0
            avg_daily = sum(daily_pnl) / len(daily_pnl) if daily_pnl else 0

            info_text = f"Total P&L: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)\n"
            info_text += f"Avg Daily: ${avg_daily:.2f}\n"
            info_text += f"Current: ${values[-1]:.2f}"

            ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes,
                    fontsize=10, va='top', ha='left',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            # 调整布局
            plt.tight_layout()

            # 保存图表
            chart_file = os.path.join(self.charts_dir, f"pnl_{int(time.time())}.png")
            plt.savefig(chart_file, dpi=100, bbox_inches='tight')
            plt.close()

            logger.info("生成盈亏曲线图")
            return chart_file

        except Exception as e:
            logger.error(f"生成盈亏曲线失败: {e}")
            return None

    def _calculate_ma(self, prices, period):
        """计算移动平均线"""
        if len(prices) < period:
            return []

        ma_values = []
        for i in range(period - 1, len(prices)):
            ma = sum(prices[i - period + 1:i + 1]) / period
            ma_values.append(ma)

        return ma_values

    def _generate_placeholder_chart(self, chart_type):
        """生成占位图表（当matplotlib不可用时）"""
        try:
            # 创建一个简单的文本文件作为占位
            chart_file = os.path.join(self.charts_dir, f"{chart_type}_{int(time.time())}.txt")

            with open(chart_file, 'w', encoding='utf-8') as f:
                f.write(f"=== {chart_type} ===\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("注意: matplotlib未安装，无法生成图表\n")
                f.write("请运行: pip install matplotlib pandas numpy\n")

            logger.warning(f"生成占位图表: {chart_type}")
            return chart_file

        except Exception as e:
            logger.error(f"生成占位图表失败: {e}")
            return None

    def get_chart_stats(self):
        """获取图表统计"""
        try:
            if os.path.exists(self.charts_dir):
                files = os.listdir(self.charts_dir)

                # 统计各类型图表
                stats = {
                    'total': len(files),
                    'kline': len([f for f in files if 'kline' in f]),
                    'asset': len([f for f in files if 'asset' in f]),
                    'market': len([f for f in files if 'market' in f]),
                    'grid': len([f for f in files if 'grid' in f]),
                    'pnl': len([f for f in files if 'pnl' in f]),
                    'directory': self.charts_dir
                }

                return stats

            return {'total': 0, 'directory': self.charts_dir}

        except Exception as e:
            logger.error(f"获取图表统计失败: {e}")
            return {'total': 0, 'directory': self.charts_dir}

# 兼容别名
ChartGenerator = ChartsModule