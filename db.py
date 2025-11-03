import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "datos", "bbdd.db")


def get_db():
    # timeout evita “database is locked” en operaciones rápidas encadenadas
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    # ajustes razonables para este proyecto
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "datos"), exist_ok=True)

    ddl_tabla = """
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cantidad REAL NOT NULL CHECK (cantidad > 0),
        categoria TEXT NOT NULL,
        descripcion TEXT,
        fecha TEXT NOT NULL  -- ISO-8601 (YYYY-MM-DD) recomendado en SQLite
    );
    """

    ddl_idx_fecha = "CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha);"
    ddl_idx_cantidad = "CREATE INDEX IF NOT EXISTS idx_gastos_cantidad ON gastos(cantidad);"

    with get_db() as con:
        cur = con.cursor()
        cur.execute(ddl_tabla)
        cur.execute(ddl_idx_fecha)
        cur.execute(ddl_idx_cantidad)
        con.commit()
