"""数据层：负责行情数据的获取、缓存与清洗"""
import datetime

import akshare as ak
import pandas as pd

from . import storage

INDICES = [
    "sh000001",  # 上证指数
    "sh000300",  # 沪深300
    "sh000905",  # 中证500
    "sh000852",  # 中证1000
    "sz399001",  # 深证成指
    "sz399006",  # 创业板指
]

STOCK_START = "2015-01-01"  # 近十年起点

# 股票池接口不可用时的代表性样本池，仅用于实验因子不中断主流程。
FALLBACK_STOCK_SYMBOLS = [
    "sh600000", "sh600009", "sh600010", "sh600015", "sh600016",
    "sh600018", "sh600028", "sh600030", "sh600031", "sh600036",
    "sh600048", "sh600050", "sh600061", "sh600104", "sh600111",
    "sh600150", "sh600276", "sh600309", "sh600346", "sh600406",
    "sh600519", "sh600585", "sh600690", "sh600703", "sh600745",
    "sh600760", "sh600809", "sh600887", "sh601006", "sh601012",
    "sh601088", "sh601166", "sh601186", "sh601211", "sh601288",
    "sh601318", "sh601328", "sh601398", "sh601601", "sh601668",
    "sh601688", "sh601857", "sh601888", "sh601899", "sh601919",
    "sh601988", "sh601989", "sh603259", "sh603288", "sh603501",
    "sz000001", "sz000002", "sz000063", "sz000066", "sz000069",
    "sz000100", "sz000157", "sz000166", "sz000333", "sz000338",
    "sz000425", "sz000538", "sz000568", "sz000596", "sz000625",
    "sz000651", "sz000661", "sz000708", "sz000725", "sz000776",
    "sz000858", "sz000876", "sz000895", "sz000938", "sz000963",
    "sz001979", "sz002001", "sz002007", "sz002027", "sz002049",
    "sz002050", "sz002129", "sz002142", "sz002179", "sz002230",
    "sz002236", "sz002241", "sz002271", "sz002304", "sz002311",
    "sz002352", "sz002410", "sz002415", "sz002459", "sz002460",
    "sz002475", "sz002493", "sz002594", "sz002714", "sz002812",
    "sz300014", "sz300015", "sz300033", "sz300059", "sz300122",
    "sz300124", "sz300142", "sz300274", "sz300308", "sz300316",
    "sz300347", "sz300408", "sz300413", "sz300433", "sz300450",
    "sz300498", "sz300750", "sz300759", "sz300760", "sz300782",
]


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


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str:
    """在不同数据源字段名中寻找目标列。"""
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"未找到字段：{candidates}")


def _symbols_from_exchange_list(df: pd.DataFrame, prefix: str,
                                include_st: bool) -> list[str]:
    """把交易所股票列表转换为 sh/sz 前缀代码。"""
    code_col = _find_column(df, ['证券代码', 'A股代码', '代码'])
    name_col = None
    for candidate in ['证券简称', 'A股简称', '名称']:
        if candidate in df.columns:
            name_col = candidate
            break

    if not include_st and name_col:
        df = df[~df[name_col].astype(str).str.contains('ST', case=False, na=False)]

    symbols = []
    for code in df[code_col].astype(str).str.zfill(6):
        symbols.append(f"{prefix}{code}")
    return symbols


def get_a_stock_symbols(include_st: bool = False,
                        fallback: bool = True) -> list[str]:
    """获取 A 股股票池，返回带市场前缀的代码列表。"""
    try:
        sh_main = ak.stock_info_sh_name_code(symbol="主板A股")
        sh_star = ak.stock_info_sh_name_code(symbol="科创板")
        sz_all = ak.stock_info_sz_name_code(symbol="A股列表")
    except Exception as exc:
        if fallback:
            print(f"  股票池接口不可用，使用内置样本池：{exc}")
            return FALLBACK_STOCK_SYMBOLS.copy()
        raise

    symbols = []
    symbols.extend(_symbols_from_exchange_list(sh_main, 'sh', include_st))
    symbols.extend(_symbols_from_exchange_list(sh_star, 'sh', include_st))
    symbols.extend(_symbols_from_exchange_list(sz_all, 'sz', include_st))
    return sorted(set(symbols))


def get_stock_data(symbol: str, adjust: str = "qfq",
                   force_refresh: bool = False,
                   sync_latest: bool = True) -> pd.DataFrame:
    """
    获取个股日线数据（带本地缓存）。
    symbol: 带市场前缀，如 "sh600519" 或 "sz000001"
    adjust: qfq=前复权 / hfq=后复权 / "" 不复权
    sync_latest: 是否检查并同步到最近交易日；批量因子计算可关闭以避免重复请求
    """
    cache_key = f"{symbol}_{adjust or 'none'}"

    if not force_refresh:
        last = storage.get_last_date(cache_key)
        if last and not sync_latest:
            print(f"  [{symbol}] 使用缓存，跳过同步")
            return storage.read_daily(cache_key)

        last_trade_date = _get_last_trade_date()
        if last and last_trade_date and last >= last_trade_date:
            print(f"  [{symbol}] 已是最新，跳过")
            return storage.read_daily(cache_key)

    print(f"  [{symbol}] 正在同步...")

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
