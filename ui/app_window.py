"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import tkinter as tk
import customtkinter
import logging
import subprocess


from tkcalendar import DateEntry
from tkinter import ttk
from pathlib import Path
from datetime import datetime
from config.app_config import app_config
from utils import msgbox, print_info
from utils.file_chooser import FileChooser
from core.pdf_stamp import PdfStampPreview
from core.pdf_sign import PdfSigner

# logger modułu
logger = logging.getLogger(__name__)


class SignPdfApp:
    def __init__(self, initial_pdf: Path | None = None):
        logger.debug("Tworzę okno główne")

        # główne okno aplikacji
        self.window = customtkinter.CTk()
        branch, version = self.get_git_info()
        self.window.title(f"Podpis elektroniczny dokumentów PDF {branch} {version}")
        self.window.geometry("900x300")
        self.window.iconphoto(False, tk.PhotoImage(file="utils/icon.png"))

        self.initial_pdf = initial_pdf
        self.stamp_pdf_path = Path("/tmp")
        self.use_visual_stamp = False
        self.page_index = 0
        self.height = 0
        self.width = 0

        # tworzenie GUI
        self._create_widgets()
        self._bind_events()

    def get_git_info(self):
        # Branch
        try:
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
        except Exception:
            branch = "unknown"

        # Najnowszy tag
        try:
            version = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
        except Exception:
            version = "v0.0"

        return branch, version

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
        self.apply_initial_pdf()

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

        # CheckBox usuń oryginał
        self.VarDeleteSourcePdf = tk.BooleanVar(value=False)
        self.CheckBoxDeleteSourcePdf = customtkinter.CTkCheckBox(
            self.Frame,
            text="Usuń oryginał",
            variable=self.VarDeleteSourcePdf,
        )
        self.CheckBoxDeleteSourcePdf.grid(row=0, column=1, padx=5, pady=5, sticky="we")
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
            text="Wstaw podpis\ni podpisz",
            command=self.create_visual_stamp,
        )
        self.ButtonCoordinates.grid(row=4, column=1, padx=5, pady=35, sticky="we")

        # Przycisk podpisz elektronicznie pdf
        self.ButtonSIGN = customtkinter.CTkButton(
            self.Frame,
            text="Tylko podpisz\ndokument",
            command=self.sign_without_stamp,
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

        # dół lewa strona
        # data i czas - ComboBox
        self.LeftFrame = customtkinter.CTkFrame(
            self.InfoFrameDOWN,
            fg_color="transparent",
            border_width=1,
            height=80,
            width=220,
        )
        self.VarNTP = tk.BooleanVar(value=True)
        self.CheckBoxData = customtkinter.CTkCheckBox(
            self.LeftFrame,
            text="NTP",
            variable=self.VarNTP,
            command=self.toggle_ntp,
        )
        self.ButtonSetDate = tk.Button(
            self.LeftFrame,
            text="Ustaw czas",
            width=8,
            command=lambda: self.ustaw_czas(),
        )
        # Pole daty
        self.EntryDataSet = DateEntry(
            self.LeftFrame, width=10, date_pattern="yyyy-mm-dd"
        )
        # Pole czasu - godziny i minuty
        self.EntryTimeSet = customtkinter.CTkEntry(self.LeftFrame, width=55)
        current_time = datetime.now().strftime("%H:%M")
        self.EntryTimeSet.insert(0, current_time)

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
        self.LeftFrame.grid(row=0, column=0, sticky="ns", padx=(0, 0))
        self.CheckBoxData.grid(row=0, column=0, sticky="w", padx=5, pady=9)
        self.EntryTimeSet.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ButtonSetDate.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        self.EntryDataSet.grid(row=1, column=1, sticky="we", padx=5, pady=5)

        self.RightFrame.grid(row=0, column=1, sticky="nsew")
        self.ButtonCert.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.EntryCert.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.ButtonLogo.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.EntryLogo.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        self.toggle_ntp()
        self.set_app_config()

    def set_app_config(self):
        self.EntryORIG_PDF.insert(0, app_config.data["config_orig_path"])
        self.EntryFINAL_PDF.insert(0, app_config.data["config_final_path"])
        self.EntryComment.insert(0, app_config.data["config_comment"])
        self.EntryCert.insert(0, app_config.data["config_cert"])
        self.EntryLogo.insert(0, app_config.data["config_logo"])

    def save_app_config(self):
        # zapisz dane do pliku konfiguracyjnego aplikacji
        app_config.data["config_orig_path"] = self.EntryORIG_PDF.get()
        app_config.data["config_final_path"] = self.EntryFINAL_PDF.get()
        app_config.data["config_comment"] = self.EntryComment.get()
        app_config.data["config_cert"] = self.EntryCert.get()
        app_config.data["config_logo"] = self.EntryLogo.get()
        app_config.config_save()

    def toggle_ntp(self):
        # print("Checkbox value:", self.VarNTP.get())
        if self.VarNTP.get():
            logger.info("Włączam NTP")
            self.ButtonSetDate.grid_remove()
            self.EntryDataSet.grid_remove()
            self.EntryTimeSet.grid_remove()
            self.set_ntp(True)
        else:
            logger.info("Wyłączam NTP")
            self.ButtonSetDate.grid()
            self.EntryDataSet.grid()
            self.EntryTimeSet.grid()
            self.set_ntp(False)

    def ustaw_czas(self):
        data = self.EntryDataSet.get().strip()
        czas = self.EntryTimeSet.get().strip()
        self.data_czas = f"{data} {czas}"
        print(self.data_czas)
        logger.debug(f"Zmieniam datę na: timedatectl set-time '{self.data_czas}'")
        subprocess.run(["timedatectl", "set-time", str(self.data_czas)])

    def open_dialog(self, widget, tekst, type, inout):
        initial_dir_entry = Path(widget.get().strip())
        initial_dir = initial_dir_entry.parent
        # okno dilogowe
        self.file_path = None

        def on_selected(path):
            self.file_path = path

        dlg = FileChooser(
            self.window,
            start_path=initial_dir,
            extensions=[type],
            title=tekst,
            on_select=on_selected,
        )
        self.window.wait_window(dlg)

        if not self.file_path:
            return  # anulowano
        widget.delete(0, "end")

        if inout == "in":
            widget.insert(0, self.file_path)
            self.rewrite_data()
            logging.info(f"Wybrano plik do odczytu: {tekst}")
        else:
            new_path = Path(self.file_path).with_name(Path(self.file_path).stem + "_sign.pdf")
            widget.insert(0, new_path)
            # path = Path(self.file_path)
            # new_path = path.with_name(path.stem + "_sign.pdf")
            # widget.insert(0, new_path)
            logging.info(f"Wybrano plik do zapisu: {tekst}")

    def rewrite_data(self):
        self.EntryFINAL_PDF.delete(0, "end")
        path = Path(self.EntryORIG_PDF.get().strip())
        new_path = path.with_name(path.stem + "_sign.pdf")
        self.EntryFINAL_PDF.insert(0, new_path)

    def set_ntp(self, enabled: bool):
        value = "true" if enabled else "false"
        try:
            subprocess.run(
                ["timedatectl", "set-ntp", value],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("NTP ustawione na %s", value)
        except subprocess.CalledProcessError as e:
            logger.warning(
                "Nie udało się ustawić NTP (%s): %s",
                value,
                e.stderr.strip(),
            )

    def apply_initial_pdf(self):
        if not self.initial_pdf:
            return

        if not self.initial_pdf.exists():
            return

        self.EntryORIG_PDF.delete(0, "end")
        self.EntryORIG_PDF.insert(0, str(self.initial_pdf))

        # ustawia *_sign.pdf
        self.rewrite_data()

        logger.info(f"GUI: załadowano plik z CLI: {self.initial_pdf}")

    def create_visual_stamp(self):
        self.use_visual_stamp = True
        orig_pdf = Path(self.EntryORIG_PDF.get().strip())

        if not orig_pdf.exists():
            msgbox.showerror("Błąd", "Wybrany źródłowy plik PDF nie istnieje.")
            return

        try:
            self._overlay = PdfStampPreview(
                parent=self.window,
                pdf_path=orig_pdf,
                logo_path=self.EntryLogo.get(),
                comment=self.EntryComment.get(),
                on_done=self.on_stamp_ready,
            )
            self._overlay.preview_pdf()

        except Exception as exc:
            msgbox.showerror("Błąd podglądu PDF", str(exc))

    def on_stamp_ready(self, pdf_stamp_path, page_index, width, height):
        self.stamp_pdf_path = pdf_stamp_path
        self.page_index = page_index
        self.width = width
        self.height = height
        self.sign_pdf()

    def sign_without_stamp(self):
        self.use_visual_stamp = False
        # jeżeli plik pieczątki pdf nie powstał to podstawiamy
        # dowolny katalog aby pyhanko podpisywał bez użycia stamp
        self.stamp_pdf_path = Path("/tmp")
        self.sign_pdf()

    def sign_pdf(self):
        try:
            self._overlay = PdfSigner(
                parent=self.window,
                pdf_stamp=self.stamp_pdf_path,
                pdf_orig=self.EntryORIG_PDF.get(),
                pdf_final=self.EntryFINAL_PDF.get(),
                logo_path=self.EntryLogo.get(),
                comment=self.EntryComment.get(),
                cert=self.EntryCert.get(),
                page_index=self.page_index,
                width=self.width,
                height=self.height,
                use_visual_stamp=self.use_visual_stamp,
                on_done=lambda result_pdf: setattr(self, "result_pdf", result_pdf),
            )
            self._overlay.sign()

        except Exception as exc:
            msgbox.showerror("Błąd podglądu PDF", str(exc))
            return

        self.LabelCoord.configure(
            text=f"Dokument {Path(self.EntryORIG_PDF.get()).name} został podpisany: {Path(self.result_pdf).name}"
        )
        print_info(f"Dokument został podpisany: {self.result_pdf}")
        # Zapisanie ustawień
        self.save_app_config()
        self.set_ntp(True)
        # Wyświetl podpisany pdf
        subprocess.run(["xdg-open", str(self.result_pdf)])
        # usuń podpisywany plik jeżeli ChecBox
        if self.VarDeleteSourcePdf.get():
            src = Path(self.EntryORIG_PDF.get())
            logger.warning(f"Usuwam plik źródłowy do podpisu {src}")
            if src.exists():
                src.unlink()
            else:
                logger.warning(f"Plik źródłowy nie istnieje: {src}")
        # sprzątanie tylko jeżeli faktycznie użyliśmy overlay
        # Usuwanie tymczasowego pliku PDF
        if (
            hasattr(self, "stamp_pdf_path")
            and self.stamp_pdf_path
            and self.stamp_pdf_path.is_file()
        ):
            tmp_pdf = self.stamp_pdf_path
            if tmp_pdf.exists():
                tmp_pdf.unlink()
                logger.info(f"Usunięto tymczasowy plik: {tmp_pdf}")
            else:
                logger.warning(f"Tymczasowy plik nie istnieje: {tmp_pdf}")
        del self.stamp_pdf_path

    def _bind_events(self):
        # obsługa zamknięcia okna
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # wychodząc z programu ustaw czas z NTP
        self.set_ntp(True)
        # Zapamiętaj ustawienia
        self.save_app_config()
        # ukrycie okna
        self.window.withdraw()
        self.window.update_idletasks()
        self.window.after(0, self.window.destroy)

    def run(self):
        # start pętli GUI
        self.window.mainloop()
