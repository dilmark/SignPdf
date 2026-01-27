"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import tkinter as tk
import customtkinter
import logging
import os

from tkcalendar import DateEntry
from tkinter import ttk, filedialog
from pathlib import Path
from datetime import datetime
from utils.app_config import config
from utils import msgbox
from utils.msgbox import print_info
from utils.pdf_overlay import Overlay
from utils.pdf_sign import Sign

# logger modułu
logger = logging.getLogger(__name__)


class PodpisApp:
    def __init__(self):
        logger.debug("Tworzę okno główne")

        # główne okno aplikacji
        self.window = customtkinter.CTk()
        self.window.title("Podpis elektroniczny dokumentów pdf")
        self.window.geometry("900x300")
        self.window.iconphoto(False, tk.PhotoImage(file="utils/icon.png"))

        # tworzenie GUI
        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        # główny kontener zakładek
        self.tabview = ttk.Notebook(self.window)
        # definicje zakładek
        self.tab_podpis = ttk.Frame(self.tabview)
        self.tab_info = ttk.Frame(self.tabview)
        # dodanie zakładek
        self.tabview.add(self.tab_podpis, text="Podpis")
        self.tabview.add(self.tab_info, text="O programie")
        self.tabview.pack(fill="both", expand=True)

        # inicjalizacja zawartości zakładek
        self._create_podpis_tab()
        self._create_info_tab()

    def _create_podpis_tab(self):
        # konfiguracja layoutu
        self.tab_podpis.grid_rowconfigure(0, weight=1)  # główna zawartość
        self.tab_podpis.grid_rowconfigure(1, weight=0)  # belka statusu
        self.tab_podpis.grid_columnconfigure(0, weight=1)

        my_font = customtkinter.CTkFont(family="Roboto", size=13, weight="bold")

        # górny panel filtrów
        self.Frame = customtkinter.CTkFrame(self.tab_podpis, border_width=0)
        self.Frame.grid(row=0, column=0, padx=3, pady=0, sticky="nswe")
        self.FrameDown = customtkinter.CTkFrame(self.tab_podpis, border_width=1)
        self.FrameDown.grid(row=1, column=0, padx=3, pady=0, sticky="sew")

        # Label
        self.MainLabel = customtkinter.CTkLabel(
            self.Frame, text="Konfiguracja programu"
        )
        self.MainLabel.grid(row=0, column=2, padx=5, pady=5, sticky="we")

        # Przycisk - Wybierz plik do podpisu
        self.ButtonORIG_PDF = customtkinter.CTkButton(
            self.Frame,
            text="Wybierz plik do podpisu",
            command=lambda: self.open_dialog(
                self.EntryORIG_PDF, "Otwórz plik do podpisu", "pdf", "in"
            ),
        )
        self.ButtonORIG_PDF.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        self.EntryORIG_PDF = customtkinter.CTkEntry(self.Frame, width=700)
        self.EntryORIG_PDF.grid(row=1, column=2, padx=5, pady=5, sticky="we")

        # Przycisk - Wybierz plik do zapisania
        self.ButtonFINAL_PDF = customtkinter.CTkButton(
            self.Frame,
            text="Zapisz pdf jako",
            command=lambda: self.open_dialog(
                self.EntryFINAL_PDF, "Zapisz plik jako", "pdf", "out"
            ),
        )
        self.ButtonFINAL_PDF.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        self.EntryFINAL_PDF = customtkinter.CTkEntry(self.Frame, width=700)
        self.EntryFINAL_PDF.grid(row=2, column=2, padx=5, pady=5, sticky="we")

        # Komentarz
        self.LabelComment = customtkinter.CTkLabel(self.Frame, text="Treść komentarza")
        self.LabelComment.grid(row=3, column=1, padx=5, pady=5, sticky="we")

        self.EntryComment = customtkinter.CTkEntry(self.Frame, width=700)
        self.EntryComment.grid(row=3, column=2, padx=5, pady=5, sticky="we")

        # Przycisk - wstaw podpis
        self.ButtonCoordinates = customtkinter.CTkButton(
            self.Frame,
            text="Wstaw podpis",
            command=self.preview_pdf,
        )
        self.ButtonCoordinates.grid(row=4, column=1, padx=5, pady=35, sticky="we")

        # Przycisk podpisz elektronicznie pdf
        self.ButtonSIGN = customtkinter.CTkButton(
            self.Frame,
            text="Podpisz dokument",
            command=self.sign_pdf,
        )
        self.ButtonSIGN.grid(row=4, column=2, padx=5, pady=35, sticky="e")

        # Belks statusu
        self.LabelCoord = customtkinter.CTkLabel(
            self.FrameDown, text="Konfiguracja: Brak widocznego podpisu.", font=my_font
        )
        self.LabelCoord.grid(padx=3, pady=2, sticky="nwe")

    def _create_info_tab(self):
        # układ zakładki informacji
        self.tab_info.columnconfigure(0, weight=1)
        self.tab_info.rowconfigure(1, weight=1)

        my_font = customtkinter.CTkFont(family="Roboto", size=14, weight="bold")
        self.InfoFrameUP = customtkinter.CTkFrame(self.tab_info, border_width=0)

        # informacje o firmie i autorze
        self.InfoLine1 = customtkinter.CTkLabel(
            self.InfoFrameUP,
            text="\nProgram dla dilmark sp. z o. o.",
            text_color="darkgreen",
            font=my_font,
        )
        self.InfoLine2 = tk.Label(
            self.InfoFrameUP,
            text="NIP: 652 175 42 36\n43-502, Czechowice-Dziedzice\nul. Legionów 87A",
            font=my_font,
        )
        self.InfoLine3 = tk.Label(
            self.InfoFrameUP,
            text=(
                "napisany przez:\n"
                "Mariusz Dyla\n"
                "mail: mariusz.dyla@dilmark.pl\n"
                "tel.: +48 602 47 47 18"
            ),
            font=my_font,
        )

        # Sterowanie porgramem
        self.InfoFrameDOWN = customtkinter.CTkFrame(self.tab_info, border_width=0)
        # Label
        self.LabelConf = customtkinter.CTkLabel(
            self.InfoFrameDOWN, text="Konfiguracja programu", font=my_font, width=250
        )

        # dół prawa strona
        self.RightFrame = customtkinter.CTkFrame(
            self.InfoFrameDOWN, fg_color="transparent", border_width=1
        )
        # Przycisk - Wybierz plik certyfikatu do podpisu
        self.ButtonCert = tk.Button(
            self.RightFrame,
            text="Wybierz certyfikat",
            width=15,
            command=lambda: self.open_dialog(
                self.EntryCert, "Otwórz plik certyfikatu", "p12", "in"
            ),
        )
        # Pole wyboru certyfikatu
        self.EntryCert = customtkinter.CTkEntry(self.RightFrame, width=450)
        # Pole wyboru pliku loga
        self.ButtonLogo = tk.Button(
            self.RightFrame,
            text="Wybierz logo",
            width=15,
            command=lambda: self.open_dialog(
                self.EntryLogo, "Otwórz plik logo", "png", "in"
            ),
        )
        self.EntryLogo = customtkinter.CTkEntry(self.RightFrame, width=450)

        # data i czas - ComboBox
        self.LeftFrame = customtkinter.CTkFrame(
            self.InfoFrameDOWN,
            fg_color="transparent",
            border_width=1,
            height=80,
            width=220,
        )
        self.LeftFrame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.CheckBoxData = customtkinter.CTkCheckBox(
            self.LeftFrame, width=2, height=2, text=""
        )
        self.VarNTP = tk.BooleanVar(value=True)
        self.CheckBoxData = customtkinter.CTkCheckBox(
            self.LeftFrame,
            text="NTP",
            variable=self.VarNTP,
            command=self.togle_ntp,
        )
        # Pole daty
        self.EntryDataSet = DateEntry(
            self.LeftFrame, width=10, date_pattern="yyyy-mm-dd"
        )
        # Pole czasu - godziny i minuty
        self.EntryTimeSet = customtkinter.CTkEntry(self.LeftFrame, width=95)
        self.EntryTimeSet.bind("<Return>", lambda e: self.ustaw_czas())
        current_time = datetime.now().strftime("%H:%M:%S")
        self.EntryTimeSet.insert(0, current_time)

        # rozmieszczenie elementów góra
        self.InfoFrameUP.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.InfoFrameUP.grid_columnconfigure((0, 1), weight=1)
        self.InfoLine1.grid(row=0, column=0, columnspan=2, pady=(10, 5))
        self.InfoLine2.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.InfoLine3.grid(row=1, column=1, padx=20, pady=5, sticky="e")
        # rozmieszczenie elementów dół
        self.InfoFrameDOWN.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.InfoFrameDOWN.grid_columnconfigure(0, weight=0)
        self.InfoFrameDOWN.grid_columnconfigure(1, weight=1)

        self.LeftFrame.grid_propagate(False)
        self.CheckBoxData.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.EntryDataSet.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.EntryTimeSet.grid(row=1, column=1, sticky="e", padx=5, pady=5)

        self.RightFrame.grid(row=0, column=1, sticky="nsew")
        self.ButtonCert.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.EntryCert.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.ButtonLogo.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.EntryLogo.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        self.togle_ntp()
        self.set_app_config()

    def set_app_config(self):
        self.EntryORIG_PDF.insert(0, config.data["config_orig_path"])
        self.EntryFINAL_PDF.insert(0, config.data["config_final_path"])
        self.EntryComment.insert(0, config.data["config_comment"])
        self.EntryCert.insert(0, config.data["config_cert"])
        self.EntryLogo.insert(0, config.data["config_logo"])

    def save_app_config(self):
        # zapisz dane do pliku konfiguracyjnego aplikacji
        config.data["config_orig_path"] = self.EntryORIG_PDF.get()
        config.data["config_final_path"] = self.EntryFINAL_PDF.get()
        config.data["config_comment"] = self.EntryComment.get()
        config.data["config_cert"] = self.EntryCert.get()
        config.data["config_logo"] = self.EntryLogo.get()
        config.config_save()

    def togle_ntp(self):
        # print("Checkbox value:", self.VarNTP.get())
        if self.VarNTP.get():
            logger.info("Włączam NTP")
            self.EntryDataSet.grid_remove()
            self.EntryTimeSet.grid_remove()
            os.system("timedatectl set-ntp true")
        else:
            logger.info("Wyłączam NTP")
            self.EntryDataSet.grid()
            self.EntryTimeSet.grid()
            os.system("timedatectl set-ntp false")

    def ustaw_czas(self):
        data = self.EntryDataSet.get().strip()
        czas = self.EntryTimeSet.get().strip()
        self.data_czas = f"{data} {czas}"
        print(self.data_czas)
        logger.debug(f"Zmieniam datę na: timedatectl set-time '{self.data_czas}'")
        os.system(f"timedatectl set-time '{self.data_czas}'")

    def open_dialog(self, widget, tekst, type, inout):
        initial_dir_entry = Path(widget.get().strip())
        initial_dir = initial_dir_entry.parent
        if inout == "in":
            # okno dilogowe
            file_path = filedialog.askopenfilename(
                title=tekst,
                filetypes=[("Pliki " + type, "*." + type)],
                initialdir=str(initial_dir),
            )

            if not file_path:
                return  # anulowano
            widget.delete(0, "end")
            widget.insert(0, file_path)
            self.rewrite_data()
            logging.info(f"Wybrano plik do odczytu: {tekst}")
        else:
            # okno dilogowe
            file_path = filedialog.asksaveasfilename(
                title=tekst,
                filetypes=[("Pliki " + type, "*." + type)],
                initialdir=str(initial_dir),
            )

            if not file_path:
                return  # anulowano
            widget.delete(0, "end")
            path = Path(file_path)
            new_path = path.with_name(path.stem + "_sign.pdf")
            widget.insert(0, new_path)
            logging.info(f"Wybrano plik do zapisu: {tekst}")

    def rewrite_data(self):
        self.EntryFINAL_PDF.delete(0, "end")
        path = Path(self.EntryORIG_PDF.get().strip())
        new_path = path.with_name(path.stem + "_sign.pdf")
        self.EntryFINAL_PDF.insert(0, new_path)

    def preview_pdf(self):
        orig_pdf = Path(self.EntryORIG_PDF.get().strip())

        if not orig_pdf.exists():
            msgbox.showerror("Błąd", "Wybrany plik PDF nie istnieje.")
            return

        try:
            self._overlay = Overlay(
                parent=self.window,
                pdf_path=orig_pdf,
                logo_path=self.EntryLogo.get(),
                comment=self.EntryComment.get(),
                label_coord=self.LabelCoord,
                on_done=self._on_overlay_ready,
            )
            self._overlay.preview_pdf()

        except Exception as e:
            msgbox.showerror("Błąd podglądu PDF", str(e))

    def _on_overlay_ready(self, result_pdf):
        """Dostajemy gotowy PDF z overlay"""
        self._overlay_result_pdf = result_pdf

    def sign_pdf(self):
        pdf_overlay = Path(self._overlay_result_pdf)

        if not pdf_overlay.exists():
            msgbox.showerror("Błąd", "Wybrany plik PDF nie istnieje.")
            return

        try:
            # def __init__(self, parent, pdf_overlay, pdf_orig, pdf_final, logo_path, comment, cert, on_done=None):
            self._overlay = Sign(
                parent=self.window,
                pdf_overlay=pdf_overlay,
                pdf_orig=self.EntryORIG_PDF.get(),
                pdf_final=self.EntryFINAL_PDF.get(),
                logo_path=self.EntryLogo.get(),
                comment=self.EntryComment.get(),
                cert=self.EntryCert.get(),
                on_done=lambda result_pdf: setattr(self, "result_pdf", result_pdf),
            )
            self._overlay.electronic_sign()

        except Exception as e:
            msgbox.showerror("Błąd podglądu PDF", str(e))
        self.LabelCoord.configure(
            text=f"Dokument został podpisany: {self.result_pdf}"
        )
        print_info(
            f"Dokument został podpisany: {self.result_pdf}"
        )
        # Wyświetl podpisany pdf
        os.system(f"xdg-open {self.result_pdf}")
        # sprzątanie tylko jeżeli faktycznie użyliśmy overlay
        if self._overlay_result_pdf and self._overlay_result_pdf.exists():
            self._overlay_result_pdf.unlink(missing_ok=True)
            del self._overlay_result_pdf
        # Zapisanie ustawień
        self.save_app_config()
        os.system("timedatectl set-ntp true")

    def _bind_events(self):
        # obsługa zamknięcia okna
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # wychodząc z programu ustaw czas z NTP
        os.system("timedatectl set-ntp true")
        # Zapamiętaj ustawienia
        self.save_app_config()
        # ukrycie okna
        self.window.withdraw()
        self.window.update_idletasks()
        self.window.after(0, self.window.destroy)

    def run(self):
        # start pętli GUI
        self.window.mainloop()
