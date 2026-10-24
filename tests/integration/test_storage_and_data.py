from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest

from data import data, storage


@pytest.fixture
def isolated_db(monkeypatch):
    db_path = Path("tests") / f".market-{uuid4().hex}.db"
    monkeypatch.setattr(storage, "DB_PATH", db_path)
    yield storage
    for suffix in ("", "-wal", "-shm"):
        path = Path(f"{db_path}{suffix}")
        if path.exists():
            path.unlink()


@pytest.mark.integration
def test_storage_upsert_is_idempotent_and_sorted(isolated_db):
    frame = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-01", "2024-01-02"],
            "open": [2, 1, 20],
            "close": [2, 1, 20],
            "high": [2, 1, 20],
            "low": [2, 1, 20],
            "volume": [2, 1, 20],
        }
    )
    isolated_db.upsert_daily("demo", frame)

    result = isolated_db.read_daily("demo")

    assert result["date"].tolist() == list(pd.to_datetime(["2024-01-01", "2024-01-02"]))
    assert result.loc[result["date"] == "2024-01-02", "close"].iloc[0] == 20


@pytest.mark.integration
def test_force_refresh_removes_stale_rows_and_clean_does_not_mutate(isolated_db, monkeypatch):
    old = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "open": [1, 2], "close": [1, 2], "high": [1, 2],
            "low": [1, 2], "volume": [1, 2],
        }
    )
    isolated_db.upsert_daily("demo", old)
    source = pd.DataFrame(
        {
            "date": ["2024-01-03"], "open": [3], "close": [3],
            "high": [3], "low": [3], "volume": [3],
        }
    )
    original = source.copy(deep=True)

    data._cached_fetch("demo", lambda _: source, force_refresh=True)

    assert source.equals(original)
    assert isolated_db.read_daily("demo")["date"].tolist() == [pd.Timestamp("2024-01-03")]


@pytest.mark.integration
def test_qfq_sync_uses_full_refresh_when_cache_exists(isolated_db, monkeypatch):
    cached = pd.DataFrame(
        {
            "date": ["2024-01-01"], "open": [1], "close": [1],
            "high": [1], "low": [1], "volume": [1],
        }
    )
    isolated_db.upsert_daily("sh600519_qfq", cached)
    monkeypatch.setattr(data, "_get_last_trade_date", lambda: "2024-01-03")
    calls = []

    def fetch(*, symbol, start_date, adjust):
        calls.append(start_date)
        return pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-03"],
                "open": [10, 30], "close": [10, 30],
                "high": [10, 30], "low": [10, 30], "volume": [10, 30],
            }
        )

    monkeypatch.setattr(data.ak, "stock_zh_a_daily", fetch)
    result = data.get_stock_data("sh600519", adjust="qfq")

    assert calls == ["20150101"]
    assert result["date"].tolist() == list(pd.to_datetime(["2024-01-01", "2024-01-03"]))

