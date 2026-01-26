"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

Informacja o licencji:
Program jest rozpowszechniany na licencji GNU GPL v3 lub nowszej.
Użytkownik ma prawo do uruchamiania, modyfikowania i dalszej dystrybucji
zgodnie z warunkami tej licencji.

Brak gwarancji:
Program jest dostarczany „tak jak jest”, bez jakiejkolwiek gwarancji,
w tym przydatności handlowej lub do określonego celu.

Pełny tekst licencji:
Znajduje się w pliku COPYING lub pod adresem:
https://www.gnu.org/licenses/gpl-3.0.en.html
"""

import logging
import os

from utils.app import PodpisApp

# Wyłącz IBus dla tej aplikacji - nie będzie wisiało przy zamykaniu
os.environ["GTK_IM_MODULE"] = "none"
os.environ["XMODIFIERS"] = "@im=none"


def main():
    logging.basicConfig(
        filename="utils/SignPdf.log",
        filemode="a",
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("START aplikacji")
    app = PodpisApp()
    app.run()
    logging.info("STOP aplikacji")


if __name__ == "__main__":
    main()
