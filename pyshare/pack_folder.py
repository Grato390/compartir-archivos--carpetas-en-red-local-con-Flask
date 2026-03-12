from __future__ import annotations

"""
Script de utilidad (línea de comandos) para preparar carpetas muy grandes
antes de enviarlas con PyShare.

Uso básico en el PC de ORIGEN:

    python pack_folder.py ruta/a/la/carpeta --salida ./paquetes --max-gb 1

Hace:
- Recorre toda la carpeta origen.
- Genera un archivo manifest.json con la estructura, tamaños y hashes.
- Crea uno o varios ZIP (partes) en la carpeta de salida, sin exceder
  aproximadamente --max-gb por ZIP.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def sha1_of_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def pack_folder(src: Path, out_dir: Path, max_gb: float) -> None:
    src = src.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list(iter_files(src))
    if not files:
        print("No se encontraron archivos en la carpeta origen.")
        return

    print(f"Escaneando carpeta: {src}")
    manifest = {
        "root": src.name,
        "total_files": len(files),
        "files": [],
    }

    for fpath in files:
        rel = fpath.relative_to(src).as_posix()
        size = fpath.stat().st_size
        digest = sha1_of_file(fpath)
        manifest["files"].append(
            {
                "path": rel,
                "size": size,
                "sha1": digest,
            }
        )

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest generado en: {manifest_path}")

    max_bytes = int(max_gb * (1024**3)) if max_gb > 0 else None
    part_idx = 1
    current_zip = None
    current_size = 0

    def new_zip():
        nonlocal part_idx, current_zip, current_size
        if current_zip is not None:
            current_zip.close()
        zip_name = f"{src.name}_part{part_idx:02d}.zip"
        zip_path = out_dir / zip_name
        current_zip = ZipFile(zip_path, "w", ZIP_DEFLATED)
        current_size = 0
        print(f"Creando archivo: {zip_path}")

    new_zip()

    for info in manifest["files"]:
        rel_path = info["path"]
        fpath = src / rel_path
        fsize = info["size"]

        if max_bytes is not None and current_size + fsize > max_bytes and current_size > 0:
            part_idx += 1
            new_zip()

        current_zip.write(fpath, arcname=rel_path)
        current_size += fsize

    if current_zip is not None:
        current_zip.close()

    total_parts = part_idx
    approx_gb = sum(f["size"] for f in manifest["files"]) / (1024**3)
    print(f"Listo. Se crearon {total_parts} parte(s). Tamaño aprox total: {approx_gb:.2f} GB.")


def main():
    parser = argparse.ArgumentParser(description="Empaquetar carpeta grande en partes con manifest para PyShare.")
    parser.add_argument("carpeta", type=str, help="Ruta de la carpeta de origen a empaquetar.")
    parser.add_argument(
        "--salida",
        type=str,
        default="paquetes",
        help="Carpeta donde se guardarán manifest.json y los ZIP. Por defecto: ./paquetes",
    )
    parser.add_argument(
        "--max-gb",
        type=float,
        default=1.0,
        help="Tamaño máximo aproximado por ZIP en GB (ej: 1.0). Usa 0 para un solo ZIP.",
    )

    args = parser.parse_args()
    src = Path(args.carpeta)
    if not src.exists() or not src.is_dir():
        print("La carpeta indicada no existe o no es una carpeta válida.")
        raise SystemExit(1)

    out_dir = Path(args.salida)
    pack_folder(src, out_dir, max_gb=args.max_gb)


if __name__ == "__main__":
    main()

