from pathlib import Path
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash


BASE_DIR = Path(__file__).resolve().parent
SHARED_DIR = BASE_DIR / "shared"
UPLOADS_DIR = BASE_DIR / "uploads"

# Asegurar que las carpetas existan
SHARED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


app = Flask(__name__)
app.secret_key = "pyshare-secret-key"  # necesario para mensajes flash


def get_relative_path(absolute_path: Path) -> str:
    """Devuelve la ruta relativa a SHARED_DIR para mostrarla en la UI."""
    try:
        rel = absolute_path.relative_to(SHARED_DIR)
    except ValueError:
        return "/"
    return "/" if str(rel) == "." else f"/{rel.as_posix()}"


def list_directory(current_subpath: str | None = None):
    """
    Lista directorios y archivos dentro de SHARED_DIR/current_subpath.
    Devuelve (ruta_actual_absoluta, lista_directorios, lista_archivos).
    """
    base = SHARED_DIR
    if current_subpath:
        # Normalizar para evitar escapes tipo ../
        safe_subpath = Path(current_subpath).as_posix().lstrip("/")
        base = (SHARED_DIR / safe_subpath).resolve()
        if not str(base).startswith(str(SHARED_DIR)):
            base = SHARED_DIR

    dirs = []
    files = []

    if base.exists() and base.is_dir():
        for entry in sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if entry.is_dir():
                dirs.append(entry.name)
            elif entry.is_file():
                files.append(entry.name)

    return base, dirs, files


def build_tree(path: Path, base: Path) -> dict:
    """
    Construye una estructura de árbol a partir de una ruta base.
    Cada nodo tiene: name, rel_path (relativa a base), is_dir, children.
    """
    try:
        rel = path.relative_to(base)
        rel_str = "" if str(rel) == "." else rel.as_posix()
    except ValueError:
        rel_str = ""

    node = {
        "name": path.name if path != base else "shared",
        "rel_path": rel_str,
        "is_dir": path.is_dir(),
        "children": [],
    }

    if path.is_dir():
        for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            node["children"].append(build_tree(child, base))

    return node


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/enviar", methods=["GET", "POST"])
def enviar():
    if request.method == "POST":
        selected_paths = request.form.getlist("selected_paths")
        if not selected_paths:
            flash("No se seleccionó ningún archivo.")
            return redirect(url_for("enviar"))

        for rel in selected_paths:
            safe_rel = Path(rel).as_posix().lstrip("/")
            abs_path = (SHARED_DIR / safe_rel).resolve() if safe_rel else SHARED_DIR
            if not str(abs_path).startswith(str(SHARED_DIR)) or not abs_path.exists():
                continue

            # Si es carpeta, copiar todos los archivos dentro
            if abs_path.is_dir():
                for file_path in abs_path.rglob("*"):
                    if file_path.is_file():
                        target = UPLOADS_DIR / file_path.name
                        try:
                            shutil.copy2(file_path, target)
                        except Exception:
                            continue
            elif abs_path.is_file():
                target = UPLOADS_DIR / abs_path.name
                try:
                    shutil.copy2(abs_path, target)
                except Exception:
                    continue

        flash("Archivos enviados correctamente. Ahora están disponibles en la sección \"Recibir\".")
        return redirect(url_for("recibir"))

    return render_template(
        "enviar.html",
        tree=build_tree(SHARED_DIR, SHARED_DIR),
    )


@app.route("/recibir")
def recibir():
    uploads = []
    for entry in sorted(UPLOADS_DIR.iterdir(), key=lambda p: p.name.lower()) if UPLOADS_DIR.exists() else []:
        if entry.is_file():
            size = entry.stat().st_size
            uploads.append(
                {
                    "name": entry.name,
                    "size": size,
                }
            )

    return render_template("recibir.html", uploads=uploads)


@app.route("/subir", methods=["POST"])
def subir():
    """
    Sube archivos desde el dispositivo del usuario a la carpeta UPLOADS_DIR.
    Soporta selección múltiple y selección de carpetas (en navegadores compatibles).
    """
    if "files" not in request.files:
        flash("No se seleccionó ningún archivo o carpeta para subir.")
        return redirect(url_for("enviar"))

    files = request.files.getlist("files")
    if not files:
        flash("No se seleccionó ningún archivo o carpeta para subir.")
        return redirect(url_for("enviar"))

    # Extensiones a excluir (ejemplo: "py, exe, log")
    raw_exclude = (request.form.get("exclude_ext") or "").strip()
    exclude_exts = {
        ext.lower().lstrip(".")
        for ext in (raw_exclude.split(",") if raw_exclude else [])
        if ext.strip()
    }

    # Tamaño máximo por archivo en MB (opcional)
    max_size_mb_raw = request.form.get("max_size_mb", "").strip()
    max_bytes = None
    if max_size_mb_raw:
        try:
            max_mb = float(max_size_mb_raw)
            if max_mb > 0:
                max_bytes = max_mb * 1024 * 1024
        except ValueError:
            max_bytes = None

    skipped_by_ext = 0
    skipped_by_size = 0

    for f in files:
        if not f.filename:
            continue
        # Sólo guardamos el nombre base, ignorando subcarpetas internas
        filename = Path(f.filename).name

        # Filtro por extensión
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext and ext in exclude_exts:
            skipped_by_ext += 1
            continue

        dest = UPLOADS_DIR / filename
        try:
            f.save(dest)
        except Exception:
            continue

        # Filtro por tamaño, si aplica
        if max_bytes is not None:
            try:
                if dest.stat().st_size > max_bytes:
                    dest.unlink(missing_ok=True)
                    skipped_by_size += 1
                    continue
            except OSError:
                continue

    if skipped_by_ext or skipped_by_size:
        msg_parts = ["Archivos subidos con filtros aplicados."]
        if skipped_by_ext:
            msg_parts.append(f"{skipped_by_ext} archivo(s) ignorado(s) por extensión.")
        if skipped_by_size:
            msg_parts.append(f"{skipped_by_size} archivo(s) ignorado(s) por tamaño.")
        flash(" ".join(msg_parts))
    else:
        flash("Archivos subidos correctamente. Ahora están disponibles en la sección \"Recibir\".")
    return redirect(url_for("recibir"))


@app.route("/descargar/<path:filename>")
def descargar(filename):
    return send_from_directory(UPLOADS_DIR, filename, as_attachment=True)


@app.route("/descargar_todo")
def descargar_todo():
    """
    Genera un archivo ZIP con todos los archivos en UPLOADS_DIR.
    """
    import io
    import zipfile
    from datetime import datetime
    from flask import send_file

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in UPLOADS_DIR.iterdir() if UPLOADS_DIR.exists() else []:
            if entry.is_file():
                zf.write(entry, arcname=entry.name)

    buf.seek(0)
    zip_name = f"pyshare_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    return send_file(
        buf,
        as_attachment=True,
        download_name=zip_name,
        mimetype="application/zip",
    )


def run():
    # Ejecutar en 0.0.0.0 para permitir conexiones en la red local
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    run()

