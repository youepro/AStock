"""
数据库存储模块
"""
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List
from loguru import logger

from config import settings

Base = declarative_base()


class IndexData(Base):
    """指数数据表"""
    __tablename__ = "index_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    change = Column(Float)
    pct_change = Column(Float)
    period = Column(String(20), default="daily")
    created_at = Column(DateTime, default=datetime.now)


class RealtimeData(Base):
    """实时数据表"""
    __tablename__ = "realtime_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(50))
    current = Column(Float)
    change = Column(Float)
    pct_change = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    pre_close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)


class AlertRule(Base):
    """预警规则表"""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False)
    condition = Column(Text)
    threshold = Column(Float)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Database:
    """数据库管理类"""

    def __init__(self, db_url: str = None):
        """
        初始化数据库连接

        Args:
            db_url: 数据库连接URL
        """
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

        # 创建表
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized: {self.db_url}")

    def save_historical_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        period: str = "daily"
    ) -> bool:
        """
        保存历史数据

        Args:
            symbol: 指数代码
            df: 历史数据DataFrame
            period: 时间周期

        Returns:
            是否成功
        """
        try:
            session = self.Session()

            for _, row in df.iterrows():
                # 检查是否已存在
                existing = session.query(IndexData).filter_by(
                    symbol=symbol,
                    date=row["date"],
                    period=period
                ).first()

                if existing:
                    # 更新
                    existing.open = float(row.get("open", 0))
                    existing.high = float(row.get("high", 0))
                    existing.low = float(row.get("low", 0))
                    existing.close = float(row.get("close", 0))
                    existing.volume = float(row.get("volume", 0))
                    existing.amount = float(row.get("amount", 0))
                    existing.change = float(row.get("change", 0))
                    existing.pct_change = float(row.get("pct_change", 0))
                else:
                    # 插入
                    data = IndexData(
                        symbol=symbol,
                        date=row["date"],
                        open=float(row.get("open", 0)),
                        high=float(row.get("high", 0)),
                        low=float(row.get("low", 0)),
                        close=float(row.get("close", 0)),
                        volume=float(row.get("volume", 0)),
                        amount=float(row.get("amount", 0)),
                        change=float(row.get("change", 0)),
                        pct_change=float(row.get("pct_change", 0)),
                        period=period
                    )
                    session.add(data)

            session.commit()
            session.close()

            logger.info(f"Saved {len(df)} records for {symbol} ({period})")
            return True

        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
            session.rollback()
            session.close()
            return False

    def get_historical_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """
        获取历史数据

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            period: 时间周期

        Returns:
            历史数据DataFrame
        """
        try:
            session = self.Session()

            query = session.query(IndexData).filter_by(symbol=symbol, period=period)

            if start_date:
                query = query.filter(IndexData.date >= start_date)
            if end_date:
                query = query.filter(IndexData.date <= end_date)

            query = query.order_by(IndexData.date)

            results = query.all()
            session.close()

            if not results:
                return None

            # 转换为DataFrame
            data = []
            for r in results:
                data.append({
                    "date": r.date,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                    "amount": r.amount,
                    "change": r.change,
                    "pct_change": r.pct_change,
                })

            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} records for {symbol} ({period})")
            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def save_realtime_data(self, data: dict) -> bool:
        """
        保存实时数据

        Args:
            data: 实时数据字典

        Returns:
            是否成功
        """
        try:
            session = self.Session()

            realtime = RealtimeData(
                symbol=data.get("symbol"),
                name=data.get("name"),
                current=data.get("current"),
                change=data.get("change"),
                pct_change=data.get("pct_change"),
                open=data.get("open"),
                high=data.get("high"),
                low=data.get("low"),
                pre_close=data.get("pre_close"),
                volume=data.get("volume"),
                amount=data.get("amount"),
                timestamp=datetime.strptime(data.get("timestamp"), "%Y-%m-%d %H:%M:%S")
            )

            session.add(realtime)
            session.commit()
            session.close()

            logger.info(f"Saved realtime data for {data.get('symbol')}")
            return True

        except Exception as e:
            logger.error(f"Error saving realtime data: {e}")
            session.rollback()
            session.close()
            return False

    def get_latest_realtime_data(self, symbol: str) -> Optional[dict]:
        """
        获取最新实时数据

        Args:
            symbol: 指数代码

        Returns:
            实时数据字典
        """
        try:
            session = self.Session()

            result = session.query(RealtimeData).filter_by(
                symbol=symbol
            ).order_by(RealtimeData.timestamp.desc()).first()

            session.close()

            if not result:
                return None

            data = {
                "symbol": result.symbol,
                "name": result.name,
                "current": result.current,
                "change": result.change,
                "pct_change": result.pct_change,
                "open": result.open,
                "high": result.high,
                "low": result.low,
                "pre_close": result.pre_close,
                "volume": result.volume,
                "amount": result.amount,
                "timestamp": result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }

            return data

        except Exception as e:
            logger.error(f"Error getting latest realtime data: {e}")
            return None

    def save_alert_rule(self, rule: dict) -> bool:
        """
        保存预警规则

        Args:
            rule: 预警规则字典

        Returns:
            是否成功
        """
        try:
            session = self.Session()

            alert = AlertRule(
                symbol=rule.get("symbol"),
                rule_type=rule.get("rule_type"),
                condition=rule.get("condition"),
                threshold=rule.get("threshold"),
                enabled=rule.get("enabled", 1)
            )

            session.add(alert)
            session.commit()
            session.close()

            logger.info(f"Saved alert rule for {rule.get('symbol')}")
            return True

        except Exception as e:
            logger.error(f"Error saving alert rule: {e}")
            session.rollback()
            session.close()
            return False

    def get_alert_rules(self, symbol: str = None, enabled_only: bool = True) -> List[dict]:
        """
        获取预警规则

        Args:
            symbol: 指数代码（可选）
            enabled_only: 只获取启用的规则

        Returns:
            预警规则列表
        """
        try:
            session = self.Session()

            query = session.query(AlertRule)

            if symbol:
                query = query.filter_by(symbol=symbol)
            if enabled_only:
                query = query.filter_by(enabled=1)

            results = query.all()
            session.close()

            rules = []
            for r in results:
                rules.append({
                    "id": r.id,
                    "symbol": r.symbol,
                    "rule_type": r.rule_type,
                    "condition": r.condition,
                    "threshold": r.threshold,
                    "enabled": r.enabled,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                })

            return rules

        except Exception as e:
            logger.error(f"Error getting alert rules: {e}")
            return []

    def delete_alert_rule(self, rule_id: int) -> bool:
        """
        删除预警规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        try:
            session = self.Session()

            rule = session.query(AlertRule).filter_by(id=rule_id).first()
            if rule:
                session.delete(rule)
                session.commit()
                logger.info(f"Deleted alert rule {rule_id}")
                result = True
            else:
                logger.warning(f"Alert rule {rule_id} not found")
                result = False

            session.close()
            return result

        except Exception as e:
            logger.error(f"Error deleting alert rule: {e}")
            session.rollback()
            session.close()
            return False
