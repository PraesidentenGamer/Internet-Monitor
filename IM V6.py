import tkinter as tk
from tkinter import ttk, font, messagebox
import psutil
import threading
import time
import os
import sys
import winreg

class NetSpeedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Monitor Einstellungen")

        # Standardwerte
        self.update_interval = 1.0
        self.opacity = 0.9
        self.font_size = 10
        self.font_color = "white"
        self.font_family = "Segoe UI"
        self.bg_color = "black"
        self.autostart_enabled = False
        self.mini_window_enabled = True  # Neu: Vorschau anzeigen ja/nein

        self.create_settings_ui()
        self.create_preview_frame()

        # Mini-Vorschau-Label in der App
        self.mini_window = MiniWindow(self)
        self.mini_window.update_settings()

        # Nur bei aktiver Mini-Vorschau zeigen
        self.mini_window_frame = None
        if self.mini_window_enabled:
            self.create_mini_window_frame()

    def create_settings_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="x")

        ttk.Label(frame, text="Update Intervall (Sekunden):").grid(row=0, column=0, sticky="w")
        self.interval_var = tk.DoubleVar(value=self.update_interval)
        ttk.Entry(frame, textvariable=self.interval_var, width=10).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Transparenz (0.1 - 1.0):").grid(row=1, column=0, sticky="w")
        self.opacity_var = tk.DoubleVar(value=self.opacity)
        ttk.Entry(frame, textvariable=self.opacity_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Schriftgröße:").grid(row=2, column=0, sticky="w")
        self.font_size_var = tk.IntVar(value=self.font_size)
        ttk.Spinbox(frame, from_=6, to=30, textvariable=self.font_size_var, width=5).grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="Schriftfarbe:").grid(row=3, column=0, sticky="w")
        self.font_color_var = tk.StringVar(value=self.font_color)
        ttk.Entry(frame, textvariable=self.font_color_var, width=10).grid(row=3, column=1, sticky="w")

        ttk.Label(frame, text="Hintergrundfarbe:").grid(row=4, column=0, sticky="w")
        self.bg_color_var = tk.StringVar(value=self.bg_color)
        ttk.Entry(frame, textvariable=self.bg_color_var, width=10).grid(row=4, column=1, sticky="w")

        ttk.Label(frame, text="Schriftart:").grid(row=5, column=0, sticky="w")
        self.font_family_var = tk.StringVar(value=self.font_family)
        font_families = sorted(font.families())
        ttk.Combobox(frame, textvariable=self.font_family_var, values=font_families, width=20).grid(row=5, column=1, sticky="w")

        self.autostart_var = tk.BooleanVar(value=self.autostart_enabled)
        ttk.Checkbutton(frame, text="Autostart aktivieren", variable=self.autostart_var).grid(row=6, column=0, columnspan=2, sticky="w")

        self.mini_window_var = tk.BooleanVar(value=self.mini_window_enabled)
        ttk.Checkbutton(frame, text="Mini-Vorschau anzeigen", variable=self.mini_window_var).grid(row=7, column=0, columnspan=2, sticky="w")

        ttk.Button(frame, text="Einstellungen übernehmen", command=self.apply_settings).grid(row=8, column=0, columnspan=2, pady=10)

    def create_preview_frame(self):
        ttk.Label(self.root, text="Live-Vorschau:").pack(anchor="w", padx=10)
        preview = ttk.Frame(self.root, relief="sunken", padding=5)
        preview.pack(fill="both", expand=True, padx=10, pady=5)
        self.preview_container = preview

    def create_mini_window_frame(self):
        self.mini_window_frame = tk.Toplevel(self.root)
        self.mini_window_frame.title("Speed Monitor")
        self.mini_window_frame.geometry("180x60")
        self.mini_window_frame.attributes("-topmost", True)
        self.mini_window_frame.protocol("WM_DELETE_WINDOW", self.on_mini_window_close)

        self.label = tk.Label(self.mini_window_frame, text="U: ...\nD: ...", justify="left")
        self.label.pack(fill="both", expand=True)

        self.update_mini_window()
        threading.Thread(target=self.mini_speed_loop, daemon=True).start()

    def apply_settings(self):
        try:
            self.update_interval = float(self.interval_var.get())
            self.opacity = float(self.opacity_var.get())
            self.font_size = self.font_size_var.get()
            self.font_color = self.font_color_var.get()
            self.bg_color = self.bg_color_var.get()
            self.font_family = self.font_family_var.get()
            self.autostart_enabled = self.autostart_var.get()
            self.mini_window_enabled = self.mini_window_var.get()
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            return

        self.mini_window.update_settings()
        self.update_mini_window()
        self.configure_autostart()

        # Mini-Fenster je nach Checkbox zeigen oder verstecken
        if self.mini_window_enabled:
            if self.mini_window_frame is None or not self.mini_window_frame.winfo_exists():
                self.create_mini_window_frame()
            else:
                self.mini_window_frame.deiconify()
        else:
            if self.mini_window_frame:
                self.mini_window_frame.withdraw()

    def update_mini_window(self):
        if self.mini_window_frame:
            self.mini_window_frame.attributes("-alpha", self.opacity)
            self.label.config(
                fg=self.font_color,
                bg=self.bg_color,
                font=(self.font_family, self.font_size)
            )

    def mini_speed_loop(self):
        while True:
            up, down = self.get_net_speed()
            text = f"U: {up:.2f} Mbit/s\nD: {down:.2f} Mbit/s"
            if self.mini_window_frame and self.mini_window_frame.winfo_exists():
                self.label.after(0, self.label.config, {"text": text})
            time.sleep(self.update_interval)

    def get_net_speed(self):
        old_sent = psutil.net_io_counters().bytes_sent
        old_recv = psutil.net_io_counters().bytes_recv
        time.sleep(self.update_interval)
        new_sent = psutil.net_io_counters().bytes_sent
        new_recv = psutil.net_io_counters().bytes_recv
        upload_mbit = (new_sent - old_sent) * 8 / 1024 / 1024
        download_mbit = (new_recv - old_recv) * 8 / 1024 / 1024
        return upload_mbit, download_mbit

    def configure_autostart(self):
        app_name = "NetSpeedMonitor"
        exe_path = os.path.realpath(sys.argv[0])
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS) as key:
                if self.autostart_enabled:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass
        except Exception as e:
            messagebox.showerror("Autostart Fehler", str(e))

    def on_mini_window_close(self):
        # Nicht schließen, sondern verstecken
        if self.mini_window_frame:
            self.mini_window_frame.withdraw()


class MiniWindow:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Label(app.preview_container, text="U: ...\nD: ...", anchor="w", justify="left")
        self.frame.pack(fill="both", expand=True)
        threading.Thread(target=self.update_speed_loop, daemon=True).start()

    def update_settings(self):
        font_style = (self.app.font_family, self.app.font_size)
        self.frame.config(
            font=font_style,
            fg=self.app.font_color,
            bg=self.app.bg_color
        )

    def get_net_speed(self):
        old_sent = psutil.net_io_counters().bytes_sent
        old_recv = psutil.net_io_counters().bytes_recv
        time.sleep(self.app.update_interval)
        new_sent = psutil.net_io_counters().bytes_sent
        new_recv = psutil.net_io_counters().bytes_recv
        upload_mbit = (new_sent - old_sent) * 8 / 1024 / 1024
        download_mbit = (new_recv - old_recv) * 8 / 1024 / 1024
        return upload_mbit, download_mbit

    def update_speed_loop(self):
        while True:
            up, down = self.get_net_speed()
            text = f"U: {up:.2f} Mbit/s\nD: {down:.2f} Mbit/s"
            self.frame.after(0, self.frame.config, {"text": text})


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    app = NetSpeedApp(root)
    root.mainloop()
