"""
网格交易模块
基于4小时K线高低点的网格交易策略
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from utils.logger import get_module_logger, trading_logger

log = get_module_logger('grid')

class GridTradingModule:
    """网格交易模块"""
    
    def __init__(self, market_module, trading_module, monitor_module):
        self.market = market_module
        self.trading = trading_module
        self.monitor = monitor_module
        
        # 网格配置
        self.grid_configs = {}
        self.active_grids = {}
        self.grid_orders = {}
        
        # 加载保存的网格配置
        self.load_grid_configs()
    
    def create_grid(
        self,
        symbol: str,
        grid_count: int = 10,
        amount_per_grid: float = 0.001,
        use_4h_range: bool = True,
        price_upper: float = None,
        price_lower: float = None
    ) -> Dict:
        """
        创建网格交易
        
        Args:
            symbol: 交易对
            grid_count: 网格数量
            amount_per_grid: 每网格交易量
            use_4h_range: 是否使用4小时K线范围
            price_upper: 上限价格（手动设置时）
            price_lower: 下限价格（手动设置时）
            
        Returns:
            创建结果
        """
        try:
            # 检查是否已有活动网格
            if symbol in self.active_grids and self.active_grids[symbol].get('active'):
                return {'error': f'{symbol} 已有活动的网格交易'}
            
            # 获取价格范围
            if use_4h_range:
                # 使用4小时K线高低点
                range_info = self.market.get_4hour_range(symbol)
                if not range_info:
                    return {'error': '获取4小时K线失败'}
                
                price_upper = range_info['high']
                price_lower = range_info['low']
                
                log.info(f"使用4小时K线范围: {price_lower:.4f} - {price_upper:.4f}")
            else:
                # 手动设置范围
                if not price_upper or not price_lower:
                    return {'error': '请指定价格上下限'}
            
            # 获取当前价格
            ticker = self.market.get_ticker(symbol)
            if not ticker:
                return {'error': '获取当前价格失败'}
            
            current_price = ticker['close']
            
            # 验证价格范围
            if price_upper <= price_lower:
                return {'error': '价格上限必须大于下限'}
            
            if current_price > price_upper or current_price < price_lower:
                return {'error': f'当前价格 {current_price:.4f} 不在网格范围内'}
            
            # 计算网格价格
            grid_prices = self._calculate_grid_prices(
                price_upper,
                price_lower,
                grid_count
            )
            
            # 获取交易对信息
            symbol_info = self.trading.get_symbol_info(symbol)
            if not symbol_info:
                return {'error': '获取交易对信息失败'}
            
            # 创建网格配置
            config = {
                'symbol': symbol,
                'grid_count': grid_count,
                'amount_per_grid': amount_per_grid,
                'price_upper': price_upper,
                'price_lower': price_lower,
                'current_price': current_price,
                'grid_prices': grid_prices,
                'active': True,
                'created_at': datetime.now().isoformat(),
                'total_profit': 0,
                'completed_trades': 0,
                'pending_orders': []
            }
            
            # 保存配置
            self.grid_configs[symbol] = config
            self.active_grids[symbol] = config
            self.save_grid_configs()
            
            # 创建初始订单
            initial_orders = self._create_initial_orders(config, current_price)
            config['pending_orders'] = initial_orders
            
            trading_logger.info(f"创建网格交易 - {symbol}: {grid_count}格, "
                               f"范围: {price_lower:.4f}-{price_upper:.4f}")
            
            return {
                'success': True,
                'symbol': symbol,
                'config': config,
                'initial_orders': len(initial_orders),
                'message': f'网格交易创建成功，已下{len(initial_orders)}个初始订单'
            }
            
        except Exception as e:
            log.error(f"创建网格失败: {e}")
            return {'error': str(e)}
    
    def _calculate_grid_prices(
        self,
        price_upper: float,
        price_lower: float,
        grid_count: int
    ) -> List[float]:
        """
        计算网格价格点位
        
        Args:
            price_upper: 上限价格
            price_lower: 下限价格
            grid_count: 网格数量
            
        Returns:
            价格列表
        """
        prices = []
        price_diff = (price_upper - price_lower) / grid_count
        
        for i in range(grid_count + 1):
            price = price_lower + (price_diff * i)
            prices.append(round(price, 4))
        
        return prices
    
    def _create_initial_orders(self, config: Dict, current_price: float) -> List[Dict]:
        """
        创建初始订单
        
        Args:
            config: 网格配置
            current_price: 当前价格
            
        Returns:
            订单列表
        """
        orders = []
        symbol = config['symbol']
        amount = config['amount_per_grid']
        
        for price in config['grid_prices']:
            if price < current_price * 0.99:  # 买单：价格低于当前价1%
                # 创建买单
                result = self.trading.buy_limit(symbol, price, amount)
                if result.get('success'):
                    orders.append({
                        'order_id': result['order_id'],
                        'type': 'buy',
                        'price': price,
                        'amount': amount,
                        'status': 'pending'
                    })
                    log.info(f"创建网格买单: {price:.4f}")
            elif price > current_price * 1.01:  # 卖单：价格高于当前价1%
                # 创建卖单
                result = self.trading.sell_limit(symbol, price, amount)
                if result.get('success'):
                    orders.append({
                        'order_id': result['order_id'],
                        'type': 'sell',
                        'price': price,
                        'amount': amount,
                        'status': 'pending'
                    })
                    log.info(f"创建网格卖单: {price:.4f}")
        
        return orders
    
    def update_grid(self, symbol: str) -> Dict:
        """
        更新网格订单（检查成交并补单）
        
        Args:
            symbol: 交易对
            
        Returns:
            更新结果
        """
        if symbol not in self.active_grids:
            return {'error': f'{symbol} 没有活动的网格交易'}
        
        config = self.active_grids[symbol]
        if not config['active']:
            return {'error': '网格交易已停止'}
        
        try:
            updated_orders = []
            new_orders = []
            completed = 0
            total_profit = 0
            
            # 检查每个待成交订单
            for order in config['pending_orders']:
                order_detail = self.trading.get_order_detail(order['order_id'])
                
                if order_detail and order_detail['state'] == 'filled':
                    # 订单已成交
                    completed += 1
                    
                    # 计算利润（简化计算）
                    if order['type'] == 'sell':
                        profit = order['amount'] * order['price'] * 0.001  # 估算利润
                        total_profit += profit
                    
                    # 创建反向订单（补单）
                    if order['type'] == 'buy':
                        # 买单成交，创建卖单
                        new_price = order['price'] * 1.005  # 加价0.5%卖出
                        result = self.trading.sell_limit(
                            symbol,
                            new_price,
                            order['amount']
                        )
                        if result.get('success'):
                            new_orders.append({
                                'order_id': result['order_id'],
                                'type': 'sell',
                                'price': new_price,
                                'amount': order['amount'],
                                'status': 'pending'
                            })
                            log.info(f"网格补单（卖）: {new_price:.4f}")
                    else:
                        # 卖单成交，创建买单
                        new_price = order['price'] * 0.995  # 降价0.5%买入
                        result = self.trading.buy_limit(
                            symbol,
                            new_price,
                            order['amount']
                        )
                        if result.get('success'):
                            new_orders.append({
                                'order_id': result['order_id'],
                                'type': 'buy',
                                'price': new_price,
                                'amount': order['amount'],
                                'status': 'pending'
                            })
                            log.info(f"网格补单（买）: {new_price:.4f}")
                else:
                    # 订单未成交，保留
                    updated_orders.append(order)
            
            # 更新配置
            config['pending_orders'] = updated_orders + new_orders
            config['completed_trades'] += completed
            config['total_profit'] += total_profit
            config['last_update'] = datetime.now().isoformat()
            
            # 保存配置
            self.save_grid_configs()
            
            return {
                'success': True,
                'symbol': symbol,
                'completed_trades': completed,
                'new_orders': len(new_orders),
                'total_completed': config['completed_trades'],
                'total_profit': config['total_profit'],
                'active_orders': len(config['pending_orders'])
            }
            
        except Exception as e:
            log.error(f"更新网格失败 {symbol}: {e}")
            return {'error': str(e)}
    
    def stop_grid(self, symbol: str, cancel_orders: bool = True) -> Dict:
        """
        停止网格交易
        
        Args:
            symbol: 交易对
            cancel_orders: 是否撤销所有订单
            
        Returns:
            停止结果
        """
        if symbol not in self.active_grids:
            return {'error': f'{symbol} 没有活动的网格交易'}
        
        config = self.active_grids[symbol]
        
        try:
            cancelled_count = 0
            
            # 撤销所有订单
            if cancel_orders:
                for order in config['pending_orders']:
                    result = self.trading.cancel_order(order['order_id'])
                    if result.get('success'):
                        cancelled_count += 1
            
            # 标记为非活动
            config['active'] = False
            config['stopped_at'] = datetime.now().isoformat()
            
            # 从活动列表移除
            del self.active_grids[symbol]
            
            # 保存配置
            self.save_grid_configs()
            
            trading_logger.info(f"停止网格交易 - {symbol}: "
                               f"总成交: {config['completed_trades']}, "
                               f"总利润: {config['total_profit']:.4f}")
            
            return {
                'success': True,
                'symbol': symbol,
                'cancelled_orders': cancelled_count,
                'total_trades': config['completed_trades'],
                'total_profit': config['total_profit'],
                'message': f'网格交易已停止，撤销了{cancelled_count}个订单'
            }
            
        except Exception as e:
            log.error(f"停止网格失败 {symbol}: {e}")
            return {'error': str(e)}
    
    def get_grid_status(self, symbol: str = None) -> Dict:
        """
        获取网格状态
        
        Args:
            symbol: 交易对（可选，不指定则返回所有）
            
        Returns:
            状态信息
        """
        if symbol:
            if symbol not in self.grid_configs:
                return {'error': f'{symbol} 没有网格配置'}
            
            config = self.grid_configs[symbol]
            return {
                'symbol': symbol,
                'active': config.get('active', False),
                'grid_count': config['grid_count'],
                'price_range': f"{config['price_lower']:.4f} - {config['price_upper']:.4f}",
                'completed_trades': config['completed_trades'],
                'total_profit': config['total_profit'],
                'active_orders': len(config.get('pending_orders', [])),
                'created_at': config['created_at'],
                'last_update': config.get('last_update')
            }
        else:
            # 返回所有网格状态
            all_status = []
            for sym, config in self.grid_configs.items():
                all_status.append({
                    'symbol': sym,
                    'active': config.get('active', False),
                    'completed_trades': config['completed_trades'],
                    'total_profit': config['total_profit'],
                    'active_orders': len(config.get('pending_orders', []))
                })
            
            return {
                'total_grids': len(self.grid_configs),
                'active_grids': len(self.active_grids),
                'grids': all_status
            }
    
    def check_4hour_update(self) -> Dict:
        """
        检查4小时K线更新并通知
        
        Returns:
            检查结果
        """
        notifications = []
        
        for symbol in self.active_grids:
            range_info = self.market.get_4hour_range(symbol)
            if range_info:
                config = self.active_grids[symbol]
                
                # 检查是否需要调整网格
                if (abs(range_info['high'] - config['price_upper']) / config['price_upper'] > 0.05 or
                    abs(range_info['low'] - config['price_lower']) / config['price_lower'] > 0.05):
                    
                    notifications.append({
                        'symbol': symbol,
                        'current_range': f"{config['price_lower']:.4f} - {config['price_upper']:.4f}",
                        'new_range': f"{range_info['low']:.4f} - {range_info['high']:.4f}",
                        'change_percent': range_info['range_percent'],
                        'message': '4小时K线范围变化较大，建议调整网格'
                    })
        
        return {
            'checked': len(self.active_grids),
            'notifications': notifications
        }
    
    def save_grid_configs(self):
        """保存网格配置到文件"""
        os.makedirs('data/grids', exist_ok=True)
        
        with open('data/grids/configs.json', 'w') as f:
            json.dump(self.grid_configs, f, indent=2)
        
        log.debug("网格配置已保存")
    
    def load_grid_configs(self):
        """从文件加载网格配置"""
        try:
            with open('data/grids/configs.json', 'r') as f:
                self.grid_configs = json.load(f)
                
                # 恢复活动网格
                for symbol, config in self.grid_configs.items():
                    if config.get('active'):
                        self.active_grids[symbol] = config
                
                log.info(f"加载 {len(self.grid_configs)} 个网格配置")
        except FileNotFoundError:
            self.grid_configs = {}
            log.info("没有找到网格配置文件")
        except Exception as e:
            log.error(f"加载网格配置失败: {e}")
            self.grid_configs = {}
