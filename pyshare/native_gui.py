from __future__ import annotations

"""
Interfaz gráfica sencilla para el modo nativo de PyShare.

Permite:
- Iniciar un servidor nativo (recibe carpetas grandes).
- Enviar una carpeta a un servidor nativo.

Uso:
    python native_gui.py
"""

import threading
import tkinter as tk
import socket
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from native_client import send_folder
from native_server import run_server
from native_common import human_size as human_readable


class NativeGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PyShare Native – Compartir en red local")
        self.geometry("560x420")
        self.resizable(False, False)

        self._server_thread: threading.Thread | None = None
        self._server_stop_event: threading.Event | None = None

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.server_frame = ttk.Frame(self.notebook)
        self.client_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.server_frame, text="🖥️ Recibir (Servidor)")
        self.notebook.add(self.client_frame, text="📤 Enviar (Cliente)")

        self._build_server_tab()
        self._build_client_tab()

        # Texto de ayuda general bajo las pestañas
        self.help_var = tk.StringVar(
            value="Paso 1: En el PC que recibirá archivos, abre la pestaña 'Recibir (Servidor)' y pulsa 'Iniciar servidor'."
        )
        ttk.Label(self, textvariable=self.help_var, foreground="#9ca3af", wraplength=540, justify="left").pack(
            fill="x", padx=10, pady=(0, 6)
        )

        # Cambiar mensaje de ayuda al cambiar de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    # ---------- Servidor ----------
    def _build_server_tab(self) -> None:
        frame = self.server_frame

        ttk.Label(frame, text="IP local (host):").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.server_host_var = tk.StringVar(value="0.0.0.0")
        ttk.Entry(frame, textvariable=self.server_host_var, width=25).grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(frame, text="Puerto:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.server_port_var = tk.StringVar(value="6000")
        ttk.Entry(frame, textvariable=self.server_port_var, width=10).grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(frame, text="Carpeta donde se guardará lo recibido:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.server_dest_var = tk.StringVar(value=str(Path("native_uploads").resolve()))
        dest_entry = ttk.Entry(frame, textvariable=self.server_dest_var, width=40)
        dest_entry.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        def browse_dest() -> None:
            path = filedialog.askdirectory(title="Elegir carpeta destino")
            if path:
                self.server_dest_var.set(path)

        ttk.Button(frame, text="Buscar...", command=browse_dest).grid(row=2, column=2, sticky="w", padx=4, pady=4)

        self.server_status_var = tk.StringVar(
            value="Servidor detenido. Pulsa 'Iniciar servidor' para empezar a escuchar conexiones."
        )
        ttk.Label(frame, textvariable=self.server_status_var, foreground="#9ca3af").grid(
            row=3, column=0, columnspan=3, sticky="w", padx=8, pady=6
        )

        ttk.Label(
            frame,
            text="Guía rápida:\n1) Ejecuta este programa en el PC que recibirá archivos.\n"
            "2) Inicia el servidor.\n3) En el otro PC usa la pestaña 'Enviar (Cliente)' para conectarse a esta IP y puerto.\n"
            "4) Para saber tu IP local abre CMD y ejecuta: ipconfig",
            foreground="#9ca3af",
            wraplength=460,
            justify="left",
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        self.server_button = ttk.Button(frame, text="Iniciar servidor", command=self.start_server_thread)
        self.server_button.grid(row=5, column=0, columnspan=3, pady=10)

        ttk.Label(frame, text="Logs del servidor:").grid(row=6, column=0, columnspan=3, sticky="w", padx=8, pady=(4, 2))
        self.server_log = ScrolledText(frame, height=6, width=64, state="disabled")
        self.server_log.grid(row=7, column=0, columnspan=3, padx=8, pady=(0, 6), sticky="we")

    def start_server_thread(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            # Toggle: detener servidor
            if self._server_stop_event:
                self._server_stop_event.set()
            self.server_status_var.set("Deteniendo servidor...")
            self.server_button.configure(state="disabled")
            return

        host = self.server_host_var.get().strip() or "0.0.0.0"
        try:
            port = int(self.server_port_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número entero.")
            return

        dest = Path(self.server_dest_var.get().strip() or "native_uploads")
        self._server_stop_event = threading.Event()

        def target():
            self.server_status_var.set(f"Servidor escuchando en {host}:{port}. Destino: {dest}")
            try:
                run_server(host, port, dest, stop_event=self._server_stop_event, log_cb=self._append_server_log)
            except Exception as e:
                self.server_status_var.set(f"Error en servidor: {e}")
                self._append_server_log(f"ERROR: {e}")
            finally:
                self.server_status_var.set("Servidor detenido.")
                self.after(0, lambda: self.server_button.configure(text="Iniciar servidor", state="normal"))

        self._server_thread = threading.Thread(target=target, daemon=True)
        self._server_thread.start()
        # Actualizar botón a estado "en marcha"
        self.server_button.configure(text="Detener servidor", state="normal")
        self._append_server_log(f"Servidor iniciado en {host}:{port}")

    # ---------- Cliente ----------
    def _build_client_tab(self) -> None:
        frame = self.client_frame

        ttk.Label(frame, text="IP del PC que recibe (servidor):").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.client_ip_var = tk.StringVar(value="192.168.1.50")
        ttk.Entry(frame, textvariable=self.client_ip_var, width=25).grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(frame, text="Puerto:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.client_port_var = tk.StringVar(value="6000")
        ttk.Entry(frame, textvariable=self.client_port_var, width=10).grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(frame, text="Carpeta que quieres compartir:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.client_folder_var = tk.StringVar()
        folder_entry = ttk.Entry(frame, textvariable=self.client_folder_var, width=40)
        folder_entry.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        def browse_folder() -> None:
            path = filedialog.askdirectory(title="Elegir carpeta a enviar")
            if path:
                self.client_folder_var.set(path)

        ttk.Button(frame, text="Buscar...", command=browse_folder).grid(row=2, column=2, sticky="w", padx=4, pady=4)

        ttk.Button(frame, text="Probar conexión", command=self.test_client_connection).grid(
            row=0, column=2, sticky="w", padx=4, pady=4
        )

        ttk.Label(frame, text="Nombre del cliente (opcional):").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.client_name_var = tk.StringVar(value="PyShareNativeClient")
        ttk.Entry(frame, textvariable=self.client_name_var, width=25).grid(
            row=3, column=1, sticky="w", padx=8, pady=4
        )

        self.client_status_var = tk.StringVar(
            value="Paso 2: Asegúrate de que el servidor está iniciado en el otro PC. Luego elige aquí la carpeta y pulsa 'Enviar carpeta'."
        )
        ttk.Label(frame, textvariable=self.client_status_var, foreground="#9ca3af", wraplength=460, justify="left").grid(
            row=4, column=0, columnspan=3, sticky="w", padx=8, pady=8
        )

        # Indicadores de progreso
        self.client_progress_var = tk.StringVar(value="Progreso: 0% (0 / 0)")
        self.client_speed_var = tk.StringVar(value="Velocidad: 0 MB/s")
        self.client_time_var = tk.StringVar(value="Tiempo estimado: 0 s")

        ttk.Label(frame, textvariable=self.client_progress_var).grid(
            row=5, column=0, columnspan=3, sticky="w", padx=8, pady=2
        )
        ttk.Label(frame, textvariable=self.client_speed_var, foreground="#9ca3af").grid(
            row=6, column=0, columnspan=3, sticky="w", padx=8, pady=2
        )
        ttk.Label(frame, textvariable=self.client_time_var, foreground="#9ca3af").grid(
            row=7, column=0, columnspan=3, sticky="w", padx=8, pady=2
        )

        self.client_button = ttk.Button(frame, text="Enviar carpeta", command=self.start_client_thread)
        self.client_button.grid(row=8, column=0, columnspan=3, pady=10)

        ttk.Label(frame, text="Logs del cliente:").grid(row=9, column=0, columnspan=3, sticky="w", padx=8, pady=(4, 2))
        self.client_log = ScrolledText(frame, height=6, width=64, state="disabled")
        self.client_log.grid(row=10, column=0, columnspan=3, padx=8, pady=(0, 6), sticky="we")

    def start_client_thread(self) -> None:
        server_ip = self.client_ip_var.get().strip()
        if not server_ip:
            messagebox.showerror("Error", "Debes indicar la IP del servidor.")
            return

        try:
            port = int(self.client_port_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número entero.")
            return

        folder = Path(self.client_folder_var.get().strip())
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Error", "La carpeta a enviar no existe o no es válida.")
            return

        client_name = self.client_name_var.get().strip() or "PyShareNativeClient"

        def target():
            try:
                self.client_status_var.set("Conectando con el servidor...")
                self.client_button.configure(state="disabled", text="Enviando...")
                self._append_client_log(f"Intentando conectar con {server_ip}:{port}")

                def progress_cb(event: dict) -> None:
                    # Se ejecuta en el hilo de envío; redirigimos la actualización al hilo principal
                    self.after(0, self._update_client_progress, event)

                send_folder(server_ip, port, folder, client_name, progress_cb=progress_cb)
                self.client_status_var.set("Transferencia finalizada. Revisa la carpeta destino en el servidor.")
                self._append_client_log("Transferencia finalizada correctamente.")
            except Exception as e:
                self.client_status_var.set(f"Error durante el envío: {e}")
                self._append_client_log(f"ERROR: {e}")
            finally:
                self.client_button.configure(state="normal", text="Enviar carpeta")

        threading.Thread(target=target, daemon=True).start()

    def _update_client_progress(self, event: dict) -> None:
        etype = event.get("type")
        if etype == "connected":
            self.client_status_var.set(
                f"Conectado a {event.get('server_ip')}:{event.get('port')}. Iniciando envío de carpeta..."
            )
            self._append_client_log(self.client_status_var.get())
        elif etype == "start":
            total = event.get("total_bytes", 0)
            self.client_progress_var.set(f"Progreso: 0% (0 / {human_readable(total)})")
            self.client_speed_var.set("Velocidad: 0 MB/s")
            self.client_time_var.set("Tiempo estimado: calculando...")
            self._append_client_log(f"Inicio: {event.get('total_files', 0)} archivo(s), {human_readable(total)}")
        elif etype == "file_start":
            idx = event.get("index", 0)
            total_files = event.get("total_files", 0)
            rel_path = event.get("rel_path", "")
            self.client_status_var.set(f"Enviando archivo {idx}/{total_files}: {rel_path}")
            self._append_client_log(self.client_status_var.get())
        elif etype == "progress":
            sent = event.get("sent_bytes", 0)
            total = max(event.get("total_bytes", 0), 1)
            elapsed = max(event.get("elapsed", 0.001), 0.001)
            speed = event.get("speed", 0.0)
            percent = (sent / total) * 100
            self.client_progress_var.set(
                f"Progreso: {percent:.1f}% ({human_readable(sent)} / {human_readable(total)})"
            )
            mb_s = speed / (1024 * 1024)
            self.client_speed_var.set(f"Velocidad: {mb_s:.2f} MB/s")
            eta = max(int((total - sent) / speed), 0) if speed > 0 else 0
            self.client_time_var.set(f"Tiempo estimado restante: {eta} s")
        elif etype == "done":
            sent = event.get("sent_bytes", 0)
            total = max(event.get("total_bytes", sent), 1)
            elapsed = max(event.get("elapsed", 0.001), 0.001)
            percent = (sent / total) * 100
            mb_s = (sent / elapsed) / (1024 * 1024)
            self.client_progress_var.set(
                f"Progreso: {percent:.1f}% ({human_readable(sent)} / {human_readable(total)})"
            )
            self.client_speed_var.set(f"Velocidad media: {mb_s:.2f} MB/s")
            self.client_time_var.set(f"Tiempo total: {elapsed:.1f} s")
            self._append_client_log("Resumen final: transferencia completa.")
        elif etype == "error":
            msg = event.get("message", "Error durante el envío.")
            self.client_status_var.set(msg)
            self._append_client_log(f"ERROR: {msg}")

    def _on_tab_change(self, event) -> None:
        current = self.notebook.index(self.notebook.select())
        if current == 0:
            self.help_var.set(
                "Servidor: este PC recibirá archivos. Deja este programa abierto mientras el otro PC envía la carpeta."
            )
        else:
            self.help_var.set(
                "Cliente: este PC enviará la carpeta. Asegúrate de que el servidor está iniciado en el otro PC."
            )

    def test_client_connection(self) -> None:
        server_ip = self.client_ip_var.get().strip()
        try:
            port = int(self.client_port_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número entero.")
            return

        if not server_ip:
            messagebox.showerror("Error", "Debes indicar la IP del servidor.")
            return

        try:
            with socket.create_connection((server_ip, port), timeout=3):
                self.client_status_var.set(f"Conexión OK con {server_ip}:{port}")
                self._append_client_log(self.client_status_var.get())
        except OSError as e:
            self.client_status_var.set(f"No conecta con {server_ip}:{port}. Revisa servidor/IP/red.")
            self._append_client_log(f"ERROR conexión: {e}")

    def _append_server_log(self, msg: str) -> None:
        def write():
            self.server_log.configure(state="normal")
            self.server_log.insert("end", msg + "\n")
            self.server_log.see("end")
            self.server_log.configure(state="disabled")

        self.after(0, write)

    def _append_client_log(self, msg: str) -> None:
        self.client_log.configure(state="normal")
        self.client_log.insert("end", msg + "\n")
        self.client_log.see("end")
        self.client_log.configure(state="disabled")


def main():
    app = NativeGui()
    app.mainloop()


if __name__ == "__main__":
    main()

