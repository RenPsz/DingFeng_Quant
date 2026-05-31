"""可视化层：本地 matplotlib 绘图，将来会被 React 前端替代"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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