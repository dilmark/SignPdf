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
import argparse
import os
import sys
import subprocess
import fitz


from pathlib import Path
from ui.app_window import SignPdfApp
from core.pdf_sign import PdfSigner
from config.app_config import app_config
from tkinter import simpledialog

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

    initial_pdf = None
    args = parse_args()

    if args.cli:
        if not args.pdf:
            print("❌ Brak pliku PDF")
            return

        exit_code = sign_no_gui(Path(args.pdf).expanduser())
        return exit_code
    if (
        args.pdf
        and Path(args.pdf).exists()
        and Path(args.pdf).is_file()
        and Path(args.pdf).suffix.lower() == ".pdf"
    ):
        initial_pdf = Path(args.pdf).expanduser()
    else:
        initial_pdf = None
    app = SignPdfApp(initial_pdf=initial_pdf)
    app.run()

    logging.info("STOP aplikacji")


def parse_args():
    parser = argparse.ArgumentParser(description="Podpis elektroniczny dokumentów PDF")
    parser.add_argument(
        "pdf",
        nargs="?",
        help="Ścieżka do pliku PDF",
    )
    parser.add_argument(
        "--no_gui",
        "--cli",
        "-c",
        "-ng",
        dest="cli",
        action="store_true",
        help="Podpisz dokument bez uruchamiania GUI",
    )

    args = parser.parse_args()
    # Walidacja
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
            sys.exit(
                f"ERROR: Podany plik PDF nie istnieje lub ma zły format: {args.pdf}"
            )
    elif args.cli:
        sys.exit("ERROR: W trybie CLI musisz podać plik PDF do podpisu!")

    return args


def sign_no_gui(pdf_path: Path):
    if not pdf_path.exists():
        print(f"❌ Plik nie istnieje: {pdf_path}")
        return 1

    output_pdf = pdf_path.with_name(pdf_path.stem + "_sign.pdf")
    # obsługa hasła dokumentu pdf gdy idziemy w trybie bez wskazywania pieczątki
    pdf_pass = None
    doc = fitz.open(pdf_path)
    if doc.is_encrypted:
        print("PDF jest zaszyfrowany")
        if not doc.can_save_incrementally:
            print("Ten dokument jest chroniony przed zmianami.")
            raise ValueError("Ten dokument jest chroniony przed zmianami.")
        authenticated = False
        attemp = 0
        while not authenticated and attemp < 3:
            pdf_pass = simpledialog.askstring(
                "Plik zabezpieczony", "Podaj hasło do pliku PDF:", show="*", parent=None
            )

            if pdf_pass is None:  # Użytkownik kliknął Anuluj
                doc.close()
                return

            if doc.authenticate(pdf_pass):
                authenticated = True
            else:
                attemp += 1
                if attemp == 3:
                    print("Nieprawidłowe hasło otwarcia dokumentu pdf")
                else:
                    print("Błąd", "Nieprawidłowe hasło!")

    signer = PdfSigner(
        parent=None,  # brak GUI
        pdf_stamp=Path("/tmp"),  # brak stempla
        pdf_orig=str(pdf_path),
        pdf_final=str(output_pdf),
        logo_path=app_config.data["config_logo"],
        comment=app_config.data["config_comment"],
        cert=app_config.data["config_cert"],
        page_index=0,
        width=0,
        height=0,
        use_visual_stamp=False,
        pdf_password=pdf_pass,
        on_done=None,
    )

    try:
        signer.sign()
    except Exception as exc:
        print(f"❌ Błąd podpisu: {exc}")
        return 2

    print(f"✅ Podpisano dokument: {output_pdf}")
    subprocess.run(["xdg-open", str(output_pdf)])
    return 0


if __name__ == "__main__":
    main()
