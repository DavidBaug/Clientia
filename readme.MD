# 🛡️ Sistema de Gestión de Seguros v3.0

Aplicación de escritorio desarrollada en **Python 3.12** y **PyQt6** para la gestión integral de clientes y pólizas con base de datos SQLite y persistencia de configuración.

## 📋 Requisitos Previos

* **Python 3.12** instalado (asegúrate de marcar "Add Python to PATH" durante la instalación).
* Sistema Operativo: **Windows 10 o 11**.

---

## 🚀 Configuración del Entorno de Desarrollo

Sigue estos pasos en la terminal (PowerShell o CMD) dentro de la carpeta del proyecto:

### 1. Crear el entorno virtual (venv)
Esto mantendrá las librerías del proyecto aisladas de tu sistema.
```bash
python -m venv venv
```

### 2. Activar el entorno virtual
```bash
# En PowerShell:
.\venv\Scripts\Activate.ps1

# En CMD:
.\venv\Scripts\activate.bat
```

### 3. Instalar dependencias
Instala las librerías necesarias (PyQt6 y PyInstaller) en el archivo requirements:
```bash
pip install -r requirements.txt
```

---

## 🛠️ Uso y Ejecución

### Ejecutar en modo desarrollo
Para lanzar la aplicación directamente con el intérprete de Python:
```bash
python main.py
```

### Crear el ejecutable (.EXE) para Windows
Si deseas generar un archivo independiente para distribuir, usa el siguiente comando:
```bash
pyinstaller --windowed --onefile --name "GestorSeguros" main.py
```
* El archivo final aparecerá en la carpeta **`dist/`**.
* **Nota:** Al mover el `.exe`, recuerda llevar contigo el archivo `seguros.db` si quieres conservar los datos existentes; de lo contrario, el programa creará una base de datos nueva y vacía al iniciar.

---

## 📂 Estructura del Proyecto

* `main.py`: Lógica principal, interfaz de usuario y orquestación.
* `database.py`: Gestión de la base de datos SQLite y esquemas.
* `dialogs.py`: Ventanas de edición, fichas de cliente y validaciones.
* `config_visibilidad.json`: (Autogenerado) Guarda tus preferencias de columnas.
* `seguros.db`: (Autogenerado) Base de datos local.

---

## ✅ Características Implementadas
* **Validación Robusta:** Control de formato en DNI, Email y Código Postal.
* **Buscador Inteligente:** Autocompletado de clientes al crear pólizas.
* **Vista Detallada:** Ficha de cliente con historial de pólizas integrado.
* **Personalización:** Menú para elegir qué columnas deseas ver en la tabla.
