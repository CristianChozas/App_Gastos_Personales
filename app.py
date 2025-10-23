"""
Aplicación web para el control de gastos personales.
Se crea la aplicacion y define qué página se muestra cuando entras en la web.
"""

import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()


def crear_app():
    """
    Crea y prepara la app.
    Configuración de rutas, las plantillas (archivos .html) y css.
    Queda lista la página incial que se muestra cuando entras a la web por primera vez.
    """
    aplicacion = Flask(
        __name__,
        template_folder="plantillas",
        static_folder="css"
    )

    aplicacion.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dont_break_me")

    @aplicacion.route("/")
    def inicio():
        "Página principal de la web"
        return render_template("index.html")

    return aplicacion


app = crear_app()

if __name__ == "__main__":
    app.run(debug=True)
