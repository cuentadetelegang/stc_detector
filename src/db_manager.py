import mysql.connector as mc
from datetime import datetime

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "RootMySQL123!"
DB_NAME = "stc_detector"
DB_PORT = 3306


class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.conectar()

    # ───────── Conexión ─────────
    def conectar(self):
        if self.conn is None or not self.conn.is_connected():
            self.conn = mc.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
            )

    # ───────── Pacientes ────────
    def agregar_paciente(self, nombre, edad, genero, mano):
        self.conectar()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO pacientes (nombre, edad, genero, mano_dominante) "
            "VALUES (%s, %s, %s, %s)",
            (nombre, edad, genero, mano),
        )
        self.conn.commit()
        return cur.lastrowid

    # ───────── Pruebas ──────────
    def crear_prueba(self, id_paciente):
        self.conectar()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO pruebas (id_paciente, fecha) VALUES (%s, %s)",
            (id_paciente, datetime.now()),
        )
        self.conn.commit()
        return cur.lastrowid

    def guardar_resultado(self, id_prueba, resultado):
        self.conectar()
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE pruebas SET resultado=%s WHERE id_prueba=%s",
            (resultado, id_prueba),
        )
        self.conn.commit()

    # ───────── Muestras ─────────
    def guardar_muestra(self, id_prueba, x, y, z):
        self.conectar()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO datos_giroscopio (id_prueba, eje_x, eje_y, eje_z) "
            "VALUES (%s, %s, %s, %s)",
            (id_prueba, x, y, z),
        )
        self.conn.commit()

    # ───────── Historial ────────
    def obtener_historial(self, id_paciente):
        """Devuelve lista [(fecha, resultado)] ordenada de más reciente a más antigua."""
        self.conectar()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT fecha, resultado FROM pruebas "
            "WHERE id_paciente=%s ORDER BY fecha DESC",
            (id_paciente,),
        )
        return cur.fetchall()
