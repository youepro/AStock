"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""

    # 应用配置
    APP_NAME: str = "A股指数分析系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/stock_index.db"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 数据源配置
    DATA_SOURCE: str = "akshare"
    DATA_UPDATE_INTERVAL: int = 5  # 秒

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # Tushare配置
    TUSHARE_TOKEN: Optional[str] = None

    # 预警配置
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_HOST: Optional[str] = None
    ALERT_EMAIL_PORT: int = 587
    ALERT_EMAIL_USER: Optional[str] = None
    ALERT_EMAIL_PASSWORD: Optional[str] = None
    ALERT_EMAIL_TO: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
