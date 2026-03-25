import os
import shutil
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDateEdit, QDialog,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QScrollArea, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)


class EditorDialog(QDialog):
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
            widget = None

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
                if datos: widget.setChecked(str(datos[i]) == "1")

            elif nombre.lower() == "sexo":
                widget = QComboBox()
                widget.addItems(["No Especificado", "Varón", "Mujer"])
                if datos: widget.setCurrentText(datos[i])

            elif nombre.lower() == "estado":
                widget = QComboBox()
                widget.addItems(["Activo", "Inactivo", "Pendiente"])
                if datos: widget.setCurrentText(datos[i])

            elif "pdf" in nombre.lower() or "archivo" in nombre.lower():
                contenedor = QWidget()
                btn_layout = QHBoxLayout(contenedor)
                btn_layout.setContentsMargins(0, 0, 0, 0)

                self.campo_ruta_pdf = QLineEdit()
                self.campo_ruta_pdf.setPlaceholderText("Seleccione archivo...")
                if datos and datos[i]:
                    self.campo_ruta_pdf.setText(str(datos[i]))

                btn_browse = QPushButton("📁 Cargar...")
                btn_browse.clicked.connect(self.seleccionar_y_copiar_pdf)

                btn_layout.addWidget(self.campo_ruta_pdf)
                btn_layout.addWidget(btn_browse)

                self.inputs[nombre] = self.campo_ruta_pdf
                self.form.addRow(QLabel(nombre), contenedor)
                continue

            else:
                widget = QLineEdit()
                if datos:
                    widget.setText(str(datos[i]) if datos[i] is not None else "")
                    if i == 0: widget.setReadOnly(True)

            if widget:
                self.inputs[nombre] = widget
                self.form.addRow(QLabel(nombre), widget)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        btns = QHBoxLayout()
        btn_save = QPushButton("Guardar Cambios")
        btn_save.clicked.connect(self.validar_y_aceptar)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def seleccionar_y_copiar_pdf(self):
        archivo_origen, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF (*.pdf)")
        if archivo_origen:
            destino_dir = os.path.join(os.getcwd(), "adjuntos")
            if not os.path.exists(destino_dir):
                os.makedirs(destino_dir)

            nombre_archivo = os.path.basename(archivo_origen)
            ruta_relativa = os.path.join("adjuntos", nombre_archivo)
            ruta_absoluta_destino = os.path.join(os.getcwd(), ruta_relativa)

            try:
                shutil.copy2(archivo_origen, ruta_absoluta_destino)
                self.campo_ruta_pdf.setText(ruta_relativa)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo copiar el archivo: {e}")

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
            elif isinstance(widget, QLineEdit):
                res[nombre] = widget.text()
        return res

    def validar_y_aceptar(self):
        vals = self.get_data_dict()
        primer_campo = list(self.inputs.keys())[0]
        if not vals.get(primer_campo):
            QMessageBox.warning(self, "Error", f"El campo {primer_campo} es obligatorio.")
            return
        self.accept()

    def get_data_list(self):
        return list(self.get_data_dict().values())


class FichaClienteDialog(QDialog):
    def __init__(self, datos_cliente, polizas, columnas_cli, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.datos_actuales = datos_cliente
        self.columnas_cli = columnas_cli

        self.setWindowTitle(f"Ficha de Cliente: {datos_cliente[2]}")
        self.resize(1000, 700)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # SECCIÓN 1: DATOS PERSONALES
        group_datos = QGroupBox("Información Personal")
        self.form_info = QFormLayout()
        self.actualizar_labels()
        group_datos.setLayout(self.form_info)

        scroll = QScrollArea()
        scroll.setWidget(group_datos)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        self.layout.addWidget(scroll)

        # SECCIÓN 2: TABLA DE PÓLIZAS (DINÁMICA TOTAL)
        group_pol = QGroupBox("Pólizas Vinculadas")
        ly_pol = QVBoxLayout()

        # Todas las columnas de pólizas + columna para el botón
        cabeceras = self.parent_app.columnas_pol + ["Acción"]
        self.tabla = QTableWidget(0, len(cabeceras))
        self.tabla.setHorizontalHeaderLabels(cabeceras)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.doubleClicked.connect(self.editar_poliza_desde_ficha)

        ly_pol.addWidget(self.tabla)
        group_pol.setLayout(ly_pol)
        self.layout.addWidget(group_pol)

        # Carga inicial de datos
        self.actualizar_tabla_polizas()

        # SECCIÓN 3: BOTONES DE ACCIÓN
        btns = QHBoxLayout()
        btn_edit_cli = QPushButton("✏️ Editar Cliente")
        btn_edit_cli.clicked.connect(self.abrir_edicion_cliente)
        
        btn_new_pol = QPushButton("📜 Nueva Póliza")
        btn_new_pol.clicked.connect(self.nueva_poliza_desde_ficha)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)

        btns.addWidget(btn_new_pol)
        btns.addWidget(btn_edit_cli)
        btns.addStretch()
        btns.addWidget(btn_close)
        self.layout.addLayout(btns)

    def actualizar_labels(self):
        # Limpiar formulario
        while self.form_info.count():
            child = self.form_info.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        # Rellenar datos
        for i, nombre in enumerate(self.columnas_cli):
            val = str(self.datos_actuales[i]) if self.datos_actuales[i] not in [None, ""] else "-"
            self.form_info.addRow(QLabel(f"<b>{nombre}:</b>"), QLabel(val))

    def actualizar_tabla_polizas(self):
        dni = self.datos_actuales[0]
        polizas = self.parent_app.db.consultar("SELECT * FROM polizas WHERE dni_nif = ?", (dni,))

        self.tabla.setRowCount(0)
        self.tabla.setRowCount(len(polizas))

        for i, fila in enumerate(polizas):
            # Llenar datos de la base de datos
            for j, valor in enumerate(fila):
                self.tabla.setItem(i, j, QTableWidgetItem(str(valor) if valor is not None else ""))

            # Botón PDF (índice 8 según tu main.py)
            idx_boton = self.tabla.columnCount() - 1
            ruta_pdf = fila[8]
            if ruta_pdf:
                btn = QPushButton("📄 Ver")
                btn.clicked.connect(lambda chk, r=ruta_pdf: self.parent_app.abrir_pdf_sistema(r))
                self.tabla.setCellWidget(i, idx_boton, btn)
            else:
                self.tabla.setItem(i, idx_boton, QTableWidgetItem("-"))

        self.tabla.resizeColumnsToContents()

    def nueva_poliza_desde_ficha(self):
        if self.parent_app.nueva_poliza_especifica(self.datos_actuales[0]):
            self.actualizar_tabla_polizas()

    def editar_poliza_desde_ficha(self):
        row = self.tabla.currentRow()
        if row < 0: return
        id_pol = self.tabla.item(row, 0).text()
        if self.parent_app.editar_poliza_especifica(id_pol):
            self.actualizar_tabla_polizas()

    def abrir_edicion_cliente(self):
        diag = EditorDialog("Editar Cliente", self.columnas_cli, self.datos_actuales, None, self)
        if diag.exec():
            nuevos_datos = diag.get_data_list()
            if self.parent_app.guardar_edicion_db("clientes", nuevos_datos, self.datos_actuales[0]):
                self.datos_actuales = nuevos_datos
                self.actualizar_labels()
                self.parent_app.load_data()