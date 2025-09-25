"""
日志管理模块
提供统一的日志记录功能
"""

import os
import sys
from loguru import logger
from config.config import config

class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.setup_logger()
    
    def setup_logger(self):
        """配置日志"""
        # 移除默认处理器
        logger.remove()
        
        # 确保日志目录存在
        log_dir = os.path.dirname(config.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 添加控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=config.log_level,
            colorize=True
        )
        
        # 添加文件输出
        logger.add(
            config.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=config.log_level,
            rotation="10 MB",  # 文件大小达到10MB时轮转
            retention="7 days",  # 保留7天
            compression="zip",  # 压缩归档
            encoding="utf-8"
        )
        
        # 添加错误日志单独记录
        logger.add(
            "logs/error.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="5 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )
        
        # 添加交易日志
        logger.add(
            "logs/trading.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "trading" in record["extra"],
            rotation="daily",
            retention="30 days",
            encoding="utf-8"
        )
        
    def get_logger(self, name: str = None):
        """获取日志实例"""
        if name:
            return logger.bind(name=name)
        return logger

# 创建全局日志管理器
log_manager = LogManager()

# 导出logger实例
logger = log_manager.get_logger()

# 特定模块日志器
def get_module_logger(module_name: str):
    """获取模块专用日志器"""
    return logger.bind(module=module_name)

# 交易日志器
trading_logger = logger.bind(trading=True)
