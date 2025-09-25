"""
HTX (火币) API基础模块
处理API签名、请求发送等基础功能
"""

import time
import base64
import hashlib
import hmac
import json
from datetime import datetime
from urllib.parse import urlencode, quote
import requests
from typing import Dict, Optional, Any
from utils.logger import logger, get_module_logger

# 模块日志
log = get_module_logger('htx_api')

class HTXApiBase:
    """HTX API基础类"""
    
    def __init__(self, access_key: str, secret_key: str, rest_url: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.rest_url = rest_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'HTX-Telegram-Bot/1.0'
        })
    
    def _generate_signature(self, method: str, path: str, params: Dict = None) -> str:
        """
        生成API签名
        
        Args:
            method: HTTP方法 (GET/POST)
            path: API路径
            params: 请求参数
        
        Returns:
            签名字符串
        """
        # 添加必要的参数
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        
        params_to_sign = {
            'AccessKeyId': self.access_key,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp
        }
        
        # 合并自定义参数
        if params:
            params_to_sign.update(params)
        
        # 排序参数
        sorted_params = sorted(params_to_sign.items(), key=lambda x: x[0])
        
        # 编码参数
        encoded_params = urlencode(sorted_params, quote_via=quote)
        
        # 构造待签名字符串
        host = self.rest_url.replace('https://', '').replace('http://', '')
        payload = [method.upper(), host, path, encoded_params]
        payload_str = '\n'.join(payload)
        
        # 计算签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Base64编码
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        # 添加签名到参数
        params_to_sign['Signature'] = signature_b64
        
        return urlencode(params_to_sign, quote_via=quote)
    
    def request(self, method: str, path: str, params: Dict = None, body: Dict = None) -> Dict:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            path: API路径  
            params: URL参数
            body: 请求体
        
        Returns:
            响应数据
        """
        try:
            # 生成签名参数
            signed_params = self._generate_signature(method, path, params)
            url = f"{self.rest_url}{path}?{signed_params}"
            
            # 发送请求
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=10)
            else:
                response = self.session.post(
                    url, 
                    json=body if body else {},
                    timeout=10
                )
            
            # 检查响应
            response.raise_for_status()
            result = response.json()
            
            # 检查业务状态
            if result.get('status') == 'error':
                error_code = result.get('err-code', 'unknown')
                error_msg = result.get('err-msg', 'Unknown error')
                log.error(f"API错误: {error_code} - {error_msg}")
                raise Exception(f"API错误: {error_code} - {error_msg}")
            
            return result
            
        except requests.RequestException as e:
            log.error(f"请求失败: {str(e)}")
            raise
        except Exception as e:
            log.error(f"处理请求时出错: {str(e)}")
            raise
    
    def get(self, path: str, params: Dict = None) -> Dict:
        """GET请求"""
        return self.request('GET', path, params)
    
    def post(self, path: str, params: Dict = None, body: Dict = None) -> Dict:
        """POST请求"""
        return self.request('POST', path, params, body)

class HTXWebSocketBase:
    """HTX WebSocket基础类"""
    
    def __init__(self, access_key: str, secret_key: str, ws_url: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.ws_url = ws_url
        self.ws = None
        self.authenticated = False
        
    def _generate_auth_data(self) -> Dict:
        """生成WebSocket认证数据"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        
        params = {
            'accessKey': self.access_key,
            'signatureMethod': 'HmacSHA256',
            'signatureVersion': '2.1',
            'timestamp': timestamp
        }
        
        # 构造待签名字符串
        host = self.ws_url.replace('wss://', '').replace('ws://', '').split('/')[0]
        path = '/ws/v2'
        
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        encoded_params = urlencode(sorted_params)
        
        payload = ['GET', host, path, encoded_params]
        payload_str = '\n'.join(payload)
        
        # 计算签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return {
            'action': 'req',
            'ch': 'auth',
            'params': {
                'authType': 'api',
                'accessKey': self.access_key,
                'signatureMethod': 'HmacSHA256',
                'signatureVersion': '2.1',
                'timestamp': timestamp,
                'signature': signature_b64
            }
        }
    
    def connect(self):
        """连接WebSocket"""
        # 实现将在具体的WebSocket客户端模块中完成
        pass
    
    def subscribe(self, topic: str):
        """订阅主题"""
        # 实现将在具体的WebSocket客户端模块中完成
        pass
    
    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()
            self.ws = None
            self.authenticated = False
