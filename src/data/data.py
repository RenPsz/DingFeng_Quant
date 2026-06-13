"""数据层：负责行情数据的获取、缓存与清洗"""
import akshare as ak
import pandas as pd
from . import storage
import datetime

storage.init_db()

INDICES = [
    "sh000001",  # 上证指数
    "sh000300",  # 沪深300
    "sh000905",  # 中证500
    "sh000852",  # 中证1000
    "sz399001",  # 深证成指
    "sz399006",  # 创业板指
]

STOCK_START = "2015-01-01"  # 近十年起点


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """统一清洗：日期化、升序、去重、数值列修正"""
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = df.drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _cached_fetch(symbol: str, fetch_fn, force_refresh: bool = False) -> pd.DataFrame:
    """
    通用缓存流程：
    1. force_refresh → 全量请求，覆盖写库
    2. 无缓存 → 全量请求，写库
    3. 有缓存 → 增量请求（从最新日期起），upsert，返回全量
    """
    if force_refresh:
        df = _clean(fetch_fn(None))
        storage.upsert_daily(symbol, df)
        return df

    last = storage.get_last_date(symbol)

    if last is None:
        df = _clean(fetch_fn(None))
        storage.upsert_daily(symbol, df)
        return df

    # 从最新缓存日期当天开始拉，覆盖当日未收盘的旧值
    incr = fetch_fn(last)
    if incr is not None and not incr.empty:
        storage.upsert_daily(symbol, _clean(incr))

    return storage.read_daily(symbol)


def get_index_data(symbol: str = "sh000300", force_refresh: bool = False) -> pd.DataFrame:
    """获取指数日线数据（带本地缓存）"""
    print(f"  [{symbol}] 正在同步...")

    def fetch(start_date):
        df = ak.stock_zh_index_daily(symbol=symbol)
        if start_date:
            df = df[pd.to_datetime(df['date']) >= pd.to_datetime(start_date)]
        return df

    return _cached_fetch(symbol, fetch, force_refresh)


def get_stock_data(symbol: str, adjust: str = "qfq",
                   force_refresh: bool = False) -> pd.DataFrame:
    """
    获取个股日线数据（带本地缓存）。
    symbol: 带市场前缀，如 "sh600519" 或 "sz000001"
    adjust: qfq=前复权 / hfq=后复权 / "" 不复权
    """
    cache_key = f"{symbol}_{adjust or 'none'}"

    # 今日已更新则直接返回缓存
    if not force_refresh:
        last = storage.get_last_date(cache_key)
        last_trade_date = _get_last_trade_date()
        if last and last_trade_date and last >= last_trade_date:
            print(f"  [{symbol}] 已是最新，跳过")
            return storage.read_daily(cache_key)

    print(f"  [{symbol}] 正在同步...")
    cache_key = f"{symbol}_{adjust or 'none'}"

    def fetch(start_date):
        sd = pd.to_datetime(start_date).strftime('%Y%m%d') if start_date else \
             pd.to_datetime(STOCK_START).strftime('%Y%m%d')
        df = ak.stock_zh_a_daily(symbol=symbol, start_date=sd, adjust=adjust)
        return df[['date', 'open', 'close', 'high', 'low', 'volume']]

    return _cached_fetch(cache_key, fetch, force_refresh)


def refresh_indices(force_refresh: bool = False) -> None:
    """批量拉取/增量更新所有主要股指，已是最新交易日则跳过"""
    print("正在检查股指数据...")
    last_trade_date = _get_last_trade_date()

    for symbol in INDICES:
        last = storage.get_last_date(symbol)
        if not force_refresh and last and last_trade_date and last >= last_trade_date:
            print(f"  [{symbol}] 已是最新，跳过")
            continue
        get_index_data(symbol, force_refresh=force_refresh)
    print("股指数据检查完成。\n")
    
def _get_last_trade_date() -> str | None:
    """获取最近交易日，优先读缓存，日历过期则更新"""
    today = datetime.date.today().strftime('%Y-%m-%d')
    cal_last = storage.get_calendar_last_date()

    # 日历缓存不存在或已过期（最新日期早于今天）则重新拉取
    if not cal_last or cal_last < today:
        print("  正在更新交易日历...")
        df = ak.tool_trade_date_hist_sina()
        dates = df['trade_date'].astype(str).tolist()
        storage.upsert_calendar(dates)

    return storage.get_last_trade_date(today)