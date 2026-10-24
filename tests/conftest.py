from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def price_data() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=320, freq="D")
    close = 100 + np.linspace(0, 30, len(dates))
    close[220:] -= np.linspace(0, 35, len(close[220:]))
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "close": close,
            "high": close + 1,
            "low": close - 1,
            "volume": np.full(len(dates), 1000.0),
        }
    )

