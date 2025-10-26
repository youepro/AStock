"""
数据分析器
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger


class DataAnalyzer:
    """数据分析器"""

    def __init__(self):
        """初始化"""
        logger.info("DataAnalyzer initialized")

    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算统计数据

        Args:
            df: 包含OHLCV数据的DataFrame

        Returns:
            统计数据字典
        """
        try:
            if df.empty:
                return {}

            stats = {
                "total_records": len(df),
                "date_range": {
                    "start": df["date"].min().strftime("%Y-%m-%d") if "date" in df.columns else None,
                    "end": df["date"].max().strftime("%Y-%m-%d") if "date" in df.columns else None,
                },
                "price": {
                    "current": float(df["close"].iloc[-1]),
                    "max": float(df["high"].max()),
                    "min": float(df["low"].min()),
                    "avg": float(df["close"].mean()),
                    "std": float(df["close"].std()),
                },
                "change": {
                    "total": float(df["close"].iloc[-1] - df["close"].iloc[0]),
                    "total_pct": float((df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100),
                    "avg_daily": float(df["pct_change"].mean()) if "pct_change" in df.columns else 0,
                    "max_gain": float(df["pct_change"].max()) if "pct_change" in df.columns else 0,
                    "max_loss": float(df["pct_change"].min()) if "pct_change" in df.columns else 0,
                },
                "volume": {
                    "total": float(df["volume"].sum()) if "volume" in df.columns else 0,
                    "avg": float(df["volume"].mean()) if "volume" in df.columns else 0,
                    "max": float(df["volume"].max()) if "volume" in df.columns else 0,
                },
            }

            # 计算涨跌天数
            if "pct_change" in df.columns:
                up_days = len(df[df["pct_change"] > 0])
                down_days = len(df[df["pct_change"] < 0])
                stats["change"]["up_days"] = up_days
                stats["change"]["down_days"] = down_days
                stats["change"]["up_ratio"] = up_days / len(df) if len(df) > 0 else 0

            logger.info("Calculated statistics")
            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def calculate_volatility(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        计算波动率

        Args:
            df: 包含收盘价的DataFrame
            window: 计算窗口

        Returns:
            波动率数据
        """
        try:
            if df.empty or len(df) < window:
                return {}

            # 计算收益率
            returns = df["close"].pct_change()

            # 历史波动率（年化）
            historical_vol = returns.std() * np.sqrt(252) * 100

            # 滚动波动率
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100

            volatility = {
                "historical": float(historical_vol),
                "current": float(rolling_vol.iloc[-1]) if not rolling_vol.empty else 0,
                "max": float(rolling_vol.max()) if not rolling_vol.empty else 0,
                "min": float(rolling_vol.min()) if not rolling_vol.empty else 0,
                "avg": float(rolling_vol.mean()) if not rolling_vol.empty else 0,
            }

            logger.info("Calculated volatility")
            return volatility

        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return {}

    def find_consecutive_days(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        查找连涨连跌天数

        Args:
            df: 包含涨跌幅的DataFrame

        Returns:
            连涨连跌数据
        """
        try:
            if df.empty or "pct_change" not in df.columns:
                return

            # 当前连续状态
            current_streak = 0
            current_type = None

            # 最大连涨
            max_up_streak = 0
            max_up_start = None
            max_up_end = None

            # 最大连跌
            max_down_streak = 0
            max_down_start = None
            max_down_end = None

            # 临时变量
            temp_streak = 0
            temp_start = None

            for i, row in df.iterrows():
                pct_change = row.get("pct_change", 0)
                date = row.get("date")

                if pd.isna(pct_change):
                    continue

                if pct_change > 0:
                    if temp_streak > 0:
                        temp_streak += 1
                    else:
                        temp_streak = 1
                        temp_start = date

                    if temp_streak > max_up_streak:
                        max_up_streak = temp_streak
                        max_up_start = temp_start
                        max_up_end = date

                    if i == len(df) - 1:
                        current_streak = temp_streak
                        current_type = "up"

                elif pct_change < 0:
                    if temp_streak < 0:
                        temp_streak -= 1
                    else:
                        temp_streak = -1
                        temp_start = date

                    if abs(temp_streak) > max_down_streak:
                        max_down_streak = abs(temp_streak)
                        max_down_start = temp_start
                        max_down_end = date

                    if i == len(df) - 1:
                        current_streak = abs(temp_streak)
                        current_type = "down"
                else:
                    temp_streak = 0

            result = {
                "current": {
                    "type": current_type,
                    "days": current_streak,
                },
                "max_up": {
                    "days": max_up_streak,
                    "start": max_up_start.strftime("%Y-%m-%d") if max_up_start else None,
                    "end": max_up_end.strftime("%Y-%m-%d") if max_up_end else None,
                },
                "max_down": {
                    "days": max_down_streak,
                    "start": max_down_start.strftime("%Y-%m-%d") if max_down_start else None,
                    "end": max_down_end.strftime("%Y-%m-%d") if max_down_end else None,
                },
            }

            logger.info("Found consecutive days")
            return result

        except Exception as e:
            logger.error(f"Error finding consecutive days: {e}")
            return {}

    def compare_indices(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        对比多个指数

        Args:
            data_dict: 指数数据字典 {symbol: DataFrame}

        Returns:
            对比结果
        """
        try:
            if not data_dict:
                return {}

            comparison = {}

            for symbol, df in data_dict.items():
                if df.empty:
                    continue

                comparison[symbol] = {
                    "current": float(df["close"].iloc[-1]),
                    "change": float(df["close"].iloc[-1] - df["close"].iloc[0]),
                    "pct_change": float((df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100),
                    "high": float(df["high"].max()),
                    "low": float(df["low"].min()),
                    "avg_volume": float(df["volume"].mean()) if "volume" in df.columns else 0,
                }

            # 排序
            sorted_by_change = sorted(
                comparison.items(),
                key=lambda x: x[1]["pct_change"],
                reverse=True
            )

            result = {
                "comparison": comparison,
                "ranking": {
                    "by_change": [{"symbol": k, **v} for k, v in sorted_by_change],
                },
            }

            logger.info(f"Compared {len(data_dict)} indices")
            return result

        except Exception as e:
            logger.error(f"Error comparing indices: {e}")
            return {}

    def calculate_correlation(self, df1: pd.DataFrame, df2: pd.DataFrame) -> float:
        """
        计算两个指数的相关性

        Args:
            df1: 第一个指数数据
            df2: 第二个指数数据

        Returns:
            相关系数
        """
        try:
            if df1.empty or df2.empty:
                return 0.0

            # 确保日期对齐
            merged = pd.merge(
                df1[["date", "close"]],
                df2[["date", "close"]],
                on="date",
                suffixes=("_1", "_2")
            )

            if len(merged) < 2:
                return 0.0

            # 计算相关系数
            correlation = merged["close_1"].corr(merged["close_2"])

            logger.info(f"Calculated correlation: {correlation:.4f}")
            return float(correlation)

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return 0.0

    def detect_support_resistance(
        self,
        df: pd.DataFrame,
        window: int = 20,
        num_levels: int = 3
    ) -> Dict[str, List[float]]:
        """
        检测支撑位和阻力位

        Args:
            df: 包含OHLC数据的DataFrame
            window: 检测窗口
            num_levels: 返回的支撑/阻力位数量

        Returns:
            支撑位和阻力位
        """
        try:
            if df.empty or len(df) < window:
                return {"support": [], "resistance": []}

            # 找局部最高点和最低点
            highs = []
            lows = []

            for i in range(window, len(df) - window):
                # 检查是否是局部最高点
                if df["high"].iloc[i] == df["high"].iloc[i-window:i+window+1].max():
                    highs.append(df["high"].iloc[i])

                # 检查是否是局部最低点
                if df["low"].iloc[i] == df["low"].iloc[i-window:i+window+1].min():
                    lows.append(df["low"].iloc[i])

            # 聚类相近的价格水平
            def cluster_levels(levels, tolerance=0.02):
                if not levels:
                    return []

                levels = sorted(levels)
                clusters = []
                current_cluster = [levels[0]]

                for level in levels[1:]:
                    if (level - current_cluster[-1]) / current_cluster[-1] < tolerance:
                        current_cluster.append(level)
                    else:
                        clusters.append(np.mean(current_cluster))
                        current_cluster = [level]

                clusters.append(np.mean(current_cluster))
                return clusters

            resistance_levels = cluster_levels(highs)
            support_levels = cluster_levels(lows)

            # 返回最近的几个水平
            result = {
                "resistance": [float(x) for x in sorted(resistance_levels, reverse=True)[:num_levels]],
                "support": [float(x) for x in sorted(support_levels, reverse=True)[:num_levels]],
            }

            logger.info(f"Detected {len(result['resistance'])} resistance and {len(result['support'])} support levels")
            return result

        except Exception as e:
            logger.error(f"Error detecting support/resistance: {e}")
            return {"support": [], "resistance": []}

    def analyze_volume_price(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        量价关系分析

        Args:
            df: 包含价格和成交量的DataFrame

        Returns:
            量价分析结果
        """
        try:
            if df.empty or "volume" not in df.columns:
                return {}

            # 计算价格和成交量的变化
            df_copy = df.copy()
            df_copy["price_change"] = df_copy["close"].pct_change()
            df_copy["volume_change"] = df_copy["volume"].pct_change()

            # 分类量价关系
            volume_price_patterns = {
                "price_up_volume_up": 0,    # 价涨量增
                "price_up_volume_down": 0,  # 价涨量缩
                "price_down_volume_up": 0,  # 价跌量增
                "price_down_volume_down": 0, # 价跌量缩
            }

            for _, row in df_copy.iterrows():
                price_change = row.get("price_change", 0)
                volume_change = row.get("volume_change", 0)

                if pd.isna(price_change) or pd.isna(volume_change):
                    continue

                if price_change > 0 and volume_change > 0:
                    volume_price_patterns["price_up_volume_up"] += 1
                elif price_change > 0 and volume_change < 0:
                    volume_price_patterns["price_up_volume_down"] += 1
                elif price_change < 0 and volume_change > 0:
                    volume_price_patterns["price_down_volume_up"] += 1
                elif price_change < 0 and volume_change < 0:
                    volume_price_patterns["price_down_volume_down"] += 1

            # 计算成交量异常
            avg_volume = df["volume"].mean()
            std_volume = df["volume"].std()
            latest_volume = df["volume"].iloc[-1]

            volume_status = "normal"
            if latest_volume > avg_volume + 2 * std_volume:
                volume_status = "extremely_high"
            elif latest_volume > avg_volume + std_volume:
                volume_status = "high"
            elif latest_volume < avg_volume - std_volume:
                volume_status = "low"

            result = {
                "patterns": volume_price_patterns,
                "volume_status": volume_status,
                "latest_volume": float(latest_volume),
                "avg_volume": float(avg_volume),
                "volume_ratio": float(latest_volume / avg_volume) if avg_volume > 0 else 0,
            }

            logger.info("Analyzed volume-price relationship")
            return result

        except Exception as e:
            logger.error(f"Error analyzing volume-price: {e}")
            return {}

    def generate_summary(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成综合分析摘要

        Args:
            df: 历史数据
            indicators: 技术指标

        Returns:
            分析摘要
        """
        try:
            summary = {
                "statistics": self.calculate_statistics(df),
                "volatility": self.calculate_volatility(df),
                "consecutive_days": self.find_consecutive_days(df),
                "support_resistance": self.detect_support_resistance(df),
                "volume_price": self.analyze_volume_price(df),
                "indicators": indicators,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            logger.info("Generated analysis summary")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
