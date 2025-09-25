"""
WebSocket实时数据模块
处理实时行情推送
"""

import json
import gzip
import threading
import time
from typing import Dict, Callable, List
import websocket
from utils.logger import get_module_logger

log = get_module_logger('websocket')

class HTXWebSocketClient:
    """HTX WebSocket客户端"""
    
    def __init__(self, ws_url: str = 'wss://api.huobi.pro/ws'):
        self.ws_url = ws_url
        self.ws = None
        self.subscriptions = {}
        self.callbacks = {}
        self.running = False
        self.reconnect_count = 0
        self.max_reconnect = 10
        self.ping_thread = None
        
    def connect(self):
        """连接WebSocket"""
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 启动连接线程
            self.running = True
            thread = threading.Thread(target=self._run)
            thread.daemon = True
            thread.start()
            
            log.info(f"WebSocket连接到 {self.ws_url}")
            
        except Exception as e:
            log.error(f"WebSocket连接失败: {e}")
            self._reconnect()
    
    def _run(self):
        """运行WebSocket"""
        while self.running:
            try:
                self.ws.run_forever()
                if self.running:
                    time.sleep(5)
                    self._reconnect()
            except Exception as e:
                log.error(f"WebSocket运行错误: {e}")
                time.sleep(5)
    
    def _on_open(self, ws):
        """连接建立"""
        log.info("WebSocket连接成功")
        self.reconnect_count = 0
        
        # 启动心跳线程
        self._start_ping()
        
        # 重新订阅
        for sub_id, sub_info in self.subscriptions.items():
            self._send_subscribe(sub_info['topic'])
    
    def _on_message(self, ws, message):
        """接收消息"""
        try:
            # 解压消息
            if isinstance(message, bytes):
                message = gzip.decompress(message).decode('utf-8')
            
            data = json.loads(message)
            
            # 处理心跳
            if 'ping' in data:
                self._send_pong(data['ping'])
                return
            
            # 处理订阅响应
            if 'subbed' in data:
                log.info(f"订阅成功: {data['subbed']}")
                return
            
            # 处理错误
            if 'status' in data and data['status'] == 'error':
                log.error(f"WebSocket错误: {data.get('err-msg', 'Unknown')}")
                return
            
            # 处理数据推送
            if 'ch' in data:
                self._handle_data(data['ch'], data)
                
        except Exception as e:
            log.error(f"处理消息失败: {e}")
    
    def _on_error(self, ws, error):
        """错误处理"""
        log.error(f"WebSocket错误: {error}")
    
    def _on_close(self, ws):
        """连接关闭"""
        log.warning("WebSocket连接关闭")
        if self.ping_thread:
            self.ping_thread = None
    
    def _reconnect(self):
        """重连"""
        if self.reconnect_count >= self.max_reconnect:
            log.error("达到最大重连次数，停止重连")
            self.running = False
            return
        
        self.reconnect_count += 1
        wait_time = min(self.reconnect_count * 5, 60)
        
        log.info(f"第{self.reconnect_count}次重连，等待{wait_time}秒...")
        time.sleep(wait_time)
        
        if self.running:
            self.connect()
    
    def _start_ping(self):
        """启动心跳"""
        def ping_loop():
            while self.running and self.ws:
                try:
                    time.sleep(20)
                    if self.ws:
                        self.ws.send(json.dumps({"ping": int(time.time() * 1000)}))
                except Exception as e:
                    log.error(f"发送心跳失败: {e}")
                    break
        
        self.ping_thread = threading.Thread(target=ping_loop)
        self.ping_thread.daemon = True
        self.ping_thread.start()
    
    def _send_pong(self, ping_id):
        """发送pong"""
        try:
            pong_msg = {"pong": ping_id}
            self.ws.send(json.dumps(pong_msg))
        except Exception as e:
            log.error(f"发送pong失败: {e}")
    
    def _send_subscribe(self, topic: str):
        """发送订阅消息"""
        try:
            sub_msg = {
                "sub": topic,
                "id": f"{topic}_{int(time.time())}"
            }
            self.ws.send(json.dumps(sub_msg))
            log.info(f"发送订阅: {topic}")
        except Exception as e:
            log.error(f"发送订阅失败: {e}")
    
    def _handle_data(self, channel: str, data: Dict):
        """处理数据推送"""
        # 查找对应的回调函数
        for sub_id, sub_info in self.subscriptions.items():
            if channel == sub_info['topic']:
                callback = sub_info['callback']
                if callback:
                    try:
                        callback(data)
                    except Exception as e:
                        log.error(f"执行回调失败: {e}")
                break
    
    def subscribe_ticker(self, symbol: str, callback: Callable):
        """
        订阅行情数据
        
        Args:
            symbol: 交易对
            callback: 回调函数
        """
        topic = f"market.{symbol}.ticker"
        sub_id = f"ticker_{symbol}"
        
        self.subscriptions[sub_id] = {
            'topic': topic,
            'callback': callback,
            'symbol': symbol
        }
        
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self._send_subscribe(topic)
        
        log.info(f"订阅行情: {symbol}")
        return sub_id
    
    def subscribe_depth(self, symbol: str, callback: Callable, step: str = 'step0'):
        """
        订阅深度数据
        
        Args:
            symbol: 交易对
            callback: 回调函数
            step: 深度类型
        """
        topic = f"market.{symbol}.depth.{step}"
        sub_id = f"depth_{symbol}_{step}"
        
        self.subscriptions[sub_id] = {
            'topic': topic,
            'callback': callback,
            'symbol': symbol
        }
        
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self._send_subscribe(topic)
        
        log.info(f"订阅深度: {symbol} {step}")
        return sub_id
    
    def subscribe_kline(self, symbol: str, period: str, callback: Callable):
        """
        订阅K线数据
        
        Args:
            symbol: 交易对
            period: 周期
            callback: 回调函数
        """
        topic = f"market.{symbol}.kline.{period}"
        sub_id = f"kline_{symbol}_{period}"
        
        self.subscriptions[sub_id] = {
            'topic': topic,
            'callback': callback,
            'symbol': symbol,
            'period': period
        }
        
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self._send_subscribe(topic)
        
        log.info(f"订阅K线: {symbol} {period}")
        return sub_id
    
    def subscribe_trade(self, symbol: str, callback: Callable):
        """
        订阅成交数据
        
        Args:
            symbol: 交易对
            callback: 回调函数
        """
        topic = f"market.{symbol}.trade.detail"
        sub_id = f"trade_{symbol}"
        
        self.subscriptions[sub_id] = {
            'topic': topic,
            'callback': callback,
            'symbol': symbol
        }
        
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self._send_subscribe(topic)
        
        log.info(f"订阅成交: {symbol}")
        return sub_id
    
    def unsubscribe(self, sub_id: str):
        """
        取消订阅
        
        Args:
            sub_id: 订阅ID
        """
        if sub_id in self.subscriptions:
            topic = self.subscriptions[sub_id]['topic']
            
            try:
                unsub_msg = {
                    "unsub": topic,
                    "id": f"{topic}_{int(time.time())}"
                }
                self.ws.send(json.dumps(unsub_msg))
                
                del self.subscriptions[sub_id]
                log.info(f"取消订阅: {topic}")
                
            except Exception as e:
                log.error(f"取消订阅失败: {e}")
    
    def close(self):
        """关闭连接"""
        log.info("关闭WebSocket连接")
        self.running = False
        
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
        
        self.subscriptions.clear()
