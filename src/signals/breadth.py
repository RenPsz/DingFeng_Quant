"""市场宽度实验因子：刻画趋势扩散是否覆盖足够多股票

已验证：60 日均线以上占比的低分位信号未跑赢基准，不进入预警层。
当前模块仅作为后续宽度快速恶化、新高新低、背离类实验的基础工具。
"""
import pandas as pd


def ma_above_ratio(stock_data: dict[str, pd.DataFrame], window: int = 60,
                   min_count: int = 30) -> pd.Series:
    """计算股票池中收盘价高于 N 日均线的股票占比。

    参数:
        stock_data: {symbol: 日线 DataFrame}，每个 DataFrame 至少包含 date/close
        window: 均线窗口，默认 60 日
        min_count: 当日有效股票数低于该值时返回 NaN
    """
    above_frames = []
    valid_frames = []

    for symbol, df in stock_data.items():
        if df.empty or 'date' not in df.columns or 'close' not in df.columns:
            continue
        item = df[['date', 'close']].copy()
        item['date'] = pd.to_datetime(item['date'])
        item = item.sort_values('date').drop_duplicates('date', keep='last')
        item['ma'] = item['close'].rolling(window).mean()
        item[symbol] = item['close'] > item['ma']
        item[f'{symbol}_valid'] = item['ma'].notna()
        above_frames.append(item.set_index('date')[symbol])
        valid_frames.append(item.set_index('date')[f'{symbol}_valid'])

    if not above_frames:
        return pd.Series(dtype=float, name=f'ma{window}_above_ratio')

    above = pd.concat(above_frames, axis=1).fillna(False)
    valid = pd.concat(valid_frames, axis=1).fillna(False)
    valid_count = valid.sum(axis=1)
    ratio = (above & valid).sum(axis=1) / valid_count.replace(0, pd.NA)
    ratio = ratio.where(valid_count >= min_count)
    ratio.name = f'ma{window}_above_ratio'
    return ratio
