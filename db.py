import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "datos", "bbdd.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "datos"), exist_ok=True)

    conexion = get_db()
    cursor = conexion.cursor()

    sql = (
        "CREATE TABLE IF NOT EXISTS gastos ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "cantidad REAL NOT NULL, "
        "categoria TEXT NOT NULL, "
        "descripcion TEXT, "
        "fecha DATE NOT NULL"
        ");"
    )
    cursor.execute(sql)

    conexion.commit()
    conexion.close()
