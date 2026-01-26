"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import fitz
import pikepdf
import tempfile
import logging
import tkinter as tk

from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
from utils.msgbox import print_info
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rcanvas
from reportlab.lib.utils import ImageReader
from utils import msgbox

# logger modułu
logger = logging.getLogger(__name__)


class overlay:
    def __init__(self, parent, pdf_path, logo_path, comment, label_coord, on_done=None):
        logger.debug("Tworzę plik z graficznym podpisem i tekstem")

        self.parent = parent
        self.raw_path = Path(pdf_path)
        self.logo_path = logo_path
        self.comment = comment
        self.LabelCoord = label_coord
        self.on_done = on_done

        self.doc = None
        self.page_index = 0
        self.page_count = 0
        self.preview = None
        self.canvas = None

    def preview_pdf(self):
        # sprawdzenie śceżki pliku
        if not self.raw_path:
            msgbox.showwarning("Brak pliku", "Nie wybrano pliku PDF do podglądu.")
            return
        pdf_path = self.raw_path
        if not pdf_path.exists():
            msgbox.showerror(
                "Plik nie istnieje",
                f"Wskazany plik nie istnieje:\n{pdf_path}"
            )
            return
        elif not pdf_path.is_file():
            msgbox.showerror(
                "Nieprawidłowa ścieżka",
                "Wskazana ścieżka nie jest plikiem."
            )
            return
        elif pdf_path.suffix.lower() != ".pdf":
            msgbox.showerror(
                "Nieprawidłowy format",
                "Wybrany plik nie jest dokumentem PDF."
            )
            return

        self.doc = fitz.open(pdf_path)
        self.page_index = 0
        self.page_count = self.doc.page_count

        self.preview = tk.Toplevel(self.parent)
        self.preview.title("Podgląd PDF")

        self.canvas = tk.Canvas(self.preview)
        self.canvas.pack()

        btn_frame = tk.Frame(self.preview)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="⟵ Poprzednia", command=self.prev_page).pack(
            side="left", padx=5
        )

        tk.Button(btn_frame, text="Następna ⟶", command=self.next_page).pack(
            side="left", padx=5
        )

        self.coordinations = {}

        self.render_page()
        self.canvas.bind("<Button-1>", self.click_event)

    def render_page(self):
        page = self.doc[self.page_index]
        self.pix = page.get_pixmap()
        img = Image.frombytes(
            "RGB", [self.pix.width, self.pix.height], self.pix.samples
        )

        self.preview_img = ImageTk.PhotoImage(img)

        self.canvas.config(width=self.pix.width, height=self.pix.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.preview_img)

        self.preview.title(
            f"Podgląd PDF – strona {self.page_index + 1}/{self.page_count}"
        )

    def next_page(self):
        if self.page_index < self.page_count - 1:
            self.page_index += 1
            self.render_page()

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1
            self.render_page()

    def click_event(self, event):
        # zapis kliknięcia w canvas
        self.coordinations["page"] = self.page_index
        self.coordinations["x"] = event.x
        self.coordinations["y"] = event.y
        self.LabelCoord.configure(
            text=f"Podpis na stronie {self.page_index + 1}, współrzędne: {event.x}x{event.y}"
        )
        print_info(f'Wybrane koordynaty: strona - {self.page_index} współrzędne: {event.x}x{event.y}')
        self.generate_sign()
        self.preview.destroy()

    def generate_sign(self):
        # Data
        data = datetime.now().strftime("%d.%m.%Y").replace('"', "")
        sig_width, sig_height = 130, 30
        raw_path = Path(self.logo_path)
        if not raw_path:
            msgbox.showwarning("Brak pliku", "Nie wybrano pliku png do podglądu.")
            return
        sig_path = raw_path
        if not sig_path.exists():
            msgbox.showerror(
                "Plik nie istnieje",
                f"Wskazany obraz popdisu nie istnieje:\n{sig_path}"
            )
            return
        elif not sig_path.is_file():
            msgbox.showerror(
                "Nieprawidłowa ścieżka",
                "Wskazana obraz popdisu nie jest plikiem."
            )
            return
        elif sig_path.suffix.lower() != ".png":
            msgbox.showerror(
                "Nieprawidłowy format",
                "Wybrany obraz popdisu nie jest dokumentem png."
            )
            return
        text = "Podpisano: Mariusz Dyla"
        textData = f"dnia: {data}"
        textReason = self.comment
        pdfmetrics.registerFont(TTFont("Roboto", "utils/Roboto-MediumItalic.ttf"))

        # Rozmiar strony PDF
        page = self.doc[self.coordinations["page"]]
        page_width = page.rect.width
        page_height = page.rect.height

        # 1 tymczasowy plik z podpisem - TEMP OVERLAY
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as overlay_tmp:
            overlay_path = Path(overlay_tmp.name)
        c = rcanvas.Canvas(str(overlay_path), pagesize=(page_width, page_height))

        # Konwersja Y: Tkinter -> PDF
        pdf_x = self.coordinations["x"]
        pdf_y = page_height - self.coordinations["y"]

        # Wstawienie PNG podpisu
        sig_img = ImageReader(sig_path)
        c.drawImage(
            sig_img,
            pdf_x,
            pdf_y - sig_height,
            width=sig_width,
            height=sig_height,
            mask="auto",
        )

        # Wstawienie tekstu nad podpisem
        text_x = pdf_x
        text_y = pdf_y - sig_height
        textData_y = text_y - 9
        textReason_y = textData_y - 9

        c.setFont("Roboto", 9)
        c.drawString(text_x, text_y, text)
        c.drawString(text_x, textData_y, textData)
        c.drawString(text_x, textReason_y, textReason)
        # zapisanie pliku tymczasoweego z podpisem
        c.save()

        # Scalanie PDF orig i podpisanego
        pdf_path = Path(self.raw_path)
        # 2 tymczasowy plik z podpisem - signed_output.pdf - TEMP PDF PO OVERLAY
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as signed_tmp:
            signed_overlay_pdf = Path(signed_tmp.name)

        with pikepdf.open(pdf_path) as original, pikepdf.open(overlay_path) as sig:
            page = original.pages[self.page_index]
            # Dodajemy podpis jako obrazek na stronie
            page.add_overlay(sig.pages[0])
            original.save(signed_overlay_pdf)

        # zapamiętujemy ścieżkę do dalszego podpisu
        if self.on_done:
            self.on_done(signed_overlay_pdf)

        # sprzątanie
        overlay_path.unlink(missing_ok=True)
