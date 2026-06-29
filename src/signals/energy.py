"""时域能量分析因子：短期能量 / 长期能量比值

核心思路（日K口径）：
    - 把收益率序列当作时域信号，信号能量定义为收益率平方和（波动剧烈则能量大）。
    - 短窗口能量代表近期波动水平，长窗口能量代表常态波动水平。
    - 二者比值升高 → 近期波动相对常态显著放大 → 短期波动加剧信号。
"""
import numpy as np
import pandas as pd


def energy_ratio(df: pd.DataFrame, short_window: int = 20,
                 long_window: int = 250) -> pd.Series:
    """计算逐日的短期/长期能量比因子。

    参数:
        df: 含 'close' 列的行情 DataFrame（按日期升序）
        short_window: 短期能量窗口（交易日），默认 20 ≈ 1个月
        long_window: 长期能量窗口（交易日），默认 250 ≈ 1年（中长期视角）

    返回:
        与 df 等长的 Series，前 long_window 个为 NaN。
        值 > 1 表示近期波动强于常态，越高越剧烈。
        注：属幅度类因子，验证显示为波动同期描述，预警领先性有限。
    """
    returns = df['close'].pct_change()
    sq = returns ** 2  # 逐日能量

    # 用平均能量（均方）而非能量总和，消除窗口长度差异带来的量纲偏差
    short_energy = sq.rolling(short_window).mean()
    long_energy = sq.rolling(long_window).mean()

    ratio = short_energy / long_energy.replace(0, np.nan)
    ratio.name = 'energy_ratio'
    return ratio
