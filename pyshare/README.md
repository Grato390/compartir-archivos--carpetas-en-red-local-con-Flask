# PyShare – Compartir archivos en red local (modo nativo)

Aplicación nativa sencilla para **compartir carpetas y archivos grandes en una red local** usando solo Python.  
No requiere navegador ni Flask; todo se hace con scripts y una pequeña interfaz de escritorio.

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

La carpeta principal del proyecto es `pyshare` y contiene, entre otros:

- `native_common.py` → utilidades compartidas del modo nativo
- `native_server.py` → servidor nativo (recibe carpetas grandes)
- `native_client.py` → cliente nativo (envía carpetas grandes)
- `native_gui.py` → interfaz gráfica simple para usar servidor/cliente
- `pack_folder.py` / `unpack_manifest.py` → empaquetar/verificar carpetas muy grandes

En la carpeta superior (donde está `pyshare`) hay un archivo:

- `requirements.txt` → lista de dependencias de Python.

---

## 3. Instalación en cualquier PC

Estos pasos sirven para **cualquier computadora** donde quieras usar PyShare (tu PC, otro PC en la oficina, etc.).

### 3.1. Copiar el proyecto

Lleva estas carpetas/archivos al nuevo PC (por USB, red, etc.):

- Carpeta `pyshare/` completa
- Archivo `requirements.txt`

Quedará algo así (simplificado):

```text
carpeta_de_trabajo/
├── requirements.txt
└── pyshare/
    ├── native_common.py
    ├── native_server.py
    ├── native_client.py
    ├── native_gui.py
    ├── pack_folder.py
    └── unpack_manifest.py
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

Este proyecto usa solo la **librería estándar de Python**, por lo que no necesitas instalar paquetes extra.

El archivo `requirements.txt` está vacío a propósito para dejar claro que no hay dependencias externas.

---

## 4. Modo avanzado para juegos / carpetas muy grandes

Para carpetas de varios GB (por ejemplo juegos), la subida directa por WiFi puede fallar.  
Para esos casos puedes usar dos scripts de ayuda incluidos en `pyshare/`:

- `pack_folder.py` → se ejecuta en el **PC origen**
- `unpack_manifest.py` → se ejecuta en el **PC destino**

La idea:

1. En el **PC origen**:
   - Crea un paquete de la carpeta grande en partes más pequeñas, con un **manifest** que describe todos los archivos.
2. Usa PyShare para enviar esos ZIP al otro PC.
3. En el **PC destino**:
   - Reconstruyes todo tal cual estaba usando `unpack_manifest.py`, que verifica tamaños y hashes.

### 7.1. Preparar carpeta grande en el PC origen

Desde la carpeta `pyshare`:

```bash
python pack_folder.py "C:\ruta\a\tu_juego" --salida "C:\ruta\paquetes_juego" --max-gb 1
```

- `--salida` → carpeta donde se guardarán:
  - `manifest.json`
  - `juego_part01.zip`, `juego_part02.zip`, ...
- `--max-gb` → tamaño aproximado máximo por ZIP (ejemplo: `1` = 1 GB por parte).  
  Pon `0` si quieres un solo ZIP (no recomendado para 4 GB por WiFi).

Luego, con PyShare:

- En la página **Enviar**, selecciona esos ZIP desde la carpeta de paquetes y súbelos (puedes hacerlo en varias tandas).

### 7.2. Reconstruir en el PC destino

En el PC que recibe, después de haber descargado todos los ZIP y `manifest.json` en una carpeta (por ejemplo `C:\paquetes_juego`), ejecuta:

```bash
python unpack_manifest.py "C:\paquetes_juego" --dest "C:\juego_recibido" --borrar-zip
```

- `--dest` → carpeta donde quieres reconstruir el juego.
- `--borrar-zip` → si lo añades, borra los ZIP cuando termine correctamente.

El script:

- Extrae todo respetando la estructura de carpetas.
- Comprueba:
  - Tamaño de cada archivo.
  - Hash SHA‑1 de cada archivo.
- Muestra un resumen:
  - Cuántos archivos están OK.
  - Si falta alguno o está corrupto.

De esta forma puedes:

- Enviar juegos / carpetas de varios GB **por partes**.
- Verificar que en el PC destino **llegó todo y está igual que en el origen**.

### 4.3. Modo nativo (sin web) para grandes volúmenes

Modo nativo simple, por consola:

- `native_server.py` → se ejecuta en el PC que **recibe**
- `native_client.py` → se ejecuta en el PC que **envía**

Ejemplo de uso:

En el **PC destino** (recibe):

```bash
cd pyshare
python native_server.py --host 0.0.0.0 --port 6000 --dest native_uploads
```

En el **PC origen** (envía, estando en la misma red):

```bash
cd pyshare
python native_client.py 192.168.1.50 --port 6000 --carpeta "C:\mi_juego"
```

- Cambia `192.168.1.50` por la IP real del servidor.
- La carpeta completa `C:\mi_juego` se enviará al servidor, que la reconstruirá dentro de `native_uploads`, respetando subcarpetas.
- Si vuelves a ejecutar el cliente con la misma carpeta, los archivos que **ya existan con el mismo tamaño** se saltan, lo que ayuda a reintentar si hubo cortes.

### 4.4. Interfaz gráfica nativa

Para no usar la consola puedes lanzar una pequeña GUI:

```bash
cd pyshare
python native_gui.py
```

- Pestaña **Servidor**:
  - Configuras host, puerto y carpeta destino.
  - Pulsas **“Iniciar servidor”**.
- Pestaña **Cliente**:
  - Pones IP del servidor, puerto y eliges la carpeta a enviar.
  - Pulsas **“Enviar carpeta”**.

Internamente usa `native_server` y `native_client`, pero con interfaz de ventanas.

---

## 5. Notas sobre versiones de Python

- El código está pensado para **Python 3.9+**.
- Si en algún PC tienes una versión diferente y hay errores:
  1. Instala Python 3.10 o 3.11.
  2. Asegúrate de ejecutar el proyecto con esa versión, por ejemplo en Windows:

     ```bash
     py -3.11 app.py
     ```

  3. Vuelve a crear el entorno virtual y reinstalar dependencias si hace falta.

---

## 6. Problemas frecuentes

- **No conecta el cliente con el servidor**
  - Verifica que ambos PCs estén en la **misma red**.
  - Revisa la IP y puerto del servidor.
  - Asegúrate de que el firewall no bloquee el puerto usado (por defecto 6000).

- **Transferencia muy lenta**
  - Usa, si es posible, conexión por **cable de red**.
  - Evita que los equipos se duerman durante la transferencia.

- **Faltan archivos al reconstruir con unpack_manifest**
  - Asegúrate de haber copiado **todas las partes ZIP** y el `manifest.json`.
  - Vuelve a ejecutar `pack_folder.py` en origen si el manifest indica errores.

---

## 7. Resumen rápido para un nuevo PC

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

5. Ejecutar en ese PC el modo que quieras:
   - Modo nativo consola → `native_server.py` / `native_client.py`
   - Modo nativo con GUI → `native_gui.py`

