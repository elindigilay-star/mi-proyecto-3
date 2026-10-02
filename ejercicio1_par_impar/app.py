from contextlib import contextmanager

from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)

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


class ClasificadorParidad:
    CANTIDAD = 5

    @staticmethod
    def es_par(numero):
        return numero % 2 == 0

    @classmethod
    def clasificar(cls, numero):
        return "PAR" if cls.es_par(numero) else "IMPAR"

    @classmethod
    def primeros_pares(cls):
        return [n for n in range(1, 2 * cls.CANTIDAD + 1) if cls.es_par(n)]

    @classmethod
    def primeros_impares(cls):
        return [n for n in range(1, 2 * cls.CANTIDAD + 1) if not cls.es_par(n)]


class RepositorioParesImpares(BaseDeDatos):
    DDL = """CREATE TABLE IF NOT EXISTS pares_impares (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tipo VARCHAR(10) NOT NULL,
        valor INT NOT NULL
    )"""

    def guardar(self, pares, impares):
        with self.conexion() as cursor:
            cursor.executemany(
                "INSERT INTO pares_impares (tipo, valor) VALUES (%s, %s)",
                [("par", n) for n in pares] + [("impar", n) for n in impares],
            )

    def ultimos(self, tipo, cantidad):
        with self.conexion() as cursor:
            cursor.execute(
                "SELECT valor FROM pares_impares WHERE tipo=%s ORDER BY id DESC LIMIT %s",
                (tipo, cantidad),
            )
            return [fila[0] for fila in cursor.fetchall()]


repositorio = RepositorioParesImpares(DB_CONFIG)


@app.route("/", methods=["GET", "POST"])
def par_impar():
    resultado = None
    primeros_pares = []
    primeros_impares = []

    if request.method == "POST":
        numero = int(request.form["numero"])
        resultado = f"El número {numero} es {ClasificadorParidad.clasificar(numero)}"

        primeros_pares = ClasificadorParidad.primeros_pares()
        primeros_impares = ClasificadorParidad.primeros_impares()
        repositorio.guardar(primeros_pares, primeros_impares)

    historial_pares = repositorio.ultimos("par", ClasificadorParidad.CANTIDAD)
    historial_impares = repositorio.ultimos("impar", ClasificadorParidad.CANTIDAD)

    return render_template(
        "index.html",
        resultado=resultado,
        primeros_pares=primeros_pares,
        primeros_impares=primeros_impares,
        historial_pares=historial_pares,
        historial_impares=historial_impares,
    )


if __name__ == "__main__":
    repositorio.inicializar()
    app.run(debug=True)