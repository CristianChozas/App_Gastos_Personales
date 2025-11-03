"""
Aplicación web para el control de gastos personales.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from db import init_db, get_db

load_dotenv()


def crear_app() -> Flask:
    """
    Crea y configura la aplicación Flask.
    """
    aplicacion = Flask(
        __name__, template_folder="plantillas", static_folder="css")
    aplicacion.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dont_break_me")

    # ---------- Helpers ----------
    def _to_float_or_none(x: str):
        x = (x or "").strip().replace(",", ".")
        try:
            return float(x) if x != "" else None
        except ValueError:
            return None

    # ---------- Rutas ----------
    @aplicacion.route("/")
    def inicio():
        """
        Listado con filtros y total coherente con los filtros.
        """
        desde = (request.args.get("desde") or "").strip()
        hasta = (request.args.get("hasta") or "").strip()
        cantidad_min = _to_float_or_none(request.args.get("cantidad_min"))
        cantidad_max = _to_float_or_none(request.args.get("cantidad_max"))

        where = ["1=1"]
        params = []

        if desde:
            where.append("fecha >= ?")
            params.append(desde)
        if hasta:
            where.append("fecha <= ?")
            params.append(hasta)
        if cantidad_min is not None:
            where.append("cantidad >= ?")
            params.append(cantidad_min)
        if cantidad_max is not None:
            where.append("cantidad <= ?")
            params.append(cantidad_max)

        where_sql = " AND ".join(where)

        with get_db() as con:
            cur = con.cursor()
            gastos = cur.execute(
                f"""
                SELECT id, cantidad, categoria, descripcion, fecha
                FROM gastos
                WHERE {where_sql}
                ORDER BY fecha DESC
                """,
                params,
            ).fetchall()

            total = cur.execute(
                f"SELECT COALESCE(SUM(cantidad), 0) AS total FROM gastos WHERE {where_sql}",
                params,
            ).fetchone()["total"]

        return render_template("index.html", gastos=gastos, total=total)

    @aplicacion.route("/nuevo", methods=["GET", "POST"])
    def nuevo_gasto():
        """
        Formulario de alta. Usa PRG (Post/Redirect/Get).
        """
        if request.method == "GET":
            exito = (request.args.get("ok") == "1")
            return render_template("form.html", exito=exito)

        # POST
        cantidad_raw = (request.form.get("cantidad")
                        or "").strip().replace(",", ".")
        categoria = (request.form.get("categoria") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        fecha = (request.form.get("fecha") or "").strip()

        try:
            cantidad = float(cantidad_raw)
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            flash("La cantidad no es válida. Debe ser un número mayor que 0.")
            return render_template("form.html")

        if not categoria or not fecha:
            flash("Categoría y fecha son obligatorias.")
            return render_template("form.html")

        with get_db() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO gastos (cantidad, categoria, descripcion, fecha) VALUES (?, ?, ?, ?)",
                (cantidad, categoria, descripcion, fecha),
            )
            con.commit()

        # Redirige para evitar reenvío del formulario y mostrar mensaje de éxito
        return redirect(url_for("nuevo_gasto", ok=1))

    @aplicacion.post("/borrar/<int:gasto_id>")
    def borrar_gasto(gasto_id: int):
        """
        Elimina un gasto por id.
        """
        with get_db() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
            con.commit()
        flash("Gasto eliminado.")
        return redirect(url_for("inicio"))

    return aplicacion


app = crear_app()
init_db()

if __name__ == "__main__":
    app.run(debug=True)
