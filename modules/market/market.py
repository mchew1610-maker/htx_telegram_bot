"""市场数据模块 - 完整实现"""
import requests
import time
from datetime import datetime, timedelta
from loguru import logger
from utils.htx_api_base import HTXApiBase

class MarketModule(HTXApiBase):
    """市场数据模块 - 真实数据实现"""

    def __init__(self, access_key=None, secret_key=None, rest_url="https://api.huobi.pro"):
        """初始化 - 市场数据API不需要认证"""
        # 市场数据接口不需要API密钥
        if access_key and not access_key.startswith("http"):
            super().__init__(access_key, secret_key, rest_url)
        else:
            # 如果第一个参数是URL或没有access_key，只设置URL
            self.rest_url = access_key if access_key and access_key.startswith("http") else rest_url
            self.session = requests.Session()
            self.session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'HTX-Telegram-Bot/1.0'
            })

        logger.info(f"市场模块初始化: {self.rest_url}")

    def get_ticker(self, symbol):
        """
        获取行情数据

        Args:
            symbol: 交易对 (如 btcusdt)

        Returns:
            行情数据字典
        """
        try:
            url = f"{self.rest_url}/market/detail/merged"
            params = {'symbol': symbol.lower()}

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and data.get('tick'):
                    tick = data['tick']

                    # 计算涨跌幅
                    close = float(tick.get('close', 0))
                    open_price = float(tick.get('open', 1))
                    change = ((close - open_price) / open_price * 100) if open_price > 0 else 0

                    return {
                        'symbol': symbol,
                        'close': close,
                        'change': change,
                        'high': float(tick.get('high', 0)),
                        'low': float(tick.get('low', 0)),
                        'volume': float(tick.get('vol', 0)),
                        'amount': float(tick.get('amount', 0)),
                        'bid': float(tick.get('bid', [0])[0]) if tick.get('bid') else 0,
                        'ask': float(tick.get('ask', [0])[0]) if tick.get('ask') else 0,
                        'bid_size': float(tick.get('bid', [0, 0])[1]) if len(tick.get('bid', [])) > 1 else 0,
                        'ask_size': float(tick.get('ask', [0, 0])[1]) if len(tick.get('ask', [])) > 1 else 0,
                        'count': tick.get('count', 0),
                        'timestamp': datetime.now().isoformat()
                    }

            logger.warning(f"获取行情失败: {symbol}")
            return None

        except Exception as e:
            logger.error(f"获取行情异常 {symbol}: {e}")
            return None

    def get_all_tickers(self):
        """获取所有交易对行情"""
        try:
            url = f"{self.rest_url}/market/tickers"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    tickers = []
                    for tick in data.get('data', []):
                        symbol = tick.get('symbol', '')
                        close = float(tick.get('close', 0))
                        open_price = float(tick.get('open', 1))
                        change = ((close - open_price) / open_price * 100) if open_price > 0 else 0

                        tickers.append({
                            'symbol': symbol,
                            'close': close,
                            'change': change,
                            'volume': float(tick.get('vol', 0)),
                            'amount': float(tick.get('amount', 0)),
                            'high': float(tick.get('high', 0)),
                            'low': float(tick.get('low', 0))
                        })

                    return tickers

            return []

        except Exception as e:
            logger.error(f"获取全部行情失败: {e}")
            return []

    def get_klines(self, symbol, period='1day', size=150):
        """
        获取K线数据

        Args:
            symbol: 交易对
            period: 周期 (1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon)
            size: 数量 (最大2000)

        Returns:
            K线数据列表
        """
        try:
            url = f"{self.rest_url}/market/history/kline"
            params = {
                'symbol': symbol.lower(),
                'period': period,
                'size': min(size, 2000)  # 最大2000
            }

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    klines = []
                    for item in data.get('data', []):
                        klines.append({
                            'id': item.get('id'),  # 时间戳
                            'open': float(item.get('open', 0)),
                            'close': float(item.get('close', 0)),
                            'high': float(item.get('high', 0)),
                            'low': float(item.get('low', 0)),
                            'volume': float(item.get('vol', 0)),
                            'amount': float(item.get('amount', 0)),
                            'count': item.get('count', 0),
                            'timestamp': datetime.fromtimestamp(item.get('id', 0)).isoformat()
                        })

                    return klines

            return []

        except Exception as e:
            logger.error(f"获取K线失败 {symbol}: {e}")
            return []

    def get_4hour_range(self, symbol):
        """
        获取4小时K线的高低点范围
        用于网格交易

        Args:
            symbol: 交易对

        Returns:
            包含高低点的字典
        """
        try:
            # 获取最近的4小时K线
            klines = self.get_klines(symbol, period='4hour', size=1)

            if klines:
                kline = klines[0]
                high = kline['high']
                low = kline['low']

                # 计算范围百分比
                range_percent = ((high - low) / low * 100) if low > 0 else 0

                return {
                    'high': high,
                    'low': low,
                    'range_percent': range_percent,
                    'timestamp': kline['timestamp']
                }

            return None

        except Exception as e:
            logger.error(f"获取4小时范围失败 {symbol}: {e}")
            return None

    def get_depth(self, symbol, depth=20):
        """
        获取深度数据

        Args:
            symbol: 交易对
            depth: 深度档位

        Returns:
            深度数据
        """
        try:
            url = f"{self.rest_url}/market/depth"
            params = {
                'symbol': symbol.lower(),
                'depth': depth,
                'type': 'step0'  # 精度类型
            }

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and data.get('tick'):
                    tick = data['tick']

                    return {
                        'symbol': symbol,
                        'bids': tick.get('bids', []),  # [[price, amount], ...]
                        'asks': tick.get('asks', []),
                        'timestamp': datetime.fromtimestamp(tick.get('ts', 0) / 1000).isoformat()
                    }

            return None

        except Exception as e:
            logger.error(f"获取深度失败 {symbol}: {e}")
            return None

    def get_24hr_stats(self, symbol):
        """
        获取24小时统计

        Args:
            symbol: 交易对

        Returns:
            24小时统计数据
        """
        try:
            ticker = self.get_ticker(symbol)

            if ticker:
                return {
                    'symbol': symbol,
                    'price_change': ticker['close'] - (ticker['close'] / (1 + ticker['change'] / 100)),
                    'price_change_percent': ticker['change'],
                    'high_price': ticker['high'],
                    'low_price': ticker['low'],
                    'volume': ticker['volume'],
                    'quote_volume': ticker['amount'],
                    'close_price': ticker['close'],
                    'timestamp': ticker['timestamp']
                }

            return None

        except Exception as e:
            logger.error(f"获取24小时统计失败 {symbol}: {e}")
            return None

    def get_top_gainers(self, limit=10):
        """获取涨幅榜"""
        try:
            tickers = self.get_all_tickers()

            # 过滤USDT交易对
            usdt_tickers = [t for t in tickers if t['symbol'].endswith('usdt')]

            # 按涨幅排序
            usdt_tickers.sort(key=lambda x: x['change'], reverse=True)

            return usdt_tickers[:limit]

        except Exception as e:
            logger.error(f"获取涨幅榜失败: {e}")
            return []

    def get_top_losers(self, limit=10):
        """获取跌幅榜"""
        try:
            tickers = self.get_all_tickers()

            # 过滤USDT交易对
            usdt_tickers = [t for t in tickers if t['symbol'].endswith('usdt')]

            # 按跌幅排序
            usdt_tickers.sort(key=lambda x: x['change'])

            return usdt_tickers[:limit]

        except Exception as e:
            logger.error(f"获取跌幅榜失败: {e}")
            return []

    def get_top_volume(self, limit=10):
        """获取成交量榜"""
        try:
            tickers = self.get_all_tickers()

            # 过滤USDT交易对
            usdt_tickers = [t for t in tickers if t['symbol'].endswith('usdt')]

            # 按成交量排序
            usdt_tickers.sort(key=lambda x: x['amount'], reverse=True)

            return usdt_tickers[:limit]

        except Exception as e:
            logger.error(f"获取成交量榜失败: {e}")
            return []

    def get_trade_detail(self, symbol):
        """
        获取最新成交

        Args:
            symbol: 交易对

        Returns:
            成交数据
        """
        try:
            url = f"{self.rest_url}/market/trade"
            params = {'symbol': symbol.lower()}

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and data.get('tick'):
                    tick = data['tick']
                    trades = []

                    for trade in tick.get('data', []):
                        trades.append({
                            'id': trade.get('id'),
                            'price': float(trade.get('price', 0)),
                            'amount': float(trade.get('amount', 0)),
                            'direction': trade.get('direction'),  # buy/sell
                            'timestamp': datetime.fromtimestamp(trade.get('ts', 0) / 1000).isoformat()
                        })

                    return trades

            return []

        except Exception as e:
            logger.error(f"获取成交明细失败 {symbol}: {e}")
            return []

# 兼容别名
MarketData = MarketModule