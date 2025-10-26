"""
AkShare数据获取实现
"""
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak
from loguru import logger

from .base_fetcher import BaseFetcher
from ..constants import SUPPORTED_INDICES


class AkShareFetcher(BaseFetcher):
    """AkShare数据获取器"""

    def __init__(self):
        """初始化"""
        super().__init__()
        logger.info("AkShareFetcher initialized")

    def get_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情数据

        Args:
            symbol: 指数代码 (如: sh000001)

        Returns:
            实时数据字典
        """
        if not self.validate_symbol(symbol):
            logger.error(f"Invalid symbol: {symbol}")
            return None

        try:
            # 获取实时行情
            df = ak.stock_zh_index_spot_em()

            # 根据symbol查找对应的指数
            index_info = SUPPORTED_INDICES.get(symbol)
            if not index_info:
                return None

            # 查找匹配的行
            index_name = index_info["name"]
            matched = df[df["名称"] == index_name]

            if matched.empty:
                logger.warning(f"No data found for {symbol}")
                return None

            row = matched.iloc[0]

            # 构造返回数据
            result = {
                "symbol": symbol,
                "name": index_name,
                "code": index_info["code"],
                "current": float(row["最新价"]),
                "change": float(row["涨跌额"]),
                "pct_change": float(row["涨跌幅"]),
                "open": float(row["今开"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "pre_close": float(row["昨收"]),
                "volume": float(row["成交量"]),
                "amount": float(row["成交额"]),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            logger.info(f"Fetched realtime data for {symbol}: {result['current']}")
            return result

        except Exception as e:
            logger.error(f"Error fetching realtime data for {symbol}: {e}")
            return None

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
        if not self.validate_symbol(symbol):
            logger.error(f"Invalid symbol: {symbol}")
            return None

        try:
            index_info = SUPPORTED_INDICES.get(symbol)
            if not index_info:
                return None

            # 获取指数代码
            code = index_info["code"]

            # 根据周期选择不同的接口
            if period == "daily":
                # 获取日线数据 - 使用东方财富接口
                df = ak.stock_zh_index_daily_em(symbol=symbol)
            elif period == "weekly":
                # 获取周线数据
                df = ak.stock_zh_index_daily_em(symbol=symbol)
                df = self._resample_to_weekly(df)
            elif period == "monthly":
                # 获取月线数据
                df = ak.stock_zh_index_daily_em(symbol=symbol)
                df = self._resample_to_monthly(df)
            else:
                logger.error(f"Unsupported period: {period}")
                return None

            if df is None or df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None

            # 重命名列
            df = df.rename(columns={
                "date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            })

            # 确保date列是datetime类型
            df["date"] = pd.to_datetime(df["date"])

            # 过滤日期范围
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df["date"] >= start) & (df["date"] <= end)]

            # 计算涨跌幅
            df["pct_change"] = df["close"].pct_change() * 100
            df["change"] = df["close"].diff()

            # 重置索引
            df = df.reset_index(drop=True)

            logger.info(f"Fetched {len(df)} records for {symbol} from {start_date} to {end_date}")
            return df

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None

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
        if not self.validate_symbol(symbol):
            logger.error(f"Invalid symbol: {symbol}")
            return None

        try:
            index_info = SUPPORTED_INDICES.get(symbol)
            if not index_info:
                return None

            code = index_info["code"]

            # 获取分时数据
            # 注意：akshare的分钟数据接口可能有限制，这里使用分时数据作为示例
            df = ak.stock_zh_index_daily_tx(symbol=code)

            if df is None or df.empty:
                logger.warning(f"No intraday data found for {symbol}")
                return None

            # 数据处理
            df = df.rename(columns={
                "date": "datetime",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            })

            df["datetime"] = pd.to_datetime(df["datetime"])

            # 根据period重采样
            if period != "1min":
                df = self._resample_intraday(df, period)

            logger.info(f"Fetched {len(df)} intraday records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None

    def _resample_to_weekly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将日线数据重采样为周线

        Args:
            df: 日线数据

        Returns:
            周线数据
        """
        df = df.set_index("date")
        weekly = df.resample("W").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        return weekly.reset_index()

    def _resample_to_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将日线数据重采样为月线

        Args:
            df: 日线数据

        Returns:
            月线数据
        """
        df = df.set_index("date")
        monthly = df.resample("M").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        return monthly.reset_index()

    def _resample_intraday(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        重采样分钟数据

        Args:
            df: 分钟数据
            period: 目标周期

        Returns:
            重采样后的数据
        """
        period_map = {
            "5min": "5T",
            "15min": "15T",
            "30min": "30T",
            "60min": "60T",
        }

        resample_rule = period_map.get(period, "5T")

        df = df.set_index("datetime")
        resampled = df.resample(resample_rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        return resampled.reset_index()

    def get_all_indices_realtime(self) -> Optional[pd.DataFrame]:
        """
        获取所有支持指数的实时数据

        Returns:
            所有指数的实时数据DataFrame
        """
        try:
            results = []
            for symbol in SUPPORTED_INDICES.keys():
                data = self.get_realtime_data(symbol)
                if data:
                    results.append(data)

            if results:
                df = pd.DataFrame(results)
                logger.info(f"Fetched realtime data for {len(results)} indices")
                return df

            return None

        except Exception as e:
            logger.error(f"Error fetching all indices realtime data: {e}")
            return None
