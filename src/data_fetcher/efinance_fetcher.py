"""
EFinance数据获取实现（东方财富）
"""
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import time

try:
    import efinance as ef
except ImportError:
    ef = None
    logger.warning("efinance not installed, please run: pip install efinance")

from .base_fetcher import BaseFetcher
from ..constants import SUPPORTED_INDICES


class EFinanceFetcher(BaseFetcher):
    """EFinance数据获取器"""

    # 指数代码映射（东方财富格式）
    INDEX_CODE_MAP = {
        "sh000001": "000001",  # 上证指数
        "sz399001": "399001",  # 深证成指
        "sz399006": "399006",  # 创业板指
        "sh000016": "000016",  # 上证50
        "sh000300": "000300",  # 沪深300
        "sh000905": "000905",  # 中证500
        "sh000852": "000852",  # 中证1000
        "sz399005": "399005",  # 中小板指
        "sz399102": "399102",  # 创业板综
        "sh000688": "000688",  # 科创50
    }

    def __init__(self):
        """初始化"""
        super().__init__()
        if ef is None:
            raise ImportError("efinance not installed, please run: pip install efinance")
        logger.info("EFinanceFetcher initialized")

    def _get_ef_code(self, symbol: str) -> Optional[str]:
        """
        获取东方财富格式的代码

        Args:
            symbol: 标准指数代码

        Returns:
            东方财富格式代码
        """
        return self.INDEX_CODE_MAP.get(symbol)

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
            ef_code = self._get_ef_code(symbol)
            if not ef_code:
                logger.error(f"No EFinance code mapping for {symbol}")
                return None

            # 获取实时行情
            df = ef.stock.get_realtime_quotes([ef_code])

            if df is None or df.empty:
                logger.warning(f"No realtime data found for {symbol}")
                return None

            row = df.iloc[0]
            index_info = SUPPORTED_INDICES.get(symbol)

            # 构造返回数据
            result = {
                "symbol": symbol,
                "name": index_info["name"],
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
            ef_code = self._get_ef_code(symbol)
            if not ef_code:
                logger.error(f"No EFinance code mapping for {symbol}")
                return None

            # 转换日期格式
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")

            # 获取K线数据
            df = ef.stock.get_quote_history(
                ef_code,
                beg=start,
                end=end,
                klt=101 if period == "daily" else (102 if period == "weekly" else 103)
            )

            if df is None or df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None

            # 重命名列
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "涨跌幅": "pct_change",
                "涨跌额": "change",
            })

            # 选择需要的列
            columns = ["date", "open", "high", "low", "close", "volume"]
            if "amount" in df.columns:
                columns.append("amount")

            df = df[columns]

            # 确保date列是datetime类型
            df["date"] = pd.to_datetime(df["date"])

            # 计算涨跌幅和涨跌额（如果不存在）
            if "pct_change" not in df.columns:
                df["pct_change"] = df["close"].pct_change() * 100
            if "change" not in df.columns:
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
            ef_code = self._get_ef_code(symbol)
            if not ef_code:
                logger.error(f"No EFinance code mapping for {symbol}")
                return None

            # 周期映射
            period_map = {
                "1min": 1,
                "5min": 5,
                "15min": 15,
                "30min": 30,
                "60min": 60,
            }

            klt = period_map.get(period, 5)

            # 获取分钟数据
            df = ef.stock.get_quote_history(ef_code, klt=klt)

            if df is None or df.empty:
                logger.warning(f"No intraday data found for {symbol}")
                return None

            # 重命名列
            df = df.rename(columns={
                "日期": "datetime",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            })

            df["datetime"] = pd.to_datetime(df["datetime"])

            logger.info(f"Fetched {len(df)} intraday records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None

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
                # 添加小延迟避免请求过快
                time.sleep(0.1)

            if results:
                df = pd.DataFrame(results)
                logger.info(f"Fetched realtime data for {len(results)} indices")
                return df

            return None

        except Exception as e:
            logger.error(f"Error fetching all indices realtime data: {e}")
            return None
