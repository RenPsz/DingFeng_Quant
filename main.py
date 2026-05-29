import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 全量数据获取与基础指标计算
# ==========================================
print("正在获取沪深300数据...")
## df是panda数据的DataFrame，类似于excel的二维表格。
df = ak.stock_zh_index_daily(symbol="sh000300")
##df['xx']操作一整列
df['date'] = pd.to_datetime(df['date'])
##根据时间排序，重置索引从0开始
df = df.sort_values('date').reset_index(drop=True)

print("正在计算双均线策略信号...")
##df动态创建新的数据列['MA5']，rolling滑动窗口总值，mean()计算平均值
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA20'] = df['close'].rolling(window=20).mean()

# 产生信号并滞后一天交易
##np.where(如果, 就, 否则)，一次处理整个df数据库，动态创建信号列
df['signal'] = np.where(df['MA5'] > df['MA20'], 1, 0)
##shift(1)把df数据库整体下移一行\fillna(x)，把Null填充为x值.
df['position'] = df['signal'].shift(1).fillna(0)

## pct_change() = (当天值 - 前一天值) ÷ 前一天值, 计算涨跌值
df['market_return'] = df['close'].pct_change().fillna(0)    ## 计算每日收益率
df['strategy_return'] = df['market_return'] * df['position'] ## 计算策略收益率(市场收益率×1/0（持仓）)

# ==========================================
# 💡 核心修复：先裁剪，后独立计算财富指数
# ==========================================
start_date = '2023-01-01'
# 严格筛选时间段，并复制一份干净的数据切片
# df[df['date'] >= start_date]条件筛选，只保留日期在start_date及之后的行
# .copy()复制一份副本，reset_index(drop=True)截取的片段数据索引值还是原来的df索引值，所以需要重置
df_plot = df[df['date'] >= start_date].copy().reset_index(drop=True)

# 确保在 2023-01-01 这一天，所有的财富起点都严格等于 1.0（不继承历史污染）
# 1 + df_plot['market_return']归一化处理，-1%(0.99),+1%(1.01),起点index=0->1;
# (1 + df_plot['market_return'])->整列，用.cumprod() cumulative produc整列累乘
df_plot['cum_market_wealth'] = (1 + df_plot['market_return']).cumprod()
df_plot['cum_strategy_wealth'] = (1 + df_plot['strategy_return']).cumprod()

# 将财富曲线的第一行强制归一化为 1（让图表从同一个起跑线出发）
# .loc按标签定位（label-based location），参数1：行index，参数2:列名,修改指定二维点值
df_plot.loc[0, 'cum_market_wealth'] = 1.0
df_plot.loc[0, 'cum_strategy_wealth'] = 1.0


# ==========================================
# 📊 2. 回测指标计算模块
# ==========================================
def calculate_metrics(wealth_series, daily_returns):
    total_return = wealth_series.iloc[-1] - 1
    days = len(wealth_series)
    annual_return = (wealth_series.iloc[-1]) ** (242 / days) - 1

    historical_max = wealth_series.cummax()
    drawdowns = (wealth_series - historical_max) / historical_max
    max_drawdown = drawdowns.min()

    daily_rf = 0.02 / 242
    excess_returns = daily_returns - daily_rf
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(242) if excess_returns.std() != 0 else 0
    return total_return, annual_return, max_drawdown, sharpe_ratio


m_total, m_annual, m_dd, m_sharpe = calculate_metrics(df_plot['cum_market_wealth'], df_plot['market_return'])
s_total, s_annual, s_dd, s_sharpe = calculate_metrics(df_plot['cum_strategy_wealth'], df_plot['strategy_return'])

print("\n" + "=" * 20 + f" 修正版回测报告 ({start_date} 至今) " + "=" * 20)
print(f"{'性能指标':<15}{'基准策略 (持有沪深300)':<25}{'双均线趋势策略':<25}")
print("-" * 65)
print(f"{'累计收益率':<13}{m_total:>20.2%}{s_total:>20.2%}")
print(f"{'年化收益率':<13}{m_annual:>20.2%}{s_annual:>20.2%}")
print(f"{'最大回撤':<14}{m_dd:>20.2%}{s_dd:>20.2%}")
print(f"{'年化夏普比率':<11}{m_sharpe:>22.2f}{s_sharpe:>22.2f}")
print("=" * 65)

# ==========================================
# 🎨 3. 终极绘图模块（格式化日期横坐标）
# ==========================================
print("\n正在生成可视化图表...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# 子图1：净值曲线对比（X轴直接传入包含日期对象的 df_plot['date']）
ax1.plot(df_plot['date'], df_plot['cum_market_wealth'], label='基准净值 (沪深300)', color='red', alpha=0.7)
ax1.plot(df_plot['date'], df_plot['cum_strategy_wealth'], label='策略净值 (双均线)', color='green', linewidth=2)
ax1.set_title('策略资产净值 (Equity Curve) 对比', fontsize=14)
ax1.set_ylabel('净值 (从1开始)', fontsize=12)
ax1.legend()
ax1.grid(True, linestyle='--', alpha=0.5)

# 子图2：历史回撤图
historical_max_s = df_plot['cum_strategy_wealth'].cummax()
drawdowns_s = (df_plot['cum_strategy_wealth'] - historical_max_s) / historical_max_s

historical_max_m = df_plot['cum_market_wealth'].cummax()
drawdowns_m = (df_plot['cum_market_wealth'] - historical_max_m) / historical_max_m

ax2.fill_between(df_plot['date'], drawdowns_m * 100, 0, label='基准回撤', color='red', alpha=0.2)
ax2.fill_between(df_plot['date'], drawdowns_s * 100, 0, label='策略回撤', color='green', alpha=0.3)
ax2.set_title('历史回撤幅度 (%) 对比', fontsize=14)
ax2.set_ylabel('回撤比例 (%)', fontsize=12)
ax2.set_xlabel('日期', fontsize=12)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.5)

# 美化X轴日期显示格式
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # 显示年-月
plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # 每隔3个月显示一个刻度
plt.gcf().autofmt_xdate()  # 自动旋转日期避免重叠

plt.tight_layout()
plt.show()