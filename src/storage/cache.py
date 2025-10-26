"""
Redis缓存模块
"""
import json
import redis
from typing import Optional, Any
from loguru import logger

from config import settings


class Cache:
    """Redis缓存管理类"""

    def __init__(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis cache initialized")
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.enabled = False

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """
        设置缓存

        Args:
            key: 键
            value: 值
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            # 将值转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)

            self.redis_client.setex(key, expire, value)
            logger.debug(f"Cache set: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 键

        Returns:
            缓存值
        """
        if not self.enabled:
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 键

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 键

        Returns:
            是否存在
        """
        if not self.enabled:
            return False

        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存

        Args:
            pattern: 键模式（如: index:*）

        Returns:
            删除的键数量
        """
        if not self.enabled:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {count} cache keys matching: {pattern}")
                return count
            return 0

        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0

    def get_realtime_data(self, symbol: str) -> Optional[dict]:
        """
        获取实时数据缓存

        Args:
            symbol: 指数代码

        Returns:
            实时数据字典
        """
        key = f"realtime:{symbol}"
        return self.get(key)

    def set_realtime_data(self, symbol: str, data: dict, expire: int = 5) -> bool:
        """
        设置实时数据缓存

        Args:
            symbol: 指数代码
            data: 实时数据
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        key = f"realtime:{symbol}"
        return self.set(key, data, expire)

    def get_historical_data(self, symbol: str, start_date: str, end_date: str, period: str) -> Optional[str]:
        """
        获取历史数据缓存

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期

        Returns:
            历史数据JSON字符串
        """
        key = f"historical:{symbol}:{period}:{start_date}:{end_date}"
        return self.get(key)

    def set_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str,
        data: str,
        expire: int = 3600
    ) -> bool:
        """
        设置历史数据缓存

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期
            data: 历史数据JSON字符串
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        key = f"historical:{symbol}:{period}:{start_date}:{end_date}"
        return self.set(key, data, expire)

    def get_indicators(self, symbol: str, period: str) -> Optional[dict]:
        """
        获取技术指标缓存

        Args:
            symbol: 指数代码
            period: 周期

        Returns:
            技术指标字典
        """
        key = f"indicators:{symbol}:{period}"
        return self.get(key)

    def set_indicators(self, symbol: str, period: str, data: dict, expire: int = 300) -> bool:
        """
        设置技术指标缓存

        Args:
            symbol: 指数代码
            period: 周期
            data: 技术指标数据
            expire: 过期时间（秒）

        Returns:
            是否成功
        """
        key = f"indicators:{symbol}:{period}"
        return self.set(key, data, expire)

    def clear_all(self) -> bool:
        """
        清除所有缓存

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            self.redis_client.flushdb()
            logger.info("All cache cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return False
