"""可视化层：本地 matplotlib 绘图，将来会被 React 前端替代"""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


def plot_equity_curve(df):
    """绘制净值曲线 + 历史回撤双子图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # 子图1：净值曲线对比
    ax1.plot(df['date'], df['cum_market_wealth'], label='基准净值',
             color='red', alpha=0.7)
    ax1.plot(df['date'], df['cum_strategy_wealth'], label='策略净值 (双均线)',
             color='green', linewidth=2)
    ax1.set_title('策略资产净值 (Equity Curve) 对比', fontsize=14)
    ax1.set_ylabel('净值 (从1开始)', fontsize=12)
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)

    # 子图2：历史回撤
    dd_m = _drawdown(df['cum_market_wealth'])
    dd_s = _drawdown(df['cum_strategy_wealth'])
    ax2.fill_between(df['date'], dd_m * 100, 0, label='基准回撤', color='red', alpha=0.2)
    ax2.fill_between(df['date'], dd_s * 100, 0, label='策略回撤', color='green', alpha=0.3)
    ax2.set_title('历史回撤幅度 (%) 对比', fontsize=14)
    ax2.set_ylabel('回撤比例 (%)', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)

    # 日期格式化
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    plt.show()


def _drawdown(wealth_series):
    """计算回撤序列的内部工具函数"""
    historical_max = wealth_series.cummax()
    return (wealth_series - historical_max) / historical_max


def plot_signal_factors(df, hfr, er, ac, title='信号处理因子 vs K线', save_path=None):
    """绘制收盘价与三个信号处理因子的对照图（4个子图共享X轴）。

    参数:
        df: 含 'date'、'close' 的行情切片
        hfr/er/ac: 与 df 对齐的高频占比/能量比/自相关 Series
        save_path: 若提供则保存到该路径，否则弹窗显示
    """
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    ax_price, ax_hfr, ax_er, ax_ac = axes

    # 子图1：收盘价
    ax_price.plot(df['date'], df['close'], color='black', linewidth=1.5)
    ax_price.set_title(title, fontsize=14)
    ax_price.set_ylabel('收盘价')
    ax_price.grid(True, linestyle='--', alpha=0.5)

    # 子图2：高频占比
    ax_hfr.plot(df['date'], hfr, color='purple')
    ax_hfr.set_ylabel('高频占比')
    ax_hfr.grid(True, linestyle='--', alpha=0.5)

    # 子图3：能量比（基准线1.0）
    ax_er.plot(df['date'], er, color='orange')
    ax_er.axhline(1.0, color='gray', linestyle=':', alpha=0.7)
    ax_er.set_ylabel('能量比')
    ax_er.grid(True, linestyle='--', alpha=0.5)

    # 子图4：自相关（基准线0）
    ax_ac.plot(df['date'], ac, color='teal')
    ax_ac.axhline(0, color='gray', linestyle=':', alpha=0.7)
    ax_ac.set_ylabel('自相关')
    ax_ac.set_xlabel('日期')
    ax_ac.grid(True, linestyle='--', alpha=0.5)

    ax_ac.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120)
        plt.close(fig)
    else:
        plt.show()
