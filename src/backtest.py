"""回测层：拿价格 + position，计算收益、扣成本、滚动财富、输出指标"""
import numpy as np
import pandas as pd


def run_backtest(df: pd.DataFrame, position: pd.Series,
                 start_date: str = None, commission: float = 0.001) -> pd.DataFrame:
    """
    执行回测，返回带净值曲线的结果 DataFrame。

    流程:
        1. 在全量数据上算市场收益和策略收益（含手续费）
        2. 按 start_date 切片，得到干净的回测区间
        3. 在切片内独立累乘财富，并用除法归一化到 1.0
    """
    data = df.copy()
    data['position'] = position
    data['market_return'] = data['close'].pct_change().fillna(0)

    # 换仓时按单边费率扣除手续费
    data['trade'] = data['position'].diff().abs().fillna(0)
    data['strategy_return'] = (
        data['market_return'] * data['position'] - data['trade'] * commission
    )

    # 先切片，再独立计算财富，避免继承历史净值
    if start_date is not None:
        data = data[data['date'] >= start_date].copy()
    data = data.reset_index(drop=True)

    data['cum_market_wealth'] = (1 + data['market_return']).cumprod()
    data['cum_strategy_wealth'] = (1 + data['strategy_return']).cumprod()

    # 用除法归一化到 1.0（保留首日真实收益，不直接抹平）
    data['cum_market_wealth'] /= data['cum_market_wealth'].iloc[0]
    data['cum_strategy_wealth'] /= data['cum_strategy_wealth'].iloc[0]

    return data


def calculate_metrics(wealth_series: pd.Series, daily_returns: pd.Series,
                      annual_rf: float = 0.02, trading_days: int = 242) -> dict:
    """计算单条曲线的核心绩效指标，返回字典"""
    total_return = wealth_series.iloc[-1] - 1

    days = len(wealth_series)
    annual_return = wealth_series.iloc[-1] ** (trading_days / days) - 1

    historical_max = wealth_series.cummax()
    drawdowns = (wealth_series - historical_max) / historical_max
    max_drawdown = drawdowns.min()

    daily_rf = annual_rf / trading_days
    excess = daily_returns - daily_rf
    sharpe = (excess.mean() / excess.std()) * np.sqrt(trading_days) if excess.std() != 0 else 0

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe,
    }


def print_report(metrics_market: dict, metrics_strategy: dict, start_date: str):
    print("\n" + "=" * 60 + f"\n回测报告 ({start_date} 至今)")
    print("=" * 60)
    print(f"{'性能指标':<12}{'基准(一直持有)':>15}{'加入双均线策略':>16}")
    print("-" * 60)
    print(f"{'累计收益率':<12}{metrics_market['total_return']:>20.2%}{metrics_strategy['total_return']:>23.2%}")
    print(f"{'年化收益率':<12}{metrics_market['annual_return']:>20.2%}{metrics_strategy['annual_return']:>23.2%}")
    print(f"{'最大回撤':<12}{metrics_market['max_drawdown']:>21.2%}{metrics_strategy['max_drawdown']:>23.2%}")
    print(f"{'年化夏普比率':<12}{metrics_market['sharpe_ratio']:>19.2f}{metrics_strategy['sharpe_ratio']:>23.2f}")
    print("=" * 60)
    # :<13 :>20.2%都是格式化对齐 + 宽度 + 数字格式，:开始格式化指令
    # > — 右对齐
    # 20 — 总宽度 20 个字符
    # .2 — 小数点后保留 2 位
    # f — 浮点数格式
    # % — 百分比格式（自动乘以 100 并加 % 符号）
