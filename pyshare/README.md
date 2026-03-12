# PyShare – Compartir archivos en red local

Aplicación web sencilla para **compartir archivos en una red WiFi local** usando Python y Flask.  
Funciona desde el navegador (PC, laptop, celular, tablet) sin necesidad de internet.

---

## 1. Requisitos

- **Python 3.9 o superior** (recomendado 3.10 o 3.11)
- `pip` instalado (viene con Python moderno)
- Estar conectado a la **misma red** (WiFi o cable) que los demás dispositivos.

### Verificar versión de Python

En una terminal / consola:

```bash
python --version
```

o en Windows también puedes probar:

```bash
py --version
```

Si la versión es menor a 3.9, instala una versión más nueva desde la página oficial de Python.

---

## 2. Estructura del proyecto

La carpeta principal del proyecto es `pyshare` y contiene:

- `app.py` → servidor Flask
- `uploads/` → aquí se guardan los archivos enviados y desde aquí se descargan
- `shared/` → (actualmente no se usa en la UI, puedes ignorarla)
- `templates/`
  - `index.html`
  - `enviar.html`
  - `recibir.html`
- `static/`
  - `style.css`

En la carpeta superior (donde está `pyshare`) hay un archivo:

- `requirements.txt` → lista de dependencias de Python.

---

## 3. Instalación en cualquier PC

Estos pasos sirven para **cualquier computadora** donde quieras usar PyShare (tu PC, otro PC en la oficina, etc.).

### 3.1. Copiar el proyecto

Lleva estas carpetas/archivos al nuevo PC (por USB, red, etc.):

- Carpeta `pyshare/` completa
- Archivo `requirements.txt`

Quedará algo así:

```text
carpeta_de_trabajo/
├── requirements.txt
└── pyshare/
    ├── app.py
    ├── uploads/
    ├── shared/
    ├── templates/
    └── static/
```

### 3.2. (Opcional pero recomendado) Crear entorno virtual

En la carpeta donde están `requirements.txt` y `pyshare/`:

```bash
python -m venv venv
```

Luego activas el entorno:

- **Windows (CMD/PowerShell):**

  ```bash
  venv\Scripts\activate
  ```

Si todo va bien, verás algo como `(venv)` al inicio de la línea de comandos.

### 3.3. Instalar dependencias

Con el entorno virtual activado (o con Python del sistema) ejecuta:

```bash
pip install -r requirements.txt
```

Esto instalará al menos:

- `Flask`
- `Werkzeug`

---

## 4. Ejecutar el servidor

1. Ir a la carpeta `pyshare`:

   ```bash
   cd pyshare
   ```

2. Ejecutar la aplicación:

   ```bash
   python app.py
   ```

3. Si todo está correcto, verás algo como:

   ```text
   * Running on http://0.0.0.0:5000
   ```

4. En el **mismo PC** abre el navegador y entra a:

   ```text
   http://127.0.0.1:5000
   ```

---

## 5. Conexión desde otros dispositivos de la red

Para que celulares, tablets u otros PCs entren a PyShare:

1. En el **PC servidor** (donde corre `python app.py`), obtener su IP local.

   - En Windows, en una consola:

     ```bash
     ipconfig
     ```

   - Busca la IP IPv4 de tu adaptador de red (ejemplo: `192.168.1.50`).

2. En el navegador de otro dispositivo (móvil, tablet, laptop):

   - Ir a:

     ```text
     http://192.168.1.50:5000
     ```

   - Cambia `192.168.1.50` por la IP real de tu PC.

> Nota: todos los dispositivos deben estar conectados a la **misma red WiFi o LAN**.

---

## 6. Cómo usar la aplicación

### 6.1. Página principal

Al entrar verás:

- Título: **“Compartir archivos en red”**
- Dos botones grandes:
  - **Enviar archivos**
  - **Recibir archivos**

### 6.2. Enviar archivos

1. Entra a la opción **“Enviar archivos”**.
2. Verás:
   - Botón **“Elegir archivos”**:
     - Puedes seleccionar **una carpeta completa** (en navegadores como Chrome/Edge) o varios archivos.
   - Debajo aparecerá una **vista en forma de árbol**:
     - 📁 carpetas
     - 📄 documentos
     - 🖼 imágenes
     - 🎬 videos
     - Cada elemento tiene su **checkbox**.
3. Marca o desmarca lo que quieras enviar usando los checks.
4. Pulsa **“Subir a recibir”**.
5. La aplicación enviará esos archivos al servidor y te mostrará la página **“Recibir archivos”**, donde aparecen listos para descargar.

### 6.3. Recibir / descargar archivos

1. Entra a la opción **“Recibir archivos”** (desde el menú principal o desde el botón).
2. Verás una tabla con:
   - Nombre del archivo.
   - Tamaño aproximado (B / KB / MB).
   - Botón **“Descargar”** para cada archivo.
3. Opcionalmente puedes usar el botón **“Descargar todos (ZIP)”** para bajar todo en un solo archivo comprimido.

Los archivos que aparecen aquí se almacenan en la carpeta:

```text
pyshare/uploads/
```

Si quieres limpiarlos, puedes borrar manualmente el contenido de esa carpeta.

---

## 7. Notas sobre versiones de Python

- El código está pensado para **Python 3.9+**.
- Si en algún PC tienes una versión diferente y hay errores:
  1. Instala Python 3.10 o 3.11.
  2. Asegúrate de ejecutar el proyecto con esa versión, por ejemplo en Windows:

     ```bash
     py -3.11 app.py
     ```

  3. Vuelve a crear el entorno virtual y reinstalar dependencias si hace falta.

---

## 8. Problemas frecuentes

- **El navegador no abre la página desde otro dispositivo**
  - Verifica que:
    - El servidor siga ejecutándose (la terminal con `python app.py` debe estar abierta).
    - Usas la IP correcta (no `127.0.0.1` en el otro dispositivo, sino la IP local del PC servidor).
    - No haya un firewall bloqueando el puerto `5000`.

- **Error al instalar dependencias**
  - Asegúrate de que `pip` corresponde a la misma versión de Python con la que vas a ejecutar:

    ```bash
    python -m pip install -r requirements.txt
    ```

- **No se suben archivos grandes**
  - Revisa tu conexión de red y asegúrate de que el navegador no se cierre ni recargue.

---

## 9. Resumen rápido para un nuevo PC

1. Instalar **Python 3.9+**.
2. Copiar `pyshare/` y `requirements.txt`.
3. (Opcional) Crear y activar entorno virtual:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

5. Ejecutar servidor:

   ```bash
   cd pyshare
   python app.py
   ```

6. Desde cualquier dispositivo en la misma red abrir en el navegador:

   ```text
   http://IP_DEL_PC:5000
   ```

