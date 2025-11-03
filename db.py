import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "datos", "bbdd.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def _col_exists(con: sqlite3.Connection, table: str, col: str) -> bool:
    cur = con.execute(f"PRAGMA table_info({table})")
    return any(r["name"] == col for r in cur.fetchall())


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "datos"), exist_ok=True)

    ddl_gastos = """
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cantidad REAL NOT NULL CHECK (cantidad > 0),
        categoria TEXT NOT NULL,
        descripcion TEXT,
        fecha TEXT NOT NULL  -- ISO-8601 (YYYY-MM-DD) recomendado en SQLite
    );
    """

    idx_gastos_fecha = "CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha);"
    idx_gastos_cantidad = "CREATE INDEX IF NOT EXISTS idx_gastos_cantidad ON gastos(cantidad);"

    ddl_users = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL UNIQUE,
        email TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """

    with get_db() as con:
        cur = con.cursor()

        cur.execute(ddl_gastos)
        cur.execute(ddl_users)

        cur.execute(idx_gastos_fecha)
        cur.execute(idx_gastos_cantidad)

        version = cur.execute("PRAGMA user_version").fetchone()[0] or 0

        if version < 1:
            if not _col_exists(con, "gastos", "owner_id"):
                cur.execute(
                    "ALTER TABLE gastos ADD COLUMN owner_id INTEGER REFERENCES users(id)"
                )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_gastos_owner ON gastos(owner_id);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_gastos_owner_fecha ON gastos(owner_id, fecha);"
            )
            cur.execute("PRAGMA user_version = 1")

        con.commit()
