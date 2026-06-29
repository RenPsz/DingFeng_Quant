"""预警有效性评估：把因子转成预警信号，统计命中率，并与传统指标基准对比

最终采用的命中口径（中长期风险预警定位）：
    命中 = 预警发出后 horizon(默认60)个交易日内最大回撤超过阈值(默认15%)。
    即衡量"在重大回撤来临前能否提前预警"，而非预测短期涨跌。

预警信号生成：
    - 幅度类因子(能量比/高频占比)：用滚动 z-score 突破，捕捉相对自身常态的异常抬升。
    - 趋势结构类因子(自相关)：用由正转负的跳变，捕捉趋势动能衰竭。

验证结论(沪深300全历史)：
    自相关转负因子命中率显著跑赢 RSI/布林带等基准(1.45x)，
    幅度类因子是波动的同期产物、无领先性。详见 docs/changelog.md。
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 242


def future_drawdown(close: pd.Series, horizon: int = 60) -> pd.Series:
    """未来 horizon 日内的最大回撤(负值)，对齐到当前日。

    用于中长期风险预警：从当前日买入，未来一段时间内最深跌幅。
    """
    n = len(close)
    arr = close.to_numpy()
    out = np.full(n, np.nan)
    for i in range(n):
        end = min(i + horizon + 1, n)
        window = arr[i:end]
        if len(window) < 2:
            continue
        # 从当前日起的滚动峰值到谷底的最大回撤
        running_max = np.maximum.accumulate(window)
        dd = (window - running_max) / running_max
        out[i] = dd.min()
    return pd.Series(out, index=close.index, name='future_drawdown')


def zscore_alert(factor: pd.Series, lookback: int = 120, k: float = 1.0) -> pd.Series:
    """幅度类因子预警：相对自身滚动常态的 z-score 突破。

    当 factor > 滚动均值 + k×滚动标准差 时发出预警(True)。
    """
    mean = factor.rolling(lookback).mean()
    std = factor.rolling(lookback).std()
    z = (factor - mean) / std.replace(0, np.nan)
    return z > k


def sign_flip_alert(factor: pd.Series) -> pd.Series:
    """趋势结构类因子预警：自相关由正转负的跳变(前一日>0 且当前<0)。"""
    prev = factor.shift(1)
    return (prev > 0) & (factor < 0)


def evaluate(alert: pd.Series, target: pd.Series,
             eligible: pd.Series = None) -> dict:
    """评估一组预警信号的命中表现。

    参数:
        alert:    预警信号布尔序列
        target:   命中目标布尔序列(如未来发生重大回撤)
        eligible: 有效样本掩码(剔除未来数据不足的尾部)，默认全部有效
    返回:
        n_alerts(预警次数) / n_hits(命中次数) / hit_rate(命中率)
    """
    if eligible is None:
        eligible = pd.Series(True, index=alert.index)
    a = alert & eligible
    n_alerts = int(a.sum())
    if n_alerts == 0:
        return {'n_alerts': 0, 'n_hits': 0, 'hit_rate': np.nan}

    n_hits = int((a & target).sum())
    return {
        'n_alerts': n_alerts,
        'n_hits': n_hits,
        'hit_rate': n_hits / n_alerts,
    }


def bollinger_alert(close: pd.Series, window: int = 20, k: float = 2.0) -> pd.Series:
    """基准1：布林带突破（价格跌破下轨或升破上轨）。"""
    ma = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = ma + k * std
    lower = ma - k * std
    return (close > upper) | (close < lower)


def rsi_alert(close: pd.Series, window: int = 14,
              low: float = 30, high: float = 70) -> pd.Series:
    """基准2：RSI 超买(>high)或超卖(<low)。"""
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    return (rsi > high) | (rsi < low)
