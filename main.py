import json
import os
import platform
import subprocess
import sys
from database import DBManager
from dialogs import EditorDialog, FichaClienteDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLineEdit,
                             QMainWindow, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget, QMenu)

CONFIG_FILE = "config_visibilidad.json"

class KeepOpenMenu(QMenu):
    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.pos())
        if action and action.isCheckable():
            action.trigger()
            # No llamamos a super().mouseReleaseEvent(event) para evitar que se cierre
        else:
            super().mouseReleaseEvent(event)


class SeguroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("favicon.ico"))
        self.db = DBManager()
        self.columnas_cli = ["DNI/NIF", "Doc. Alt", "Nombre", "Fecha Nacimiento", "Domicilio", "Número", "Puerta",
                             "Bloque", "Localidad", "CP", "Población", "País", "Tel1", "Tel2", "Email", "Doc. Elec",
                             "Sexo", "Estado", "VIP"]
        self.columnas_pol = ["ID Póliza", "DNI/NIF", "Aseguradora", "Mediador", "Figura", "Riesgo", "Fecha Inicio",
                             "Fecha Anulación", "Archivo PDF"]
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
        self.setWindowTitle("Sistema de Gestión de Seguros")
        self.resize(1200, 800)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # Menú de configuración persistente
        menu_cfg = self.menuBar().addMenu("⚙️ Opciones")

        # Creamos el submenú usando nuestra clase personalizada
        self.submenu_cols = KeepOpenMenu("Visibilidad de Columnas", self)
        menu_cfg.addMenu(self.submenu_cols)

        for col in self.columnas_cli:
            act = QAction(col, self, checkable=True)
            act.setChecked(self.visibilidad.get(col, True))
            # Usamos un truco: al cambiar, recargamos la tabla pero no el menú
            act.triggered.connect(lambda chk, c=col: self.toggle_col(c, chk))
            self.submenu_cols.addAction(act)

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
        t.setAlternatingRowColors(True)
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
                self.table_cli.setItem(r_idx, c_idx, QTableWidgetItem(str(r_data[db_idx])))
                # Guardamos el DNI real en el UserRole de la primera celda
                if c_idx == 0:
                    self.table_cli.item(r_idx, 0).setData(Qt.ItemDataRole.UserRole, r_data[0])

        # Pólizas
        p_rows = self.db.consultar("SELECT * FROM polizas WHERE dni_nif LIKE ? OR id_poliza LIKE ?", (f, f))
        self.table_pol.setColumnCount(len(self.columnas_pol))
        self.table_pol.setHorizontalHeaderLabels(self.columnas_pol)  # CORRECCIÓN: Faltaban cabeceras
        self.table_pol.setRowCount(len(p_rows))

        for r_idx, r_data in enumerate(p_rows):
            for c_idx, val in enumerate(r_data):
                if c_idx == 8 and val:  # Columna PDF
                    btn_open = QPushButton("📄 Ver PDF")
                    btn_open.clicked.connect(lambda chk, p=val: self.abrir_pdf_sistema(p))
                    self.table_pol.setCellWidget(r_idx, c_idx, btn_open)
                else:
                    self.table_pol.setItem(r_idx, c_idx, QTableWidgetItem(str(val) if val else "-"))

        # self.table_cli.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # self.table_cli.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def editar_poliza_especifica(self, id_poliza):
        datos = self.db.consultar("SELECT * FROM polizas WHERE id_poliza = ?", (id_poliza,))
        if not datos: return False

        lista_clientes = self.db.obtener_lista_clientes()
        diag = EditorDialog("Editar Póliza", self.columnas_pol, datos[0], lista_clientes, self)

        if diag.exec():
            vals = diag.get_data_list()
            exito = self.guardar_edicion_db("polizas", vals, id_poliza)
            self.load_data()
            return exito
        return False

    def nueva_poliza_especifica(self, dni_cliente):
        lista_clientes = self.db.obtener_lista_clientes()
        datos_iniciales = [None] * len(self.columnas_pol)
        datos_iniciales[1] = dni_cliente

        diag = EditorDialog("Nueva Póliza", self.columnas_pol, datos_iniciales, lista_clientes, self)
        if diag.exec():
            vals = diag.get_data_list()
            # El ID suele ser autoincremental, si es así, el primer valor debe ser None
            exito, msg = self.db.ejecutar(f"INSERT INTO polizas VALUES ({','.join(['?'] * len(self.columnas_pol))})",
                                          vals)
            if not exito:
                QMessageBox.critical(self, "Error", msg)
                return False
            self.load_data()
            return True
        return False

    def abrir_pdf_sistema(self, ruta_relativa):
        # Convertimos la ruta relativa de la DB en absoluta
        ruta_completa = os.path.join(os.getcwd(), ruta_relativa)

        if os.path.exists(ruta_completa):
            sistema = platform.system()
            try:
                if sistema == "Windows":
                    os.startfile(ruta_completa)
                elif sistema == "Darwin":  # macOS
                    subprocess.run(["open", ruta_completa])
                else:  # Linux (Ubuntu, etc.)
                    subprocess.run(["xdg-open", ruta_completa])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el visor de PDF: {e}")
        else:
            QMessageBox.warning(self, "Error", f"No se encuentra el archivo en:\n{ruta_completa}")

    def abrir_editor(self, tabla, edit=False):
        campos = self.columnas_cli if tabla == "clientes" else self.columnas_pol
        datos = None
        lista_clientes = self.db.obtener_lista_clientes() if tabla == "polizas" else None

        if edit:
            t = self.table_cli if tabla == "clientes" else self.table_pol
            row = t.currentRow()
            if row < 0: return
            # Obtener PK
            if tabla == "clientes":
                pk = t.item(row, 0).data(Qt.ItemDataRole.UserRole)
            else:
                pk = t.item(row, 0).text()

            col_pk = "dni_nif" if tabla == "clientes" else "id_poliza"
            query_res = self.db.consultar(f"SELECT * FROM {tabla} WHERE {col_pk} = ?", (pk,))
            if query_res: datos = query_res[0]

        diag = EditorDialog(f"{'Editar' if edit else 'Nuevo'} {tabla[:-1]}", campos, datos, lista_clientes, self)
        if diag.exec():
            vals = diag.get_data_list()
            if edit:
                self.guardar_edicion_db(tabla, vals, datos[0])
            else:
                exito, msg = self.db.ejecutar(f"INSERT INTO {tabla} VALUES ({','.join(['?'] * len(campos))})", vals)
                if not exito: QMessageBox.critical(self, "Error", msg)
            self.load_data()

    def guardar_edicion_db(self, tabla, vals, pk_original):
        if tabla == "clientes":
            cols_db = ["dni_nif", "doc_alt", "nombre", "fecha_nac", "domicilio", "numero", "puerta", "bloque",
                       "localidad", "cp", "poblacion", "pais", "tel1", "tel2", "email", "doc_elec", "sexo", "estado",
                       "vip"]
        else:
            cols_db = ["id_poliza", "dni_nif", "aseguradora", "mediador", "figura", "riesgo", "fecha_inicio",
                       "fecha_anulacion", "pdf_path"]

        sets = ", ".join([f"{c} = ?" for c in cols_db])
        exito, msg = self.db.ejecutar(f"UPDATE {tabla} SET {sets} WHERE {cols_db[0]} = ?", (*vals, pk_original))
        if not exito: QMessageBox.critical(self, "Error", msg)
        return exito

    def borrar_fila(self):
        idx = self.tabs.currentIndex()
        t = self.table_cli if idx == 0 else self.table_pol
        row = t.currentRow()
        if row < 0: return QMessageBox.warning(self, "Atención", "Selecciona un registro primero.")

        pk = t.item(row, 0).data(Qt.ItemDataRole.UserRole) if idx == 0 else t.item(row, 0).text()
        col = "dni_nif" if idx == 0 else "id_poliza"

        if QMessageBox.question(self, "Confirmar", f"¿Eliminar {pk}?") == QMessageBox.StandardButton.Yes:
            self.db.ejecutar(f"DELETE FROM {'clientes' if idx == 0 else 'polizas'} WHERE {col} = ?", (pk,))
            self.load_data()

    def abrir_detalle_cli(self):
        row = self.table_cli.currentRow()
        if row < 0: return
        dni = self.table_cli.item(row, 0).data(Qt.ItemDataRole.UserRole)
        datos = self.db.consultar("SELECT * FROM clientes WHERE dni_nif = ?", (dni,))[0]
        polizas = self.db.consultar("SELECT * FROM polizas WHERE dni_nif = ?", (dni,))
        diag = FichaClienteDialog(datos, polizas, self.columnas_cli, self)
        diag.exec()

    def abrir_detalle_pol(self):
        self.abrir_editor("polizas", edit=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeguroApp()
    window.show()
    sys.exit(app.exec())
