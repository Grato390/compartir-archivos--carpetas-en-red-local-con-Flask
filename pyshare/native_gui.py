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
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from native_client import send_folder
from native_server import run_server


class NativeGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PyShare Native – Compartir en red local")
        self.geometry("560x420")
        self.resizable(False, False)

        self._server_thread: threading.Thread | None = None

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
            "2) Inicia el servidor.\n3) En el otro PC usa la pestaña 'Enviar (Cliente)' para conectarse a esta IP y puerto.",
            foreground="#9ca3af",
            wraplength=460,
            justify="left",
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        ttk.Button(frame, text="Iniciar servidor", command=self.start_server_thread).grid(
            row=5, column=0, columnspan=3, pady=10
        )

    def start_server_thread(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            messagebox.showinfo("Servidor en marcha", "El servidor ya está en ejecución.")
            return

        host = self.server_host_var.get().strip() or "0.0.0.0"
        try:
            port = int(self.server_port_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número entero.")
            return

        dest = Path(self.server_dest_var.get().strip() or "native_uploads")

        def target():
            self.server_status_var.set(f"Servidor escuchando en {host}:{port}. Destino: {dest}")
            try:
                run_server(host, port, dest)
            except Exception as e:
                self.server_status_var.set(f"Error en servidor: {e}")

        self._server_thread = threading.Thread(target=target, daemon=True)
        self._server_thread.start()

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

        self.client_button = ttk.Button(frame, text="Enviar carpeta", command=self.start_client_thread)
        self.client_button.grid(row=5, column=0, columnspan=3, pady=10)

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
                self.client_status_var.set("Enviando carpeta, revisa la consola para más detalles...")
                self.client_button.configure(state="disabled")
                send_folder(server_ip, port, folder, client_name)
                self.client_status_var.set("Transferencia finalizada. Revisa la carpeta destino en el servidor.")
            except Exception as e:
                self.client_status_var.set(f"Error durante el envío: {e}")
            finally:
                self.client_button.configure(state="normal")

        threading.Thread(target=target, daemon=True).start()

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


def main():
    app = NativeGui()
    app.mainloop()


if __name__ == "__main__":
    main()

