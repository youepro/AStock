"""
数据获取基类
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime


class BaseFetcher(ABC):
    """数据获取基类"""

    def __init__(self):
        """初始化"""
        self.name = self.__class__.__name__

    @abstractmethod
    def get_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情数据

        Args:
            symbol: 指数代码

        Returns:
            实时数据字典
        """
        pass

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """
        获取历史数据

        Args:
            symbol: 指数代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 时间周期 (daily, weekly, monthly)

        Returns:
            历史数据DataFrame
        """
        pass

    @abstractmethod
    def get_intraday_data(
        self,
        symbol: str,
        period: str = "5min"
    ) -> Optional[pd.DataFrame]:
        """
        获取分钟级数据

        Args:
            symbol: 指数代码
            period: 时间周期 (1min, 5min, 15min, 30min, 60min)

        Returns:
            分钟数据DataFrame
        """
        pass

    def validate_symbol(self, symbol: str) -> bool:
        """
        验证指数代码是否有效

        Args:
            symbol: 指数代码

        Returns:
            是否有效
        """
        from ..constants import SUPPORTED_INDICES
        return symbol in SUPPORTED_INDICES

    def format_date(self, date_str: str) -> str:
        """
        格式化日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            格式化后的日期字符串
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y%m%d")
        except ValueError:
            return date_str
