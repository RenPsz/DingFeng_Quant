"""信号处理因子包：把价格序列当作信号，做时域/频域/相关性分析"""
from .spectrum import high_freq_ratio
from .energy import energy_ratio
from .autocorr import autocorr_factor
