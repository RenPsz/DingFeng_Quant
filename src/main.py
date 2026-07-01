"""主程序：运行当前保留的中长期预警候选因子验证。"""
import data
from signals import traditional_factors
from signals.evaluate import evaluate_traditional_factors

# ---- 参数配置 ----
SYMBOL = "sh600519"

# ---- 0. 更新股指缓存 ----
data.refresh_indices()

# ---- 1. 取数据 ----
df = data.get_stock_data(SYMBOL)

# ---- 2. 传统动量因子验证 ----
print("正在计算传统动量因子...")
factors = traditional_factors(df)
print("最新因子快照：")
print(factors.tail(1).T)

print("\n正在验证传统动量因子的中长期预警表现...")
evaluation = evaluate_traditional_factors(df['close'], factors)
print(evaluation.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
