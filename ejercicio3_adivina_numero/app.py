import random
from contextlib import contextmanager

from flask import Flask, render_template, request, session
import pymysql

app = Flask(__name__)
app.secret_key = "secreto123"

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "ejercicios_flask",
    "charset": "utf8mb4",
}


class BaseDeDatos:
    def __init__(self, config):
        self.config = config

    @contextmanager
    def conexion(self, con_bd=True):
        config = self.config if con_bd else {**self.config, "database": None}
        conn = pymysql.connect(**config)
        try:
            yield conn.cursor()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def inicializar(self):
        with self.conexion(con_bd=False) as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            cursor.execute(f"USE {self.config['database']}")
            cursor.execute(self.DDL)


class JuegoAdivina:
    MINIMO = 1
    MAXIMO = 100

    def __init__(self, numero_secreto, total_intentos=0):
        self.numero_secreto = numero_secreto
        self.total_intentos = total_intentos
        self.adivinado = False

    @classmethod
    def iniciar(cls):
        return cls(random.randint(cls.MINIMO, cls.MAXIMO))

    @classmethod
    def desde_dict(cls, datos):
        return cls(datos["secreto"], datos["intentos"])

    def registrar_intento(self, intento):
        self.total_intentos += 1
        if intento < self.numero_secreto:
            return "El numero secreto es MAYOR"
        if intento > self.numero_secreto:
            return "El numero secreto es MENOR"
        self.adivinado = True
        return "Felicidades, adivinaste"

    @property
    def terminado(self):
        return self.adivinado

    def to_dict(self):
        return {"secreto": self.numero_secreto, "intentos": self.total_intentos}


class RepositorioIntentos(BaseDeDatos):
    DDL = """CREATE TABLE IF NOT EXISTS intentos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        numero_secreto INT NOT NULL,
        intento INT NOT NULL,
        total_intentos INT NOT NULL
    )"""

    def guardar(self, juego, intento):
        with self.conexion() as cursor:
            cursor.execute(
                """INSERT INTO intentos (numero_secreto, intento, total_intentos)
                   VALUES (%s, %s, %s)""",
                (juego.numero_secreto, intento, juego.total_intentos),
            )

    def ultimos(self, cantidad):
        with self.conexion() as cursor:
            cursor.execute(
                """SELECT numero_secreto, intento, total_intentos
                   FROM intentos ORDER BY id DESC LIMIT %s""",
                (cantidad,),
            )
            return cursor.fetchall()

    def ultimo_juego(self):
        filas = self.ultimos(1)
        if not filas:
            return None
        secreto, _, total = filas[0]
        return JuegoAdivina(secreto, total)


repositorio = RepositorioIntentos(DB_CONFIG)


@app.route("/", methods=["GET", "POST"])
def adivina_numero():
    if "juego" in session:
        juego = JuegoAdivina.desde_dict(session["juego"])
    else:
        juego = JuegoAdivina.iniciar()
        session["juego"] = juego.to_dict()

    mensaje = None

    if request.method == "POST":
        intento = int(request.form["intento"])
        mensaje = juego.registrar_intento(intento)
        repositorio.guardar(juego, intento)

        if juego.terminado:
            session.pop("juego", None)
        else:
            session["juego"] = juego.to_dict()

    historial = repositorio.ultimos(10)

    return render_template(
        "index.html",
        mensaje=mensaje,
        ganador=juego.terminado,
        total_intentos=juego.total_intentos,
        historial=historial,
    )


if __name__ == "__main__":
    repositorio.inicializar()
    app.run(debug=True)