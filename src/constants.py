"""
常量定义模块
"""

# 支持的指数代码和名称
SUPPORTED_INDICES = {
    "sh000001": {"name": "上证指数", "code": "000001.SH", "symbol": "sh000001"},
    "sz399001": {"name": "深证成指", "code": "399001.SZ", "symbol": "sz399001"},
    "sz399006": {"name": "创业板指", "code": "399006.SZ", "symbol": "sz399006"},
    "sh000688": {"name": "科创50", "code": "000688.SH", "symbol": "sh000688"},
    "sh000300": {"name": "沪深300", "code": "000300.SH", "symbol": "sh000300"},
    "sh000905": {"name": "中证500", "code": "000905.SH", "symbol": "sh000905"},
    "sh000852": {"name": "中证1000", "code": "000852.SH", "symbol": "sh000852"},
}

# 时间周期
PERIODS = {
    "1min": "1分钟",
    "5min": "5分钟",
    "15min": "15分钟",
    "30min": "30分钟",
    "60min": "60分钟",
    "daily": "日线",
    "weekly": "周线",
    "monthly": "月线",
}

# 技术指标参数
INDICATOR_PARAMS = {
    "MA": [5, 10, 20, 30, 60, 120, 250],
    "EMA": [12, 26],
    "BOLL": {"period": 20, "std": 2},
    "RSI": [6, 12, 24],
    "KDJ": {"fastk_period": 9, "slowk_period": 3, "slowd_period": 3},
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
}

# 交易时间段
TRADING_HOURS = {
    "morning": {"start": "09:30", "end": "11:30"},
    "afternoon": {"start": "13:00", "end": "15:00"},
}

# 数据字段映射
DATA_COLUMNS = {
    "date": "日期",
    "open": "开盘",
    "high": "最高",
    "low": "最低",
    "close": "收盘",
    "volume": "成交量",
    "amount": "成交额",
    "change": "涨跌额",
    "pct_change": "涨跌幅",
}
