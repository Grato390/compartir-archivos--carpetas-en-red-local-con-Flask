from __future__ import annotations

"""
Servidor nativo sencillo para transferir carpetas grandes por la red local.

Uso:
    python native_server.py --host 0.0.0.0 --port 6000 --dest ./native_uploads

Después, en el otro PC, se usa native_client.py para enviar una carpeta a este servidor.
"""

import argparse
import socket
from pathlib import Path

from native_common import BUFFER_SIZE, recv_json_line, send_json_line, human_size


def handle_client(conn: socket.socket, dest_root: Path) -> None:
    with conn:
        hello = recv_json_line(conn)
        if not hello or hello.get("type") != "hello":
            return
        print(f"Cliente conectado: {hello.get('client_name','desconocido')} (proto v{hello.get('version')})")

        send_json_line(conn, {"type": "hello_ack"})

        while True:
            header = recv_json_line(conn)
            if header is None:
                break

            if header.get("type") == "end":
                print("Cliente indicó fin de transferencia.")
                break

            if header.get("type") != "file":
                continue

            rel_path = header["rel_path"]
            size = int(header["size"])

            dest = dest_root / rel_path
            dest = dest.resolve()
            if not str(dest).startswith(str(dest_root)):
                print(f"Ignorando ruta insegura: {rel_path}")
                # Consumir bytes del archivo sin guardar
                remaining = size
                while remaining > 0:
                    chunk = conn.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        raise ConnectionError("Conexión cerrada durante lectura de archivo.")
                    remaining -= len(chunk)
                continue

            if dest.exists() and dest.stat().st_size == size:
                print(f"[SKIP] {rel_path} (ya existe con mismo tamaño)")
                # Consumir bytes sin reescribir
                remaining = size
                while remaining > 0:
                    chunk = conn.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        raise ConnectionError("Conexión cerrada durante lectura de archivo.")
                    remaining -= len(chunk)
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            print(f"[RECIBIENDO] {rel_path} ({human_size(size)})")
            remaining = size
            with dest.open("wb") as f:
                while remaining > 0:
                    chunk = conn.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        raise ConnectionError("Conexión cerrada durante lectura de archivo.")
                    f.write(chunk)
                    remaining -= len(chunk)

            print(f"[OK] {rel_path}")


def run_server(host: str, port: int, dest: Path) -> None:
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Destino de archivos: {dest}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        print(f"Servidor escuchando en {host}:{port}")

        while True:
            conn, addr = s.accept()
            print(f"Conexión entrante de {addr[0]}:{addr[1]}")
            try:
                handle_client(conn, dest)
            except Exception as e:
                print(f"Error con cliente: {e}")
            finally:
                print("Conexión cerrada.\n")


def main():
    parser = argparse.ArgumentParser(description="Servidor nativo para transferir carpetas grandes.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host/IP para escuchar (por defecto 0.0.0.0).")
    parser.add_argument("--port", type=int, default=6000, help="Puerto TCP para escuchar (por defecto 6000).")
    parser.add_argument(
        "--dest",
        type=str,
        default="native_uploads",
        help="Carpeta destino donde se guardarán los archivos recibidos.",
    )

    args = parser.parse_args()
    run_server(args.host, args.port, Path(args.dest))


if __name__ == "__main__":
    main()

