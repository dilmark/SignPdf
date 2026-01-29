"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import os
import stat
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime


class FileChooser(tk.Toplevel):
    def __init__(self, parent, start_path=".", extensions=None, on_select=None):
        super().__init__(parent)

        self.title("Wybierz plik")
        self.geometry("900x500")

        self.current_path = Path(start_path).resolve()
        self.on_select = on_select
        self.show_hidden = tk.BooleanVar(value=False)

        self.search_var = tk.StringVar()

        # ☑️ rozszerzenia
        self.extensions = extensions or ["pdf"]
        self.ext_vars = {ext: tk.BooleanVar(value=True) for ext in self.extensions}

        self._build_ui()
        self.refresh()

    # ---------------- UI ----------------
    def _build_ui(self):
        # 🔝 pasek górny
        top = ttk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Button(top, text="⬅️ W górę", command=self.go_up).pack(side="left")
        self.path_var = tk.StringVar()

        self.path_entry = ttk.Entry(top, textvariable=self.path_var)
        self.path_entry.pack(side="left", padx=10, fill="x", expand=True)

        self.path_entry.bind("<Return>", self.on_path_enter)
        self.path_entry.bind("<FocusOut>", self.on_path_enter)

        # 🔍 + ☑️ jedna linia
        filter_line = ttk.Frame(self)
        filter_line.pack(fill="x", padx=5, pady=5)

        ttk.Label(filter_line, text="🔍 Szukaj:").pack(side="left")
        search_entry = ttk.Entry(filter_line, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        ttk.Label(filter_line, text="Typy:").pack(side="left")
        self.ext_entry = ttk.Entry(filter_line, width=25)
        self.ext_entry.pack(side="left", padx=(5, 0))
        self.ext_entry.insert(0, ",".join(self.extensions))
        self.ext_entry.bind("<KeyRelease>", lambda e: self.refresh())

        ttk.Checkbutton(
            filter_line,
            text="Pokaż ukryte",
            variable=self.show_hidden,
            command=self.refresh,
        ).pack(side="left", padx=(10, 0))

        # odświeżanie po zmianie pola
        self.ext_entry.bind("<KeyRelease>", lambda e: self.refresh())
        # 📋 Treeview
        columns = ("name", "size", "date", "perm")
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", selectmode="browse"
        )

        self.tree.heading("name", text="Nazwa")
        self.tree.heading("size", text="Rozmiar")
        self.tree.heading("date", text="Data modyfikacji")
        self.tree.heading("perm", text="Uprawnienia")

        self.tree.column("name", anchor="w", width=350)
        self.tree.column("size", anchor="e", width=90)
        self.tree.column("date", anchor="center", width=160)
        self.tree.column("perm", anchor="center", width=120)

        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_single_click)

        # 🔽 dół
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=5, pady=5)

        ttk.Button(bottom, text="Wybierz", command=self.select_file).pack(side="right")
        ttk.Button(bottom, text="Anuluj", command=self.destroy).pack(
            side="right", padx=5
        )

    # ---------------- Logic ----------------

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.path_var.set(str(self.current_path))

        query = self.search_var.get().lower()
        active_exts = {
            e.strip().lower() for e in self.ext_entry.get().split(",") if e.strip()
        }

        dirs = []
        files = []

        with os.scandir(self.current_path) as it:
            for entry in it:
                if not self.show_hidden.get() and entry.name.startswith("."):
                    continue  # 🧹 ukryte

                if query and query not in entry.name.lower():
                    continue

                info = entry.stat()
                mtime = datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M")
                perms = stat.filemode(info.st_mode)

                if entry.is_dir():
                    dirs.append(("📂 " + entry.name, "", mtime, perms, entry))
                elif entry.is_file():
                    ext = entry.name.split(".")[-1].lower()
                    if ext in active_exts:
                        size = f"{info.st_size / 1024:.1f} KB"
                        files.append((entry.name, size, mtime, perms, entry))

        # 📂 najpierw katalogi
        for row in sorted(dirs, key=lambda x: x[0].lower()):
            self.tree.insert("", "end", values=row[:4])

        for row in sorted(files, key=lambda x: x[0].lower()):
            self.tree.insert("", "end", values=row[:4])

    def go_up(self):
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
            self.refresh()

    def on_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item)["values"][0]

        if name.startswith("📂"):
            dirname = name.replace("📂", "").strip()
            self.current_path = self.current_path / dirname
            self.refresh()
        else:
            self.select_file()

    def on_path_enter(self, event=None):
        raw = Path(self.path_var.get()).expanduser()

        # jeśli katalog istnieje → wejdź
        if raw.exists() and raw.is_dir():
            self.current_path = raw.resolve()
            self.refresh()
            return

        # jeśli plik istnieje → wybierz
        if raw.exists() and raw.is_file():
            if self.on_select:
                self.on_select(raw.resolve())
            self.destroy()
            return

        # ❗ plik NIE istnieje (tryb SAVE)
        if not raw.exists():
            parent = raw.parent
            if parent.exists() and parent.is_dir():
                if self.on_select:
                    self.on_select(raw)
                self.destroy()

    def on_single_click(self, event=None):
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item)["values"][0]

        # 📂 katalog
        if name.startswith("📂"):
            dirname = name.replace("📂", "").strip()
            self.path_var.set(str(self.current_path / dirname))
            return

        # 📄 plik
        full_path = self.current_path / name
        self.path_var.set(str(full_path))

    def select_file(self):
        path = Path(self.path_var.get()).expanduser()

        if not path.exists():
            return

        if self.on_select:
            self.on_select(path)

        self.destroy()
