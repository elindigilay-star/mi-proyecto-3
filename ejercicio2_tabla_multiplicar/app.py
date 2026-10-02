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


class TablaMultiplicar:
    FACTORES = range(1, 11)

    def __init__(self, numero):
        self.numero = numero
        self.filas = [(numero, factor, numero * factor) for factor in self.FACTORES]

    @classmethod
    def desde_filas(cls, filas):
        tabla = cls(filas[0][0])
        tabla.filas = filas
        return tabla

    def __iter__(self):
        return iter(self.filas)

    def __len__(self):
        return len(self.filas)

    def __getitem__(self, indice):
        return self.filas[indice]

    def __eq__(self, otro):
        return isinstance(otro, TablaMultiplicar) and self.filas == otro.filas

    def __repr__(self):
        return f"TablaMultiplicar({self.numero}) - {len(self)} filas"


class RepositorioTablas(BaseDeDatos):
    DDL = """CREATE TABLE IF NOT EXISTS tablas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        numero INT NOT NULL,
        factor INT NOT NULL,
        resultado INT NOT NULL
    )"""

    def guardar(self, tabla):
        with self.conexion() as cursor:
            cursor.executemany(
                "INSERT INTO tablas (numero, factor, resultado) VALUES (%s, %s, %s)",
                tabla,
            )

    def ultimas_filas(self, cantidad):
        with self.conexion() as cursor:
            cursor.execute(
                "SELECT numero, factor, resultado FROM tablas ORDER BY id DESC LIMIT %s",
                (cantidad,),
            )
            return cursor.fetchall()

    def ultima_tabla(self):
        filas = self.ultimas_filas(len(TablaMultiplicar.FACTORES))
        return TablaMultiplicar.desde_filas(filas) if filas else None


repositorio = RepositorioTablas(DB_CONFIG)


@app.route("/", methods=["GET", "POST"])
def tabla_multiplicar():
    tabla = None
    numero = None

    if request.method == "POST":
        numero = int(request.form["numero"])
        tabla = TablaMultiplicar(numero)
        repositorio.guardar(tabla)

    historial = repositorio.ultimas_filas(10)

    return render_template("index.html", tabla=tabla, numero=numero, historial=historial)


if __name__ == "__main__":
    repositorio.inicializar()
    app.run(debug=True)