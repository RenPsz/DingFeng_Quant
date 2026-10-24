import numpy as np
import pandas as pd
import pytest

from backtest import calculate_metrics, run_backtest
from signals.energy import energy_ratio
from signals.evaluate import evaluate, future_drawdown, lower_tail_alert, sign_flip_alert
from signals.spectrum import _single_window_ratio
from strategy import ma_cross_signal


@pytest.mark.unit
def test_future_drawdown_excludes_incomplete_tail_window():
    close = pd.Series([100, 90, 80, 85, 70], dtype=float)

    result = future_drawdown(close, horizon=2)

    assert result.iloc[:3].notna().all()
    assert result.iloc[0] == pytest.approx(-0.2)
    assert result.iloc[3:].isna().all()


@pytest.mark.unit
def test_alert_helpers_and_evaluate_respect_eligible_mask():
    factor = pd.Series([1.0, 2.0, -1.0, 1.0])
    target = pd.Series([False, True, True, True])
    eligible = pd.Series([True, True, False, True])

    assert sign_flip_alert(factor).tolist() == [False, False, True, False]
    assert evaluate(pd.Series([True, True, True, False]), target, eligible) == {
        "n_alerts": 2,
        "n_hits": 1,
        "hit_rate": 0.5,
    }
    assert lower_tail_alert(pd.Series([1, 2, 3]), lookback=2).dtype == bool


@pytest.mark.unit
def test_factor_edge_cases_are_defined():
    assert _single_window_ratio(np.zeros(8), 0.25) == 0.0
    frame = pd.DataFrame({"close": [100.0] * 10})
    assert energy_ratio(frame, short_window=2, long_window=3).dropna().isna().all()


@pytest.mark.unit
def test_ma_signal_is_lagged_and_backtest_applies_trade_costs():
    frame = pd.DataFrame({"close": [1.0, 1.0, 2.0, 3.0, 2.0]})
    position = ma_cross_signal(frame, fast=2, slow=3)
    assert position.iloc[0] == 0
    assert position.index.equals(frame.index)

    result = run_backtest(
        frame.assign(date=pd.date_range("2024-01-01", periods=5)),
        position,
        commission=0.1,
    )
    assert result.loc[0, "cum_market_wealth"] == pytest.approx(1.0)
    assert result.loc[3, "strategy_return"] == pytest.approx(0.4)


@pytest.mark.unit
def test_calculate_metrics_handles_zero_volatility():
    wealth = pd.Series([1.0, 1.1, 1.21])
    returns = pd.Series([0.0, 0.1, 0.1])

    metrics = calculate_metrics(wealth, returns)

    assert metrics["total_return"] == pytest.approx(0.21)
    assert metrics["sharpe_ratio"] != np.inf

