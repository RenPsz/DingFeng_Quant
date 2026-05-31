"""数据层：负责行情数据的获取与清洗"""
import akshare as ak
import pandas as pd

def get_index_data(symbol: str = "sh000300", start_date: str = None) -> pd.DataFrame:
    """
    获取指数日线数据，返回按日期升序、索引重置的干净 DataFrame。

    参数:
        symbol: 指数代码，如 "sh000300"
        start_date: 可选，过滤起始日期（如 "2023-01-01"）。
                    注意：这里不做切片，切片留给回测层，避免污染均线计算。
    返回:
        含 date / open / close / high / low / volume 的 DataFrame
    """
    print(f"正在获取 {symbol} 数据...")
    df = ak.stock_zh_index_daily(symbol=symbol)

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # 去重 + 数值列类型修正
    df = df.drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df