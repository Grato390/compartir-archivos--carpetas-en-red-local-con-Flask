from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable


BUFFER_SIZE = 1024 * 1024  # 1 MB
PROTOCOL_VERSION = 1


@dataclass
class FileEntry:
    rel_path: str
    size: int


def iter_files(base: Path) -> Generator[FileEntry, None, None]:
    """Devuelve todos los archivos bajo base como FileEntry con ruta relativa."""
    base = base.resolve()
    for path in base.rglob("*"):
        if path.is_file():
            rel = path.relative_to(base).as_posix()
            size = path.stat().st_size
            yield FileEntry(rel_path=rel, size=size)


def send_json_line(sock: socket.socket, payload: dict) -> None:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n"
    sock.sendall(data)


def recv_json_line(sock: socket.socket) -> dict | None:
    """Lee hasta un \\n y parsea JSON. Devuelve None si se cierra la conexión."""
    buf = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            if not buf:
                return None
            raise ConnectionError("Conexión cerrada inesperadamente mientras se leía JSON.")
        if chunk == b"\n":
            break
        buf.extend(chunk)
    return json.loads(buf.decode("utf-8"))


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


