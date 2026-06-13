"""存储层：SQLite 本地缓存，负责行情数据的落库与读取"""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "cache" / "market.db"
OHLCV = ['open', 'close', 'high', 'low', 'volume']


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """建表，幂等"""
    "创建股票，指数日k表"
    "创建交易日历表"
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily (
                symbol TEXT NOT NULL,
                date   TEXT NOT NULL,
                open   REAL,
                close  REAL,
                high   REAL,
                low    REAL,
                volume REAL,
                PRIMARY KEY (symbol, date)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_calendar (
                date TEXT PRIMARY KEY
            )
        """)

def upsert_calendar(dates: list[str]) -> None:
    """写入交易日历"""
    with _connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO trade_calendar (date) VALUES (?)",
            [(d,) for d in dates]
        )


def get_last_trade_date(reference: str) -> str | None:
    """返回 reference 日期当天或之前最近的交易日，无数据返回 None"""
    with _connect() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM trade_calendar WHERE date <= ?",
            (reference,)
        ).fetchone()
    return row[0] if row and row[0] else None


def get_calendar_last_date() -> str | None:
    """返回交易日历表中最新的日期"""
    with _connect() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM trade_calendar"
        ).fetchone()
    return row[0] if row and row[0] else None


def get_last_date(symbol: str) -> str | None:
    """返回该 symbol 缓存中的最新日期，无数据返回 None"""
    with _connect() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM daily WHERE symbol = ?", (symbol,)
        ).fetchone()
    return row[0] if row and row[0] else None


def read_daily(symbol: str) -> pd.DataFrame:
    """读取该 symbol 的全部缓存，按日期升序"""
    with _connect() as conn:
        df = pd.read_sql_query(
            "SELECT date, open, close, high, low, volume "
            "FROM daily WHERE symbol = ? ORDER BY date",
            conn, params=(symbol,)
        )
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


def upsert_daily(symbol: str, df: pd.DataFrame) -> None:
    """写入/更新行情，df 需含 date + OHLCV 列"""
    if df.empty:
        return
    out = df.copy()
    out['symbol'] = symbol
    out['date'] = pd.to_datetime(out['date']).dt.strftime('%Y-%m-%d')
    out = out[['symbol', 'date'] + OHLCV]
    with _connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO daily "
            "(symbol, date, open, close, high, low, volume) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            out.itertuples(index=False, name=None)
        )