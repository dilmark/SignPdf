import os
import sys
from pathlib import Path


def get_resource_path(relative_path=""):
    """
    Uniwersalna funkcja do pobierania ścieżek zasobów.
    Działa dla skryptów .py i skompilowanego pliku Nuitka.
    """
    if hasattr(sys, "frozen"):
        # Jeśli program jest skompilowany (Nuitka/PyInstaller)
        # sys._MEIPASS (dla innych) lub dirname(__file__) dla Nuitka onefile
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Jeśli paths.py jest w podfolderze utils/, musimy wyjść poziom wyżej
        # aby trafić do głównego katalogu zasobów
        base_path = os.path.join(base_path, "..")
    else:
        # Jeśli odpalamy jako czysty python, szukamy względem pliku głównego
        # Zakładamy, że utils/ jest w głównym folderze projektu
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    full_path = os.path.join(base_path, relative_path)
    return os.path.normpath(full_path)


ROOT_DIR = Path(get_resource_path())
