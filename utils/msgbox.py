"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)


def showinfo(title, message):
    logger.info("%s: %s", title, message)
    messagebox.showinfo(title, message)


def showwarning(title, message):
    logger.warning("%s: %s", title, message)
    ask = messagebox.askyesno(title, message)
    return ask


def showerror(title, message):
    logger.error("%s: %s", title, message)
    messagebox.showerror(title, message)


def print_info(*args):
    """Loguje dowolną liczbę argumentów jak print, do konsoli i do pliku"""
    msg = " ".join(str(a) for a in args)  # zamień wszystkie argumenty na string
    logger.info(msg)  # zapis do pliku
    print(msg)  # tradycyjny print
