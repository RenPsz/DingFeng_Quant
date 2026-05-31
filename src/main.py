"""主程序：只做流程编排，不写具体计算逻辑"""
from data import get_index_data
from strategy import ma_cross_signal
from backtest import run_backtest, calculate_metrics, print_report
from plot import plot_equity_curve

# ---- 参数配置 ----
SYMBOL = "sh600519"
START_DATE = "2020-01-01"
FAST, SLOW = 5, 20
COMMISSION = 0.001

# ---- 1. 取数据 ----
df = get_index_data(SYMBOL)

# ---- 2. 生成信号 ----
print("正在计算双均线策略信号...")
position = ma_cross_signal(df, fast=FAST, slow=SLOW)

# ---- 3. 回测 ----
print("正在执行回测...")
result = run_backtest(df, position, start_date=START_DATE, commission=COMMISSION)

# ---- 4. 计算指标并打印报告 ----
metrics_market = calculate_metrics(result['cum_market_wealth'], result['market_return'])
metrics_strategy = calculate_metrics(result['cum_strategy_wealth'], result['strategy_return'])
print_report(metrics_market, metrics_strategy, START_DATE)

# ---- 5. 可视化 ----
print("\n正在生成可视化图表...")
plot_equity_curve(result)