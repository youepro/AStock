"""
FastAPI主应用
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger
import os

from config import settings
from ..constants import SUPPORTED_INDICES, PERIODS
from ..data_fetcher import YFinanceFetcher
from ..indicators import IndicatorCalculator
from ..storage import Database, Cache
from ..analysis import DataAnalyzer

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A股指数实时获取和分析API"
)

# 挂载静态文件
static_path = os.path.join(os.path.dirname(__file__), "../../frontend/static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
fetcher = YFinanceFetcher()
calculator = IndicatorCalculator()
database = Database()
cache = Cache()
analyzer = DataAnalyzer()

# 配置日志
logger.add(
    settings.LOG_FILE,
    rotation="1 day",
    retention="7 days",
    level=settings.LOG_LEVEL
)


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} started")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info(f"{settings.APP_NAME} shutdown")


@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回前端页面"""
    html_path = os.path.join(os.path.dirname(__file__), "../../frontend/templates/index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/api/indices")
async def get_supported_indices():
    """
    获取支持的指数列表
    """
    try:
        indices = []
        for symbol, info in SUPPORTED_INDICES.items():
            indices.append({
                "symbol": symbol,
                "name": info["name"],
                "code": info["code"]
            })

        return {
            "success": True,
            "data": indices,
            "count": len(indices)
        }

    except Exception as e:
        logger.error(f"Error getting supported indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/realtime/all")
async def get_all_realtime_data():
    """
    获取所有支持指数的实时行情
    """
    try:
        df = fetcher.get_all_indices_realtime()

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="No data found")

        data = df.to_dict(orient="records")

        return {
            "success": True,
            "data": data,
            "count": len(data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all realtime data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/realtime/{symbol}")
async def get_realtime_data(symbol: str):
    """
    获取指数实时行情

    Args:
        symbol: 指数代码 (如: sh000001)
    """
    try:
        # 检查缓存
        cached_data = cache.get_realtime_data(symbol)
        if cached_data:
            logger.info(f"Returning cached realtime data for {symbol}")
            return {
                "success": True,
                "data": cached_data,
                "from_cache": True
            }

        # 获取实时数据
        data = fetcher.get_realtime_data(symbol)

        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # 保存到缓存
        cache.set_realtime_data(symbol, data, expire=5)

        # 保存到数据库
        database.save_realtime_data(data)

        return {
            "success": True,
            "data": data,
            "from_cache": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting realtime data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period: str = Query("daily", description="时间周期 (daily, weekly, monthly)")
):
    """
    获取指数历史数据

    Args:
        symbol: 指数代码
        start_date: 开始日期
        end_date: 结束日期
        period: 时间周期
    """
    try:
        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 先从数据库查询
        df = database.get_historical_data(symbol, start_date, end_date, period)

        # 如果数据库没有或数据不完整，从API获取
        if df is None or df.empty:
            logger.info(f"Fetching historical data from API for {symbol}")
            df = fetcher.get_historical_data(symbol, start_date, end_date, period)

            if df is None or df.empty:
                raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

            # 保存到数据库
            database.save_historical_data(symbol, df, period)

        # 替换NaN值为None，避免JSON序列化错误
        df = df.fillna(0)

        # 转换为JSON
        data = df.to_dict(orient="records")

        # 转换日期格式
        for item in data:
            if "date" in item and hasattr(item["date"], "strftime"):
                item["date"] = item["date"].strftime("%Y-%m-%d")

        return {
            "success": True,
            "data": data,
            "count": len(data),
            "period": period,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/indicators/{symbol}")
async def get_indicators(
    symbol: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period: str = Query("daily", description="时间周期")
):
    """
    获取技术指标

    Args:
        symbol: 指数代码
        start_date: 开始日期
        end_date: 结束日期
        period: 时间周期
    """
    try:
        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 获取历史数据
        df = database.get_historical_data(symbol, start_date, end_date, period)

        if df is None or df.empty:
            df = fetcher.get_historical_data(symbol, start_date, end_date, period)

            if df is None or df.empty:
                raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # 计算技术指标
        df_with_indicators = calculator.calculate_all_indicators(df)

        # 获取最新信号
        signals = calculator.get_latest_signals(df_with_indicators)

        # 转换为JSON
        data = df_with_indicators.tail(100).to_dict(orient="records")

        # 转换日期格式
        for item in data:
            if "date" in item and hasattr(item["date"], "strftime"):
                item["date"] = item["date"].strftime("%Y-%m-%d")

        return {
            "success": True,
            "data": data,
            "signals": signals,
            "count": len(data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{symbol}")
async def get_analysis(
    symbol: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period: str = Query("daily", description="时间周期")
):
    """
    获取综合分析

    Args:
        symbol: 指数代码
        start_date: 开始日期
        end_date: 结束日期
        period: 时间周期
    """
    try:
        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 获取历史数据
        df = database.get_historical_data(symbol, start_date, end_date, period)

        if df is None or df.empty:
            df = fetcher.get_historical_data(symbol, start_date, end_date, period)

            if df is None or df.empty:
                raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # 计算技术指标
        df_with_indicators = calculator.calculate_all_indicators(df)

        # 获取信号
        signals = calculator.get_latest_signals(df_with_indicators)

        # 生成分析摘要
        summary = analyzer.generate_summary(df_with_indicators, signals)

        return {
            "success": True,
            "data": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare")
async def compare_indices(
    symbols: str = Query(..., description="指数代码列表，逗号分隔"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    period: str = Query("daily", description="时间周期")
):
    """
    对比多个指数

    Args:
        symbols: 指数代码列表（逗号分隔）
        start_date: 开始日期
        end_date: 结束日期
        period: 时间周期
    """
    try:
        # 解析symbols
        symbol_list = [s.strip() for s in symbols.split(",")]

        if len(symbol_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required")

        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 获取各个指数的数据
        data_dict = {}
        for symbol in symbol_list:
            df = database.get_historical_data(symbol, start_date, end_date, period)

            if df is None or df.empty:
                df = fetcher.get_historical_data(symbol, start_date, end_date, period)

            if df is not None and not df.empty:
                data_dict[symbol] = df

        if not data_dict:
            raise HTTPException(status_code=404, detail="No data found for any symbol")

        # 对比分析
        comparison = analyzer.compare_indices(data_dict)

        return {
            "success": True,
            "data": comparison
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def get_alerts(symbol: Optional[str] = None):
    """
    获取预警规则

    Args:
        symbol: 指数代码（可选）
    """
    try:
        rules = database.get_alert_rules(symbol=symbol)

        return {
            "success": True,
            "data": rules,
            "count": len(rules)
        }

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts")
async def create_alert(rule: dict):
    """
    创建预警规则

    Args:
        rule: 预警规则
    """
    try:
        success = database.save_alert_rule(rule)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create alert rule")

        return {
            "success": True,
            "message": "Alert rule created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/alerts/{rule_id}")
async def delete_alert(rule_id: int):
    """
    删除预警规则

    Args:
        rule_id: 规则ID
    """
    try:
        success = database.delete_alert_rule(rule_id)

        if not success:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        return {
            "success": True,
            "message": "Alert rule deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
