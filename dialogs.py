from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QLabel, QScrollArea,
                             QWidget, QDateEdit, QCheckBox, QComboBox, QMessageBox,
                             QCompleter, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QDate, Qt


class EditorDialog(QDialog):
    # (Mantenemos la clase EditorDialog igual que en el paso anterior)
    def __init__(self, titulo, campos, datos=None, lista_clientes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(500, 650)
        self.inputs = {}
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form = QFormLayout(container)

        for i, nombre in enumerate(campos):
            if nombre == "DNI/NIF" and lista_clientes is not None:
                widget = QComboBox()
                widget.setEditable(True)
                items = [f"{c[0]} - {c[1]}" for c in lista_clientes]
                widget.addItems(items)
                completer = QCompleter(items)
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
                widget.setCompleter(completer)
                if datos: widget.setCurrentText(str(datos[i]))
            elif "fecha" in nombre.lower():
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("yyyy-MM-dd")
                if datos and datos[i]:
                    widget.setDate(QDate.fromString(datos[i], "yyyy-MM-dd"))
                else:
                    widget.setDate(QDate.currentDate())
            elif nombre.lower() in ["vip", "doc. elec", "doc_elec"]:
                widget = QCheckBox()
                if datos: widget.setChecked(bool(datos[i]))
            elif nombre.lower() == "sexo":
                widget = QComboBox();
                widget.addItems(["No Especificado", "Varón", "Mujer"])
                if datos: widget.setCurrentText(datos[i])
            elif nombre.lower() == "estado":
                widget = QComboBox();
                widget.addItems(["Activo", "Inactivo", "Pendiente"])
                if datos: widget.setCurrentText(datos[i])
            else:
                widget = QLineEdit()
                if datos:
                    widget.setText(str(datos[i]) if datos[i] else "")
                    if i == 0: widget.setReadOnly(True)
            self.inputs[nombre] = widget
            self.form.addRow(QLabel(nombre), widget)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        btns = QHBoxLayout()
        btn_save = QPushButton("Guardar Cambios")
        btn_save.clicked.connect(self.validar_y_aceptar)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def get_data_dict(self):
        res = {}
        for nombre, widget in self.inputs.items():
            if isinstance(widget, QDateEdit):
                res[nombre] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QCheckBox):
                res[nombre] = "1" if widget.isChecked() else "0"
            elif isinstance(widget, QComboBox):
                texto = widget.currentText()
                res[nombre] = texto.split(" - ")[0].strip() if " - " in texto else texto.strip()
            else:
                res[nombre] = widget.text()
        return res

    def validar_y_aceptar(self):
        vals = self.get_data_dict()
        if not vals.get("DNI/NIF"):
            QMessageBox.warning(self, "Error", "El DNI/NIF es obligatorio.")
            return
        self.accept()

    def get_data_list(self):
        return list(self.get_data_dict().values())


class FichaClienteDialog(QDialog):
    def __init__(self, datos_cliente, polizas, columnas_cli, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ficha de Cliente: {datos_cliente[2]}")
        self.resize(700, 800)
        self.datos_actuales = datos_cliente
        self.columnas_cli = columnas_cli
        self.parent_app = parent  # Para llamar a la lógica de guardado de main.py
        self.init_ui(polizas)

    def init_ui(self, polizas):
        self.layout = QVBoxLayout(self)

        # SECCIÓN 1: DATOS (Vista de Lectura)
        group_datos = QGroupBox("Información Personal")
        self.form_info = QFormLayout()
        self.actualizar_labels()
        group_datos.setLayout(self.form_info)

        scroll = QScrollArea()
        scroll.setWidget(group_datos)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(350)
        self.layout.addWidget(scroll)

        # SECCIÓN 2: TABLA DE PÓLIZAS
        group_pol = QGroupBox(f"Pólizas Vinculadas ({len(polizas)})")
        ly_pol = QVBoxLayout()
        tabla = QTableWidget(len(polizas), 4)
        tabla.setHorizontalHeaderLabels(["ID Póliza", "Aseguradora", "Riesgo", "Inicio"])
        for i, p in enumerate(polizas):
            tabla.setItem(i, 0, QTableWidgetItem(str(p[0])))
            tabla.setItem(i, 1, QTableWidgetItem(str(p[2])))
            tabla.setItem(i, 2, QTableWidgetItem(str(p[5])))
            tabla.setItem(i, 3, QTableWidgetItem(str(p[6])))
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ly_pol.addWidget(tabla)
        group_pol.setLayout(ly_pol)
        self.layout.addWidget(group_pol)

        # SECCIÓN 3: BOTONES
        btns = QHBoxLayout()
        btn_edit = QPushButton("✏️ Editar Datos")
        btn_edit.clicked.connect(self.abrir_edicion)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_edit)
        btns.addStretch()
        btns.addWidget(btn_close)
        self.layout.addLayout(btns)

    def actualizar_labels(self):
        # Limpiar form si ya existe
        while self.form_info.count():
            child = self.form_info.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        for i, nombre in enumerate(self.columnas_cli):
            val = str(self.datos_actuales[i]) if self.datos_actuales[i] not in [None, "", 0, "0"] else "-"
            # Estilo visual para VIP
            if nombre == "VIP" and val == "1":
                val = "⭐ SÍ"
            elif nombre == "VIP":
                val = "No"
            self.form_info.addRow(QLabel(f"<b>{nombre}:</b>"), QLabel(val))

    def abrir_edicion(self):
        diag = EditorDialog("Editar Cliente", self.columnas_cli, self.datos_actuales, None, self)
        if diag.exec():
            nuevos_datos = diag.get_data_list()
            # Llamamos al método de guardado en la app principal
            if self.parent_app.guardar_edicion_db("clientes", nuevos_datos, self.datos_actuales[0]):
                self.datos_actuales = nuevos_datos
                self.actualizar_labels()
                self.parent_app.load_data()  # Refrescar tabla principal