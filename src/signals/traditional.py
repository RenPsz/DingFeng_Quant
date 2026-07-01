"""传统动量因子：补充独立于信号处理方法的价格趋势维度

验证结论：
    - 中长期动量低分位(momentum_low)具备弱预警增益，可作为候选预警因子。
    - 波动率、量能放大、贝塔单因子验证未跑赢基准，已删除。
"""
import pandas as pd


def momentum_factor(df: pd.DataFrame, window: int = 120) -> pd.Series:
    """计算中长期动量因子：当前收盘价相对 window 日前的涨跌幅。"""
    momentum = df['close'].pct_change(window)
    momentum.name = 'momentum'
    return momentum


def traditional_factors(df: pd.DataFrame) -> pd.DataFrame:
    """汇总当前保留的传统因子。"""
    factors = pd.DataFrame(index=df.index)
    factors['momentum'] = momentum_factor(df)
    return factors
