"""
系统功能测试脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from src.data_fetcher import AkShareFetcher
from src.indicators import IndicatorCalculator
from src.storage import Database, Cache
from src.analysis import DataAnalyzer
from datetime import datetime, timedelta

def test_data_fetcher():
    """测试数据获取模块"""
    print("\n" + "="*50)
    print("测试数据获取模块")
    print("="*50)

    fetcher = AkShareFetcher()

    # 测试实时数据
    print("\n1. 测试获取实时数据...")
    data = fetcher.get_realtime_data("sh000001")
    if data:
        print(f"✓ 成功获取上证指数实时数据")
        print(f"  当前价格: {data['current']}")
        print(f"  涨跌幅: {data['pct_change']}%")
    else:
        print("✗ 获取实时数据失败")

    # 测试历史数据
    print("\n2. 测试获取历史数据...")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    df = fetcher.get_historical_data("sh000001", start_date, end_date, "daily")
    if df is not None and not df.empty:
        print(f"✓ 成功获取历史数据")
        print(f"  数据条数: {len(df)}")
        print(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
    else:
        print("✗ 获取历史数据失败")

    return df

def test_indicators(df):
    """测试技术指标模块"""
    print("\n" + "="*50)
    print("测试技术指标模块")
    print("="*50)

    if df is None or df.empty:
        print("✗ 没有数据，跳过测试")
        return None

    calculator = IndicatorCalculator()

    # 测试MA
    print("\n1. 测试计算MA...")
    df_ma = calculator.calculate_ma(df)
    if "MA5" in df_ma.columns and "MA10" in df_ma.columns:
        print(f"✓ 成功计算MA指标")
        print(f"  MA5最新值: {df_ma['MA5'].iloc[-1]:.2f}")
        print(f"  MA10最新值: {df_ma['MA10'].iloc[-1]:.2f}")
    else:
        print("✗ 计算MA失败")

    # 测试所有指标
    print("\n2. 测试计算所有指标...")
    df_all = calculator.calculate_all_indicators(df)
    indicators = [col for col in df_all.columns if col not in df.columns]
    print(f"✓ 成功计算 {len(indicators)} 个技术指标")
    print(f"  指标列表: {', '.join(indicators[:10])}...")

    # 测试信号
    print("\n3. 测试获取信号...")
    signals = calculator.get_latest_signals(df_all)
    if signals:
        print(f"✓ 成功获取技术信号")
        if 'macd' in signals and signals['macd']:
            print(f"  MACD DIF: {signals['macd'].get('dif', 0):.2f}")
            print(f"  MACD DEA: {signals['macd'].get('dea', 0):.2f}")
    else:
        print("✗ 获取信号失败")

    return df_all

def test_storage(df):
    """测试存储模块"""
    print("\n" + "="*50)
    print("测试存储模块")
    print("="*50)

    if df is None or df.empty:
        print("✗ 没有数据，跳过测试")
        return

    # 测试数据库
    print("\n1. 测试数据库...")
    db = Database()

    # 保存历史数据
    success = db.save_historical_data("sh000001", df, "daily")
    if success:
        print("✓ 成功保存历史数据到数据库")
    else:
        print("✗ 保存历史数据失败")

    # 查询历史数据
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    df_query = db.get_historical_data("sh000001", start_date, end_date, "daily")
    if df_query is not None and not df_query.empty:
        print(f"✓ 成功从数据库查询数据")
        print(f"  查询到 {len(df_query)} 条记录")
    else:
        print("✗ 查询数据失败")

    # 测试缓存
    print("\n2. 测试缓存...")
    cache = Cache()

    if cache.enabled:
        # 设置缓存
        test_data = {"test": "data", "value": 123}
        cache.set("test_key", test_data, expire=60)

        # 获取缓存
        cached = cache.get("test_key")
        if cached and cached.get("test") == "data":
            print("✓ 缓存功能正常")
        else:
            print("✗ 缓存功能异常")
    else:
        print("⚠ Redis未连接，缓存功能已禁用")

def test_analysis(df):
    """测试分析模块"""
    print("\n" + "="*50)
    print("测试分析模块")
    print("="*50)

    if df is None or df.empty:
        print("✗ 没有数据，跳过测试")
        return

    analyzer = DataAnalyzer()

    # 测试统计分析
    print("\n1. 测试统计分析...")
    stats = analyzer.calculate_statistics(df)
    if stats:
        print("✓ 成功计算统计数据")
        print(f"  最高价: {stats['price']['max']:.2f}")
        print(f"  最低价: {stats['price']['min']:.2f}")
        print(f"  平均价: {stats['price']['avg']:.2f}")
    else:
        print("✗ 统计分析失败")

    # 测试波动率
    print("\n2. 测试波动率分析...")
    volatility = analyzer.calculate_volatility(df)
    if volatility:
        print("✓ 成功计算波动率")
        print(f"  历史波动率: {volatility.get('historical', 0):.2f}%")
        print(f"  当前波动率: {volatility.get('current', 0):.2f}%")
    else:
        print("✗ 波动率分析失败")

    # 测试连涨连跌
    print("\n3. 测试连涨连跌分析...")
    consecutive = analyzer.find_consecutive_days(df)
    if consecutive:
        print("✓ 成功分析连涨连跌")
        current = consecutive.get('current', {})
        print(f"  当前状态: {current.get('type', 'N/A')} {current.get('days', 0)}天")
    else:
        print("✗ 连涨连跌分析失败")

def main():
    """主测试函数"""
    print("\n" + "="*50)
    print("A股指数分析系统 - 功能测试")
    print("="*50)

    try:
        # 测试数据获取
        df = test_data_fetcher()

        # 测试技术指标
        df_with_indicators = test_indicators(df)

        # 测试存储
        test_storage(df)

        # 测试分析
        test_analysis(df)

        print("\n" + "="*50)
        print("测试完成！")
        print("="*50)
        print("\n提示：")
        print("1. 如果看到 ✓ 表示测试通过")
        print("2. 如果看到 ✗ 表示测试失败")
        print("3. 如果看到 ⚠ 表示警告信息")
        print("\n现在可以运行 'python main.py' 启动Web服务")

    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
