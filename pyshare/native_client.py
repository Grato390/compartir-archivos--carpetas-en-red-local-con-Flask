from __future__ import annotations

"""
Cliente nativo sencillo para enviar carpetas grandes al native_server.

Uso:
    python native_client.py 192.168.1.50 --port 6000 --carpeta "C:\\mi_juego"
"""

import argparse
import socket
from pathlib import Path

from native_common import BUFFER_SIZE, PROTOCOL_VERSION, FileEntry, iter_files, send_json_line, recv_json_line, human_size


def send_folder(server_ip: str, port: int, folder: Path, client_name: str) -> None:
    folder = folder.resolve()
    if not folder.exists() or not folder.is_dir():
        print("La carpeta a enviar no existe o no es válida.")
        return

    entries = list(iter_files(folder))
    total_bytes = sum(e.size for e in entries)
    print(f"Se enviarán {len(entries)} archivos ({human_size(total_bytes)}) desde {folder}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_ip, port))
        print(f"Conectado a {server_ip}:{port}")

        send_json_line(
            sock,
            {
                "type": "hello",
                "version": PROTOCOL_VERSION,
                "client_name": client_name,
                "base_name": folder.name,
            },
        )
        ack = recv_json_line(sock)
        if not ack or ack.get("type") != "hello_ack":
            print("El servidor no respondió correctamente al saludo.")
            return

        sent_bytes_total = 0

        for entry in entries:
            rel_path = entry.rel_path
            size = entry.size

            send_json_line(
                sock,
                {
                    "type": "file",
                    "rel_path": rel_path,
                    "size": size,
                },
            )

            print(f"[ENVIANDO] {rel_path} ({human_size(size)})")
            path = folder / rel_path
            remaining = size
            with path.open("rb") as f:
                while remaining > 0:
                    chunk = f.read(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    remaining -= len(chunk)
                    sent_bytes_total += len(chunk)

            print(f"[OK] {rel_path}")

        # Indicar fin
        send_json_line(sock, {"type": "end"})
        print(f"Transferencia completada. Total enviado: {human_size(sent_bytes_total)}")


def main():
    parser = argparse.ArgumentParser(description="Cliente nativo para enviar carpetas grandes por la red local.")
    parser.add_argument("server_ip", type=str, help="IP del servidor (PC que ejecuta native_server.py).")
    parser.add_argument("--port", type=int, default=6000, help="Puerto TCP del servidor (por defecto 6000).")
    parser.add_argument(
        "--carpeta",
        type=str,
        required=True,
        help="Carpeta local que se enviará al servidor.",
    )
    parser.add_argument(
        "--nombre",
        type=str,
        default="PyShareNativeClient",
        help="Nombre identificador del cliente (solo informativo).",
    )

    args = parser.parse_args()
    send_folder(args.server_ip, args.port, Path(args.carpeta), client_name=args.nombre)


if __name__ == "__main__":
    main()

