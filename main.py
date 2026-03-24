import sys, json, os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLineEdit, QPushButton, QTabWidget, QHeaderView, QMessageBox)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from database import DBManager
from dialogs import EditorDialog, FichaClienteDialog

CONFIG_FILE = "config_visibilidad.json"


class SeguroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.columnas_cli = ["DNI/NIF", "Doc. Alt", "Nombre", "Fecha Nacimiento", "Domicilio", "Número", "Puerta",
                             "Bloque", "Localidad", "CP", "Población", "País", "Tel1", "Tel2", "Email", "Doc. Elec",
                             "Sexo", "Estado", "VIP"]
        self.columnas_pol = ["ID Póliza", "DNI/NIF", "Aseguradora", "Mediador", "Figura", "Riesgo", "Fecha Inicio",
                             "Fecha Anulación"]
        self.cargar_config()
        self.init_ui()

    def cargar_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.visibilidad = json.load(f)
        else:
            self.visibilidad = {col: True for col in self.columnas_cli}

    def guardar_config(self):
        with open(CONFIG_FILE, "w") as f: json.dump(self.visibilidad, f)

    def init_ui(self):
        self.setWindowTitle("Sistema de Gestión de Seguros v3.0")
        self.resize(1200, 800)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # Menú de configuración persistente
        menu_cfg = self.menuBar().addMenu("⚙️ Opciones")
        submenu = menu_cfg.addMenu("Visibilidad de Columnas")
        for col in self.columnas_cli:
            act = QAction(col, self, checkable=True)
            act.setChecked(self.visibilidad.get(col, True))
            act.triggered.connect(lambda chk, c=col: self.toggle_col(c, chk))
            submenu.addAction(act)

        # Barra de Búsqueda y Herramientas
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Filtrar por nombre o identificación del cliente...")
        self.search.textChanged.connect(self.load_data)
        bar.addWidget(self.search)

        btn_cli = QPushButton("➕ Nuevo Cliente")
        btn_cli.clicked.connect(lambda: self.abrir_editor("clientes"))
        btn_pol = QPushButton("📜 Nueva Póliza")
        btn_pol.clicked.connect(lambda: self.abrir_editor("polizas"))
        btn_del = QPushButton("🗑️ Eliminar")
        btn_del.clicked.connect(self.borrar_fila)

        for b in [btn_cli, btn_pol, btn_del]: bar.addWidget(b)
        layout.addLayout(bar)

        self.tabs = QTabWidget()
        self.table_cli = self.config_tabla(self.abrir_detalle_cli)
        self.table_pol = self.config_tabla(self.abrir_detalle_pol)
        self.tabs.addTab(self.table_cli, "Listado de Clientes")
        self.tabs.addTab(self.table_pol, "Listado de Pólizas")
        layout.addWidget(self.tabs)

        self.setCentralWidget(main_widget)
        self.load_data()

    def config_tabla(self, func):
        t = QTableWidget()
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.doubleClicked.connect(func)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setAlternatingRowColors(True)  # Ayuda a la legibilidad visual
        return t

    def toggle_col(self, col, state):
        self.visibilidad[col] = state
        self.guardar_config()
        self.load_data()

    def load_data(self):
        f = f"%{self.search.text()}%"
        # Clientes
        cols_act = [c for c in self.columnas_cli if self.visibilidad.get(c, True)]
        idxs_act = [i for i, c in enumerate(self.columnas_cli) if self.visibilidad.get(c, True)]
        rows = self.db.consultar("SELECT * FROM clientes WHERE dni_nif LIKE ? OR nombre LIKE ?", (f, f))

        self.table_cli.setColumnCount(len(cols_act))
        self.table_cli.setHorizontalHeaderLabels(cols_act)
        self.table_cli.setRowCount(len(rows))
        for r_idx, r_data in enumerate(rows):
            for c_idx, db_idx in enumerate(idxs_act):
                item = QTableWidgetItem(str(r_data[db_idx]))
                item.setData(Qt.ItemDataRole.UserRole, r_data[0])
                self.table_cli.setItem(r_idx, c_idx, item)

        # Pólizas
        p_rows = self.db.consultar("SELECT * FROM polizas WHERE dni_nif LIKE ? OR id_poliza LIKE ?", (f, f))
        self.table_pol.setColumnCount(len(self.columnas_pol))
        self.table_pol.setHorizontalHeaderLabels(self.columnas_pol)
        self.table_pol.setRowCount(len(p_rows))
        for r_idx, r_data in enumerate(p_rows):
            for c_idx, val in enumerate(r_data):
                self.table_pol.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def abrir_editor(self, tabla, edit=False):
        campos = self.columnas_cli if tabla == "clientes" else self.columnas_pol
        datos = None
        lista_clientes = None

        # Si vamos a crear/editar una póliza, cargamos los clientes para el buscador
        if tabla == "polizas":
            lista_clientes = self.db.obtener_lista_clientes()

        if edit:
            t = self.table_cli if tabla == "clientes" else self.table_pol
            row = t.currentRow()
            if row < 0: return
            pk = t.item(row, 0).data(Qt.ItemDataRole.UserRole) if tabla == "clientes" else t.item(row, 0).text()
            col_pk = "dni_nif" if tabla == "clientes" else "id_poliza"
            datos = self.db.consultar(f"SELECT * FROM {tabla} WHERE {col_pk} = ?", (pk,))[0]

        # Pasamos lista_clientes al diálogo
        diag = EditorDialog(f"{'Editar' if edit else 'Nuevo'} {tabla[:-1]}", campos, datos, lista_clientes, self)
        if diag.exec():
            vals = diag.get_data_list()

            exito, msg = False, "Operación desconocida"
            if edit:
                cols_db = ["dni_nif", "doc_alt", "nombre", "fecha_nac", "domicilio", "numero", "puerta", "bloque",
                           "localidad", "cp", "poblacion", "pais", "tel1", "tel2", "email", "doc_elec", "sexo",
                           "estado", "vip"] if tabla == "clientes" else ["id_poliza", "dni_nif", "aseguradora",
                                                                         "mediador", "figura", "riesgo", "fecha_inicio",
                                                                         "fecha_anulacion"]
                sets = ", ".join([f"{c} = ?" for c in cols_db])
                exito, msg = self.db.ejecutar(f"UPDATE {tabla} SET {sets} WHERE {cols_db[0]} = ?", (*vals, datos[0]))
            else:
                exito, msg = self.db.ejecutar(f"INSERT INTO {tabla} VALUES ({','.join(['?'] * len(campos))})", vals)

            if not exito:
                QMessageBox.critical(self, "Error de Guardado", msg)
            self.load_data()

    def borrar_fila(self):
        idx = self.tabs.currentIndex()
        t = self.table_cli if idx == 0 else self.table_pol
        row = t.currentRow()
        if row < 0: return QMessageBox.warning(self, "Atención", "Selecciona un registro primero.")
        pk = t.item(row, 0).data(Qt.ItemDataRole.UserRole) if idx == 0 else t.item(row, 0).text()
        col = "dni_nif" if idx == 0 else "id_poliza"
        if QMessageBox.question(self, "Confirmar Eliminación",
                                f"¿Eliminar registro {pk}?") == QMessageBox.StandardButton.Yes:
            exito, msg = self.db.ejecutar(f"DELETE FROM {'clientes' if idx == 0 else 'polizas'} WHERE {col} = ?", (pk,))
            if not exito: QMessageBox.critical(self, "Error al borrar", msg)
            self.load_data()

    def abrir_detalle_cli(self):
        row = self.table_cli.currentRow()
        if row < 0: return
        dni = self.table_cli.item(row, 0).data(Qt.ItemDataRole.UserRole)

        # Obtener datos completos y sus pólizas
        datos = self.db.consultar("SELECT * FROM clientes WHERE dni_nif = ?", (dni,))[0]
        polizas = self.db.consultar("SELECT * FROM polizas WHERE dni_nif = ?", (dni,))

        # Abrir la nueva Ficha en lugar del editor directo
        diag = FichaClienteDialog(datos, polizas, self.columnas_cli, self)
        diag.exec()

    def guardar_edicion_db(self, tabla, vals, pk_original):
        """Método auxiliar para que los diálogos puedan ordenar el guardado"""
        cols_db = ["dni_nif", "doc_alt", "nombre", "fecha_nac", "domicilio", "numero", "puerta", "bloque", "localidad",
                   "cp", "poblacion", "pais", "tel1", "tel2", "email", "doc_elec", "sexo", "estado",
                   "vip"] if tabla == "clientes" else ["id_poliza", "dni_nif", "aseguradora", "mediador", "figura",
                                                       "riesgo", "fecha_inicio", "fecha_anulacion"]
        sets = ", ".join([f"{c} = ?" for c in cols_db])
        exito, msg = self.db.ejecutar(f"UPDATE {tabla} SET {sets} WHERE {cols_db[0]} = ?", (*vals, pk_original))
        if not exito:
            QMessageBox.critical(self, "Error", msg)
        return exito

    def abrir_detalle_pol(self):
        self.abrir_editor("polizas", edit=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeguroApp()
    window.show()
    sys.exit(app.exec())