"""PostgreSQL connectivity helpers (psycopg2)."""
from contextlib import contextmanager

import pandas as pd
import psycopg2
import psycopg2.extras

from backend.config import settings


def connect(admin: bool = False):
    return psycopg2.connect(**settings.dsn(admin=admin))


@contextmanager
def get_conn():
    """Transactional connection: commits on success, rolls back on error."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_df(sql: str, params=None, conn=None) -> pd.DataFrame:
    def _run(c):
        with c.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        # psycopg2 returns Decimal for NUMERIC; convert to float for analytics
        for col in df.columns:
            if len(df) and df[col].map(lambda v: type(v).__name__ == "Decimal").any():
                df[col] = df[col].astype(float)
        return df

    if conn is not None:
        return _run(conn)
    with get_conn() as c:
        return _run(c)


def fetch_all(sql: str, params=None, conn=None) -> list[dict]:
    return fetch_df(sql, params, conn).to_dict(orient="records")


def fetch_one(sql: str, params=None, conn=None):
    rows = fetch_all(sql, params, conn)
    return rows[0] if rows else None


def execute(sql: str, params=None, conn=None, returning: bool = False):
    def _run(c):
        with c.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0] if returning else cur.rowcount

    if conn is not None:
        return _run(conn)
    with get_conn() as c:
        return _run(c)


def insert_rows(conn, table: str, rows: list[dict], returning: str | None = None):
    """Bulk insert a list of homogeneous dicts."""
    if not rows:
        return []
    cols = list(rows[0].keys())
    values = [tuple(_py(r[c]) for c in cols) for r in rows]
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s"
    if returning:
        sql += f" RETURNING {returning}"
    with conn.cursor() as cur:
        res = psycopg2.extras.execute_values(cur, sql, values, page_size=1000, fetch=bool(returning))
    return [r[0] for r in res] if returning else []


def _py(v):
    """Convert numpy scalars to native Python for psycopg2."""
    if hasattr(v, "item"):
        return v.item()
    if isinstance(v, float) and v != v:  # NaN -> NULL
        return None
    return v


def ping() -> bool:
    try:
        with get_conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1")
            return cur.fetchone()[0] == 1
    except Exception:
        return False
