import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
import json

# 加载环境变量
load_dotenv()

@dataclass
class TelegramConfig:
    """Telegram机器人配置"""
    bot_token: str
    chat_id: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        return cls(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            chat_id=os.getenv('TELEGRAM_CHAT_ID')
        )

@dataclass
class HTXConfig:
    """火币API配置"""
    access_key: str
    secret_key: str
    rest_url: str = 'https://api.huobi.pro'
    ws_url: str = 'wss://api.huobi.pro/ws/v2'
    
    @classmethod
    def from_env(cls):
        return cls(
            access_key=os.getenv('HTX_ACCESS_KEY'),
            secret_key=os.getenv('HTX_SECRET_KEY'),
            rest_url=os.getenv('HTX_REST_URL', 'https://api.huobi.pro'),
            ws_url=os.getenv('HTX_WS_URL', 'wss://api.huobi.pro/ws/v2')
        )

@dataclass
class GridConfig:
    """网格交易配置"""
    default_count: int = 10
    default_amount: float = 0.001
    min_profit_ratio: float = 0.002  # 最小利润率0.2%
    
    @classmethod
    def from_env(cls):
        return cls(
            default_count=int(os.getenv('GRID_DEFAULT_COUNT', 10)),
            default_amount=float(os.getenv('GRID_DEFAULT_AMOUNT', 0.001))
        )

@dataclass 
class MonitorConfig:
    """监控配置"""
    interval: int = 60  # 监控间隔（秒）
    price_alert_threshold: float = 0.05  # 价格预警阈值5%
    
    @classmethod
    def from_env(cls):
        return cls(
            interval=int(os.getenv('MONITOR_INTERVAL', 60)),
            price_alert_threshold=float(os.getenv('PRICE_ALERT_THRESHOLD', 0.05))
        )

@dataclass
class DatabaseConfig:
    """数据库配置"""
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    
    @classmethod
    def from_env(cls):
        return cls(
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379)),
            redis_db=int(os.getenv('REDIS_DB', 0))
        )

class Config:
    """全局配置管理"""
    
    def __init__(self):
        self.telegram = TelegramConfig.from_env()
        self.htx = HTXConfig.from_env()
        self.grid = GridConfig.from_env()
        self.monitor = MonitorConfig.from_env()
        self.database = DatabaseConfig.from_env()
        
        # 时区配置
        self.timezone = os.getenv('TIMEZONE', 'Asia/Shanghai')
        
        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/bot.log')
        
        # 交易对配置
        self.default_symbols = ['btcusdt', 'ethusdt', 'bnbusdt']
        
        # 验证配置
        self._validate()
    
    def _validate(self):
        """验证配置完整性"""
        if not self.telegram.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN 未配置")
        
        if not self.htx.access_key or not self.htx.secret_key:
            raise ValueError("HTX API密钥未配置")
    
    def save_user_settings(self, user_id: str, settings: dict):
        """保存用户设置"""
        settings_file = f'data/users/{user_id}_settings.json'
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def load_user_settings(self, user_id: str) -> dict:
        """加载用户设置"""
        settings_file = f'data/users/{user_id}_settings.json'
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                return json.load(f)
        
        # 返回默认设置
        return {
            'symbols': self.default_symbols,
            'grid_enabled': False,
            'monitor_enabled': True,
            'alert_settings': {
                'price_change': True,
                'order_filled': True,
                'grid_update': True
            }
        }

# 全局配置实例
config = Config()
