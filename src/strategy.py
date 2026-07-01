"""策略层：只产出持仓信号 position(0/1)，不计算任何收益"""
import numpy as np
import pandas as pd


def ma_cross_signal(df: pd.DataFrame, fast: int = 5, slow: int = 20) -> pd.Series:
    """
    双均线策略：快线上穿慢线持仓(1)，否则空仓(0)。

    关键点：
        - 均线在全量数据上计算，保证回测起点的均线值不缺失
        - shift(1) 滞后一天，避免使用当日未来信息（未来函数）
    返回:
        与 df 等长的 position Series(已滞后)，索引与 df 对齐
    """
    ma_fast = df['close'].rolling(window=fast).mean()
    ma_slow = df['close'].rolling(window=slow).mean()

    signal = np.where(ma_fast > ma_slow, 1, 0)
    position = pd.Series(signal, index=df.index).shift(1).fillna(0)

    return position
