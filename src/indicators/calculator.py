"""
技术指标计算器
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from loguru import logger


class IndicatorCalculator:
    """技术指标计算器"""

    def __init__(self):
        """初始化"""
        logger.info("IndicatorCalculator initialized")

    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算移动平均线

        Args:
            df: 包含close列的DataFrame
            periods: MA周期列表

        Returns:
            添加了MA列的DataFrame
        """
        if periods is None:
            periods = [5, 10, 20, 30, 60, 120, 250]

        try:
            result = df.copy()
            for period in periods:
                if len(df) >= period:
                    result[f"MA{period}"] = df["close"].rolling(window=period).mean()
                else:
                    logger.warning(f"Not enough data for MA{period}")

            logger.info(f"Calculated MA for periods: {periods}")
            return result

        except Exception as e:
            logger.error(f"Error calculating MA: {e}")
            return df

    def calculate_ema(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算指数移动平均线

        Args:
            df: 包含close列的DataFrame
            periods: EMA周期列表

        Returns:
            添加了EMA列的DataFrame
        """
        if periods is None:
            periods = [12, 26]

        try:
            result = df.copy()
            for period in periods:
                if len(df) >= period:
                    result[f"EMA{period}"] = df["close"].ewm(span=period, adjust=False).mean()
                else:
                    logger.warning(f"Not enough data for EMA{period}")

            logger.info(f"Calculated EMA for periods: {periods}")
            return result

        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return df

    def calculate_boll(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_multiplier: float = 2.0
    ) -> pd.DataFrame:
        """
        计算布林带

        Args:
            df: 包含close列的DataFrame
            period: 周期
            std_multiplier: 标准差倍数

        Returns:
            添加了BOLL列的DataFrame
        """
        try:
            result = df.copy()

            if len(df) >= period:
                # 中轨
                result["BOLL_MID"] = df["close"].rolling(window=period).mean()
                # 标准差
                std = df["close"].rolling(window=period).std()
                # 上轨
                result["BOLL_UPPER"] = result["BOLL_MID"] + std_multiplier * std
                # 下轨
                result["BOLL_LOWER"] = result["BOLL_MID"] - std_multiplier * std

                logger.info(f"Calculated BOLL with period={period}, std={std_multiplier}")
            else:
                logger.warning(f"Not enough data for BOLL")

            return result

        except Exception as e:
            logger.error(f"Error calculating BOLL: {e}")
            return df

    def calculate_rsi(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算相对强弱指标

        Args:
            df: 包含close列的DataFrame
            periods: RSI周期列表

        Returns:
            添加了RSI列的DataFrame
        """
        if periods is None:
            periods = [6, 12, 24]

        try:
            result = df.copy()

            for period in periods:
                if len(df) >= period + 1:
                    # 计算价格变化
                    delta = df["close"].diff()

                    # 分离上涨和下跌
                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)

                    # 计算平均涨跌
                    avg_gain = gain.rolling(window=period).mean()
                    avg_loss = loss.rolling(window=period).mean()

                    # 计算RS和RSI
                    rs = avg_gain / avg_loss
                    result[f"RSI{period}"] = 100 - (100 / (1 + rs))
                else:
                    logger.warning(f"Not enough data for RSI{period}")

            logger.info(f"Calculated RSI for periods: {periods}")
            return result

        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return df

    def calculate_kdj(
        self,
        df: pd.DataFrame,
        fastk_period: int = 9,
        slowk_period: int = 3,
        slowd_period: int = 3
    ) -> pd.DataFrame:
        """
        计算KDJ指标

        Args:
            df: 包含high, low, close列的DataFrame
            fastk_period: FastK周期
            slowk_period: SlowK周期
            slowd_period: SlowD周期

        Returns:
            添加了KDJ列的DataFrame
        """
        try:
            result = df.copy()

            if len(df) >= fastk_period:
                # 计算RSV (未成熟随机值)
                low_min = df["low"].rolling(window=fastk_period).min()
                high_max = df["high"].rolling(window=fastk_period).max()
                rsv = (df["close"] - low_min) / (high_max - low_min) * 100

                # 计算K值
                result["K"] = rsv.ewm(alpha=1/slowk_period, adjust=False).mean()

                # 计算D值
                result["D"] = result["K"].ewm(alpha=1/slowd_period, adjust=False).mean()

                # 计算J值
                result["J"] = 3 * result["K"] - 2 * result["D"]

                logger.info(f"Calculated KDJ")
            else:
                logger.warning(f"Not enough data for KDJ")

            return result

        except Exception as e:
            logger.error(f"Error calculating KDJ: {e}")
            return df

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: 包含close列的DataFrame
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期

        Returns:
            添加了MACD列的DataFrame
        """
        try:
            result = df.copy()

            if len(df) >= slow_period:
                # 计算快线和慢线
                ema_fast = df["close"].ewm(span=fast_period, adjust=False).mean()
                ema_slow = df["close"].ewm(span=slow_period, adjust=False).mean()

                # 计算DIF (MACD线)
                result["MACD_DIF"] = ema_fast - ema_slow

                # 计算DEA (信号线)
                result["MACD_DEA"] = result["MACD_DIF"].ewm(span=signal_period, adjust=False).mean()

                # 计算MACD柱
                result["MACD_HIST"] = (result["MACD_DIF"] - result["MACD_DEA"]) * 2

                logger.info(f"Calculated MACD")
            else:
                logger.warning(f"Not enough data for MACD")

            return result

        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return df

    def calculate_volume_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算成交量移动平均线

        Args:
            df: 包含volume列的DataFrame
            periods: 周期列表

        Returns:
            添加了VOL_MA列的DataFrame
        """
        if periods is None:
            periods = [5, 10, 20]

        try:
            result = df.copy()

            for period in periods:
                if len(df) >= period:
                    result[f"VOL_MA{period}"] = df["volume"].rolling(window=period).mean()
                else:
                    logger.warning(f"Not enough data for VOL_MA{period}")

            logger.info(f"Calculated VOL_MA for periods: {periods}")
            return result

        except Exception as e:
            logger.error(f"Error calculating VOL_MA: {e}")
            return df

    def calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算能量潮指标

        Args:
            df: 包含close和volume列的DataFrame

        Returns:
            添加了OBV列的DataFrame
        """
        try:
            result = df.copy()

            if len(df) > 1:
                # 计算价格变化方向
                price_change = df["close"].diff()

                # 根据价格变化方向累加成交量
                obv = []
                obv_value = 0

                for i in range(len(df)):
                    if i == 0:
                        obv.append(df["volume"].iloc[i])
                        obv_value = df["volume"].iloc[i]
                    else:
                        if price_change.iloc[i] > 0:
                            obv_value += df["volume"].iloc[i]
                        elif price_change.iloc[i] < 0:
                            obv_value -= df["volume"].iloc[i]
                        obv.append(obv_value)

                result["OBV"] = obv
                logger.info(f"Calculated OBV")
            else:
                logger.warning(f"Not enough data for OBV")

            return result

        except Exception as e:
            logger.error(f"Error calculating OBV: {e}")
            return df

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用技术指标

        Args:
            df: 包含OHLCV数据的DataFrame

        Returns:
            添加了所有指标的DataFrame
        """
        try:
            result = df.copy()

            # 趋势指标
            result = self.calculate_ma(result)
            result = self.calculate_ema(result)
            result = self.calculate_boll(result)

            # 动量指标
            result = self.calculate_rsi(result)
            result = self.calculate_kdj(result)
            result = self.calculate_macd(result)

            # 成交量指标
            result = self.calculate_volume_ma(result)
            result = self.calculate_obv(result)

            logger.info("Calculated all indicators")
            return result

        except Exception as e:
            logger.error(f"Error calculating all indicators: {e}")
            return df

    def get_latest_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取最新的技术指标信号

        Args:
            df: 包含技术指标的DataFrame

        Returns:
            信号字典
        """
        try:
            if df.empty or len(df) < 2:
                return {}

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            signals = {
                "price": {
                    "current": float(latest["close"]),
                    "change": float(latest.get("change", 0)),
                    "pct_change": float(latest.get("pct_change", 0)),
                },
                "ma": {},
                "macd": {},
                "kdj": {},
                "rsi": {},
            }

            # MA信号
            for col in df.columns:
                if col.startswith("MA"):
                    ma_value = latest.get(col)
                    if pd.notna(ma_value):
                        signals["ma"][col] = {
                            "value": float(ma_value),
                            "position": "above" if latest["close"] > ma_value else "below"
                        }

            # MACD信号
            if "MACD_DIF" in df.columns and "MACD_DEA" in df.columns:
                macd_dif = latest.get("MACD_DIF")
                macd_dea = latest.get("MACD_DEA")
                prev_dif = previous.get("MACD_DIF")
                prev_dea = previous.get("MACD_DEA")

                if all(pd.notna([macd_dif, macd_dea, prev_dif, prev_dea])):
                    signals["macd"] = {
                        "dif": float(macd_dif),
                        "dea": float(macd_dea),
                        "hist": float(latest.get("MACD_HIST", 0)),
                        "golden_cross": prev_dif <= prev_dea and macd_dif > macd_dea,
                        "death_cross": prev_dif >= prev_dea and macd_dif < macd_dea,
                    }

            # KDJ信号
            if all(col in df.columns for col in ["K", "D", "J"]):
                k_value = latest.get("K")
                d_value = latest.get("D")
                j_value = latest.get("J")

                if all(pd.notna([k_value, d_value, j_value])):
                    signals["kdj"] = {
                        "k": float(k_value),
                        "d": float(d_value),
                        "j": float(j_value),
                        "overbought": k_value > 80 and d_value > 80,
                        "oversold": k_value < 20 and d_value < 20,
                    }

            # RSI信号
            for col in df.columns:
                if col.startswith("RSI"):
                    rsi_value = latest.get(col)
                    if pd.notna(rsi_value):
                        signals["rsi"][col] = {
                            "value": float(rsi_value),
                            "overbought": rsi_value > 70,
                            "oversold": rsi_value < 30,
                        }

            return signals

        except Exception as e:
            logger.error(f"Error getting latest signals: {e}")
            return {}
