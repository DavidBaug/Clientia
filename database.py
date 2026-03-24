import sqlite3

class DBManager:
    def __init__(self, db_name="seguros.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
            dni_nif TEXT PRIMARY KEY, doc_alt TEXT, nombre TEXT NOT NULL, fecha_nac DATE,
            domicilio TEXT, numero TEXT, puerta TEXT, bloque TEXT, localidad TEXT,
            cp INTEGER, poblacion TEXT, pais TEXT DEFAULT 'España', tel1 TEXT, tel2 TEXT, 
            email TEXT, doc_elec BOOLEAN DEFAULT 0, sexo TEXT, estado TEXT, vip BOOLEAN DEFAULT 0)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS polizas (
            id_poliza TEXT PRIMARY KEY, dni_nif TEXT NOT NULL, aseguradora TEXT,
            mediador TEXT, figura TEXT, riesgo TEXT, fecha_inicio DATE, fecha_anulacion DATE,
            FOREIGN KEY(dni_nif) REFERENCES clientes(dni_nif) ON DELETE CASCADE)''')
        self.conn.commit()

    def consultar(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def ejecutar(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True, None
        except sqlite3.IntegrityError as e:
            return False, f"Conflicto de integridad (Ej: El DNI o ID ya existe): {e}"
        except sqlite3.Error as e:
            return False, f"Error de Base de Datos: {e}"

    # Añadir este método a la clase DBManager en database.py
    def obtener_lista_clientes(self):
        return self.consultar("SELECT dni_nif, nombre FROM clientes")