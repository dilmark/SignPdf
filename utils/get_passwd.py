"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import os
import sys
import tkinter as tk
import logging

from tkinter import ttk
from cryptography.hazmat.primitives.serialization import pkcs12
from pathlib import Path


def ask_cert_password(parent, attemps, max_attempts) -> bytes:
    """
    Pyta użytkownika o hasło do pliku PKCS#12 i zwraca je jako bytes.
    Jeśli użytkownik nie poda żadnego hasła, zwróci pusty bytes (b"").
    """
    dialog = PasswordDialog(parent, title=f"Próba {attemps + 1}/{max_attempts}")
    return dialog.result  # tu masz już bity hasła


def get_password(parent, cert_path: str, max_attempts: int = 3):
    """Pobiera hasło od użytkownika, dopuszczając kilka prób.
    Zwraca `bytes` (nawet b'' jeżeli hasła nie ma)."""
    attempts = 0
    while attempts < max_attempts:
        pwd = ask_cert_password(parent, attempts, max_attempts)  # ← bytes
        # ----------------------------------------------
        # Czy użytkownik anulował?
        # ----------------------------------------------
        if pwd is None:  # <- Anuluj / Esc
            logging.warning("Użytkownik anulował podanie hasła.")
            # attempts = 3
            raise PasswordCancelled("Anulowano podanie hasła.")

        # ----------------------------------------------
        # Spróbuj odczytać plik z podanym hasłem (lub brakiem hasła)
        # ----------------------------------------------
        # Sprawdzamy szybko, czy hasło jest w porządku
        try:
            # Jedynie sprawdzamy, czy OpenSSL zaakceptuje hasło – nie tworzymy signera,
            # bo potem i tak wczytamy go ponownie.
            pkcs12.load_key_and_certificates(
                data=cert_path.read_bytes(),
                password=pwd if pwd else None,
            )
            return pwd
        except Exception as exc:  # niepoprawne hasło
            attempts += 1
            print(f"Nieprawidłowe hasło ({attempts}/{max_attempts}).", file=sys.stderr)
            if attempts >= max_attempts:
                raise RuntimeError("Podano nieprawidłowe hasło za wiele razy.") from exc
    raise PasswordAttemptsExceeded("Podano nieprawidłowe hasło za wiele razy.")


def pkcs12_needs_password(pfx_path: Path) -> bool:
    """
    Zwraca True, jeżeli plik PKCS#12 wymaga podania hasła,
    w przeciwnym wypadku – False.
    """
    try:
        # próbujemy odczytać plik z pustym hasłem
        pkcs12.load_key_and_certificates(
            data=pfx_path.read_bytes(),
            password=None,  # lub b""
        )
        # Brak wyjątku → plik nie chroniony
        return False
    except ValueError:
        return True  # hasło wymagane
    except Exception as exc:
        # COKOLWIEK innego → nie ryzykujemy

        # to jest ok
        # logging.warning(
        #     "Nie udało się sprawdzić, czy certyfikat wymaga hasła (%s) – "
        #     "wymuszam pytanie o hasło",
        #     exc,
        # )
        # return True

        # sprubuj tego
        raise RuntimeError("Błąd odczytu certyfikatu.") from exc


class PasswordDialog(tk.Toplevel):
    """A simple modal password prompt. Returns the password as `bytes`."""

    def __init__(self, parent, title="Hasło do certyfikatu"):
        self._temp_root = None

        if parent is None:
            self._temp_root = tk.Tk()
            self._temp_root.withdraw()
            parent = self._temp_root

        super().__init__(parent)
        self.transient(parent)  # keep dialog on top of parent
        self.title(title)
        self.result = None  # will hold the final bytes value

        # ---------- UI ----------
        self.resizable(False, False)

        ttk.Label(self, text="Podaj hasło do certyfikatu:").grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w"
        )

        self.entry = ttk.Entry(self, show="*")
        self.entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.entry.focus()

        btn_ok = ttk.Button(self, text="OK", command=self.on_ok)
        btn_ok.grid(row=2, column=0, padx=(10, 5), pady=10, sticky="e")

        btn_cancel = ttk.Button(self, text="Anuluj", command=self.on_cancel)
        btn_cancel.grid(row=2, column=1, padx=(5, 10), pady=10, sticky="w")

        # ---- 1) Bindowanie klawiszy ----
        # Enter / Return (z klawiatury i numerycznej)
        self.entry.bind("<Return>", lambda e: self.on_ok())
        self.entry.bind("<KP_Enter>", lambda e: self.on_ok())

        # Escape – zamknięcie dialogu bez podania hasła
        self.entry.bind("<Escape>", lambda e: self.on_cancel())
        # Bindujemy także na samym top‑level, bo czasem focus może być
        # np. na przycisku OK:
        self.bind("<Escape>", lambda e: self.on_cancel())

        # ---- 2) Przycisk OK jako domyślny ----
        # dzięki temu przycisk jest podświetlony i wciśnięcie Enter
        # (gdy focus jest gdziekolwiek) wywoła jego akcję.
        btn_ok.configure(default="active")
        self.bind("<Return>", lambda e: self.on_ok())  # dodatkowy fallback

        # Make the dialog modal
        # pierwsze czekaj na okno aż się wyświetli
        self.update_idletasks()
        self.deiconify()
        self.wait_visibility(self)  # czekaj na okno po będzie Exception
        self.grab_set()  # uniemożliwia interakcję z innymi oknami
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)  # X‑button = Cancel
        self.wait_window(self)  # block until dialog is destroyed


    def on_ok(self):
        pwd = self.entry.get()
        self.result = pwd.encode("utf-8") if pwd else b""
        self.destroy()
        if self._temp_root:
            self._temp_root.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()
        if self._temp_root:
            self._temp_root.destroy()


class PasswordError(RuntimeError):
    """Bazowy typ dla wszystkich błędów związanych z hasłem."""

    pass


class PasswordAttemptsExceeded(PasswordError):
    """Użytkownik popełnił zbyt wiele niepoprawnych prób."""

    pass


class PasswordCancelled(PasswordError):
    """Użytkownik anulował podanie hasła (np. Esc/Cancel)."""

    pass
