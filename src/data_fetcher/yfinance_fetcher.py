"""
YFinance数据获取实现（Yahoo Finance）
"""
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

try:
    import yfinance as yf
except ImportError:
    yf = None
    logger.warning("yfinance not installed, please run: pip install yfinance")

from .base_fetcher import BaseFetcher
from ..constants import SUPPORTED_INDICES


class YFinanceFetcher(BaseFetcher):
    """YFinance数据获取器"""

    # 指数代码映射（Yahoo Finance格式）
    INDEX_CODE_MAP = {
        "sh000001": "000001.SS",  # 上证指数
        "sz399001": "399001.SZ",  # 深证成指
        "sz399006": "399006.SZ",  # 创业板指
        "sh000016": "000016.SS",  # 上证50
        "sh000300": "000300.SS",  # 沪深300
        "sh000905": "000905.SS",  # 中证500
        "sh000852": "000852.SS",  # 中证1000
        "sz399005": "399005.SZ",  # 中小板指
        "sz399102": "399102.SZ",  # 创业板综
        "sh000688": "000688.SS",  # 科创50
    }

    def __init__(self):
        """初始化"""
        super().__init__()
        if yf is None:
            raise ImportError("yfinance not installed, please run: pip install yfinance")
        logger.info("YFinanceFetcher initialized")

    def _get_yf_code(self, symbol: str) -> Optional[str]:
        """
        获取Yahoo Finance格式的代码

        Args:
            symbol: 标准指数代码

        Returns:
            Yahoo Finance格式代码
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
            yf_code = self._get_yf_code(symbol)
            if not yf_code:
                logger.error(f"No YFinance code mapping for {symbol}")
                return None

            # 获取实时数据
            ticker = yf.Ticker(yf_code)
            info = ticker.info

            # 获取最新的历史数据（包含今日数据）
            hist = ticker.history(period="1d")

            if hist.empty:
                logger.warning(f"No realtime data found for {symbol}")
                return None

            latest = hist.iloc[-1]
            index_info = SUPPORTED_INDICES.get(symbol)

            # 计算涨跌幅
            current_price = float(latest['Close'])
            pre_close = float(latest['Open']) if 'Open' in latest else current_price
            change = current_price - pre_close
            pct_change = (change / pre_close * 100) if pre_close != 0 else 0

            # 构造返回数据
            result = {
                "symbol": symbol,
                "name": index_info["name"],
                "code": index_info["code"],
                "current": current_price,
                "change": change,
                "pct_change": pct_change,
                "open": float(latest['Open']),
                "high": float(latest['High']),
                "low": float(latest['Low']),
                "pre_close": pre_close,
                "volume": float(latest['Volume']),
                "amount": float(latest['Volume']) * current_price,  # 估算成交额
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
            yf_code = self._get_yf_code(symbol)
            if not yf_code:
                logger.error(f"No YFinance code mapping for {symbol}")
                return None

            # 获取数据
            ticker = yf.Ticker(yf_code)

            # 根据周期设置interval
            interval_map = {
                "daily": "1d",
                "weekly": "1wk",
                "monthly": "1mo"
            }
            interval = interval_map.get(period, "1d")

            # 下载历史数据
            df = ticker.history(start=start_date, end=end_date, interval=interval)

            if df is None or df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None

            # 重置索引，将日期作为列
            df = df.reset_index()

            # 重命名列
            df = df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })

            # 选择需要的列
            columns = ["date", "open", "high", "low", "close", "volume"]
            df = df[columns]

            # 确保date列是datetime类型
            df["date"] = pd.to_datetime(df["date"])

            # 计算涨跌幅和涨跌额
            df["pct_change"] = df["close"].pct_change() * 100
            df["change"] = df["close"].diff()

            # 添加成交额（估算）
            df["amount"] = df["volume"] * df["close"]

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
            yf_code = self._get_yf_code(symbol)
            if not yf_code:
                logger.error(f"No YFinance code mapping for {symbol}")
                return None

            # 周期映射
            period_map = {
                "1min": "1m",
                "5min": "5m",
                "15min": "15m",
                "30min": "30m",
                "60min": "60m",
            }

            interval = period_map.get(period, "5m")

            # 获取分钟数据（最近7天）
            ticker = yf.Ticker(yf_code)
            df = ticker.history(period="7d", interval=interval)

            if df is None or df.empty:
                logger.warning(f"No intraday data found for {symbol}")
                return None

            # 重置索引
            df = df.reset_index()

            # 重命名列
            df = df.rename(columns={
                "Datetime": "datetime",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
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

            if results:
                df = pd.DataFrame(results)
                logger.info(f"Fetched realtime data for {len(results)} indices")
                return df

            return None

        except Exception as e:
            logger.error(f"Error fetching all indices realtime data: {e}")
            return None
