"""频域分析因子：对收益率序列做 FFT，计算高频段能量占比

核心思路（日K口径）：
    - 把收益率序列当作时域信号，在滚动窗口内做快速傅里叶变换(FFT)。
    - 低频分量对应长期趋势，高频分量对应短期噪声/情绪扰动。
    - 高频能量占比异常攀升 → 市场情绪紊乱、短期波动加剧的预警信号。

只依赖 numpy.fft，不引入 scipy。
"""
import numpy as np
import pandas as pd


def _single_window_ratio(returns: np.ndarray, high_freq_cutoff: float) -> float:
    """计算单个窗口内的高频能量占比。

    参数:
        returns: 一维收益率数组（已去均值前的原始收益率）
        high_freq_cutoff: 高频判定起点，取值 (0, 0.5]，对应归一化频率。
                          例如 0.25 表示后 50% 频段视为高频。
    返回:
        高频能量 / 总能量，范围 [0, 1]
    """
    n = len(returns)
    # 去均值：剔除直流分量(频率0)，避免均值收益主导能量分布
    centered = returns - returns.mean()

    # 实信号用 rfft，只取非负频率部分
    fft_vals = np.fft.rfft(centered)
    power = np.abs(fft_vals) ** 2  # 功率谱

    # rfft 输出对应的归一化频率：0, 1/n, ..., 0.5
    freqs = np.fft.rfftfreq(n)

    total_power = power.sum()
    if total_power == 0:
        return 0.0

    high_power = power[freqs >= high_freq_cutoff].sum()
    return high_power / total_power


def high_freq_ratio(df: pd.DataFrame, window: int = 250,
                    high_freq_cutoff: float = 0.25) -> pd.Series:
    """计算逐日的高频能量占比因子。

    参数:
        df: 含 'close' 列的行情 DataFrame（索引/顺序按日期升序）
        window: 滚动窗口长度（交易日），默认 250 ≈ 1年（中长期视角）
        high_freq_cutoff: 高频判定起点（归一化频率），默认 0.25

    返回:
        与 df 等长的 Series，前 window 个为 NaN（窗口未满）。
        值越高表示高频噪声能量占比越大。
        注：属幅度类因子，验证显示为波动同期描述，预警领先性有限。
    """
    returns = df['close'].pct_change().to_numpy()

    ratios = np.full(len(returns), np.nan)
    for end in range(window, len(returns)):
        win = returns[end - window + 1:end + 1]
        # 窗口内若含 NaN（首日 pct_change）则跳过
        if np.isnan(win).any():
            continue
        ratios[end] = _single_window_ratio(win, high_freq_cutoff)

    return pd.Series(ratios, index=df.index, name='high_freq_ratio')
