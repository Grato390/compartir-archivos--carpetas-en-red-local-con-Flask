from __future__ import annotations

"""
Script de utilidad (línea de comandos) para reconstruir una carpeta grande
a partir de los ZIP y el manifest generados por pack_folder.py.

Uso básico en el PC de DESTINO:

    python unpack_manifest.py ruta/a/paquetes --dest ./juego_recibido --borrar-zip
"""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def sha1_of_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def unpack(paquetes_dir: Path, dest_dir: Path, borrar_zip: bool) -> None:
    paquetes_dir = paquetes_dir.resolve()
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = paquetes_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"No se encontró manifest.json en {paquetes_dir}")
        raise SystemExit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_files = {f["path"]: f for f in manifest.get("files", [])}

    zip_files = sorted(paquetes_dir.glob("*.zip"))
    if not zip_files:
        print("No se encontraron archivos ZIP en la carpeta de paquetes.")
        raise SystemExit(1)

    print(f"Encontrados {len(zip_files)} archivo(s) ZIP. Extrayendo en {dest_dir} ...")

    for zpath in zip_files:
        print(f"Extrayendo {zpath.name} ...")
        with ZipFile(zpath, "r") as zf:
            zf.extractall(dest_dir)

    print("Extracción completada. Verificando tamaños y hashes (puede tardar)...")

    ok = 0
    bad = 0
    missing = 0

    for rel, info in expected_files.items():
        out_path = dest_dir / rel
        if not out_path.exists():
            print(f"[FALTA] {rel}")
            missing += 1
            continue

        size = out_path.stat().st_size
        if size != info["size"]:
            print(f"[TAMAÑO] {rel} esperado={info['size']} actual={size}")
            bad += 1
            continue

        digest = sha1_of_file(out_path)
        if digest != info["sha1"]:
            print(f"[HASH] {rel} esperado={info['sha1']} actual={digest}")
            bad += 1
            continue

        ok += 1

    total = len(expected_files)
    print(f"Archivos OK: {ok}/{total}")
    if missing or bad:
        print(f"Archivos faltantes: {missing}, archivos dañados: {bad}")
    else:
        print("Todos los archivos coinciden con el manifest.")

    if borrar_zip:
        for zpath in zip_files:
            try:
                zpath.unlink()
            except OSError:
                continue
        print("ZIP eliminados después de reconstruir.")


def main():
    parser = argparse.ArgumentParser(description="Reconstruir carpeta grande desde paquetes + manifest de PyShare.")
    parser.add_argument("paquetes", type=str, help="Carpeta donde están manifest.json y los ZIP.")
    parser.add_argument(
        "--dest",
        type=str,
        default="recibido",
        help="Carpeta destino donde se reconstruirá la estructura. Por defecto: ./recibido",
    )
    parser.add_argument(
        "--borrar-zip",
        action="store_true",
        help="Si se indica, elimina los ZIP después de reconstruir.",
    )

    args = parser.parse_args()
    paquetes_dir = Path(args.paquetes)
    if not paquetes_dir.exists() or not paquetes_dir.is_dir():
        print("La carpeta de paquetes no existe o no es válida.")
        raise SystemExit(1)

    dest_dir = Path(args.dest)
    unpack(paquetes_dir, dest_dir, borrar_zip=args.borrar_zip)


if __name__ == "__main__":
    main()

