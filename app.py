"""
Aplicación web para el control de gastos personales con registro de usuario.
"""
import os
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g
)
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import init_db, get_db

load_dotenv()


def crear_app() -> Flask:
    aplicacion = Flask(
        __name__, template_folder="plantillas", static_folder="css")
    aplicacion.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dont_break_me")

    def _to_float_or_none(x: str):
        x = (x or "").strip().replace(",", ".")
        try:
            return float(x) if x != "" else None
        except ValueError:
            return None

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                flash("Debes iniciar sesión.")
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    @aplicacion.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
        else:
            with get_db() as con:
                cur = con.cursor()
                g.user = cur.execute(
                    "SELECT id, nickname, email FROM users WHERE id = ?", (
                        user_id,)
                ).fetchone()

    @aplicacion.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "GET":
            return render_template("signup.html", exito=False)

        nickname = (request.form.get("nickname") or "").strip()
        email = (request.form.get("email") or "").strip() or None
        password = (request.form.get("password") or "").strip()

        if not nickname or not password:
            flash("Nickname y contraseña son obligatorios.")
            return render_template("signup.html", exito=False)

        pwd_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16)

        try:
            with get_db() as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO users (nickname, email, password_hash) VALUES (?, ?, ?)",
                    (nickname, email, pwd_hash),
                )
                con.commit()
        except Exception:
            flash("No se pudo registrar. ¿Nickname o email ya usados?")
            return render_template("signup.html", exito=False)

        return render_template("signup.html", exito=True)

    @aplicacion.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        nickname = (request.form.get("nickname") or "").strip()
        password = (request.form.get("password") or "").strip()

        with get_db() as con:
            cur = con.cursor()
            user = cur.execute(
                "SELECT * FROM users WHERE nickname = ?",
                (nickname,)
            ).fetchone()

        if not user:
            flash("Usuario sin registrar.")
            return render_template("login.html")

        if not check_password_hash(user["password_hash"], password):
            flash("El usuario y la contraseña no coinciden. Intentelo de nuevo")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        next_url = request.args.get("next") or url_for("inicio")
        return redirect(next_url)

    @aplicacion.get("/logout")
    def logout():
        session.clear()
        flash("Sesión cerrada.")
        return redirect(url_for("login"))

    @aplicacion.route("/")
    @login_required
    def inicio():
        """
        Listado con filtros y total del usuario logueado.
        """
        desde = (request.args.get("desde") or "").strip()
        hasta = (request.args.get("hasta") or "").strip()
        cantidad_min = _to_float_or_none(request.args.get("cantidad_min"))
        cantidad_max = _to_float_or_none(request.args.get("cantidad_max"))

        where = ["owner_id = ?"]
        params = [g.user["id"]]

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

        return render_template("index.html", gastos=gastos, total=total, user=g.user)

    @aplicacion.route("/nuevo", methods=["GET", "POST"])
    @login_required
    def nuevo_gasto():
        """
        Formulario de alta. Usa PRG (Post/Redirect/Get).
        """
        if request.method == "GET":
            exito = (request.args.get("ok") == "1")
            return render_template("form.html", exito=exito)

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
                "INSERT INTO gastos (cantidad, categoria, descripcion, fecha, owner_id) VALUES (?, ?, ?, ?, ?)",
                (cantidad, categoria, descripcion, fecha, g.user["id"]),
            )
            con.commit()

        return redirect(url_for("nuevo_gasto", ok=1))

    @aplicacion.post("/borrar/<int:gasto_id>")
    @login_required
    def borrar_gasto(gasto_id: int):
        """
        Elimina un gasto por id (solo si es del usuario).
        """
        with get_db() as con:
            cur = con.cursor()
            r = cur.execute(
                "DELETE FROM gastos WHERE id = ? AND owner_id = ?",
                (gasto_id, g.user["id"])
            )
            con.commit()
        if r.rowcount == 0:
            flash("No puedes borrar ese gasto.")
        else:
            flash("Gasto eliminado.")
        return redirect(url_for("inicio"))

    return aplicacion


app = crear_app()
init_db()

if __name__ == "__main__":
    app.run(debug=True)
