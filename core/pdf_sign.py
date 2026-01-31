"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import logging

from pathlib import Path
from pyhanko import stamp
from pyhanko.sign import fields, signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from utils import msgbox, print_info, pkcs12_needs_password, get_password

# logger modułu
logger = logging.getLogger(__name__)


class PdfSigner:
    def __init__(
        self,
        parent,
        pdf_stamp,
        pdf_orig,
        pdf_final,
        logo_path,
        comment,
        cert,
        page_index,
        width,
        height,
        use_visual_stamp,
        on_done=None,
    ):
        print_info("Tworzę plik z graficznym podpisem i tekstem")

        self.parent = parent
        self.pdf_stamp_path = Path(pdf_stamp)
        self.pdf_orig = pdf_orig
        self.pdf_final = pdf_final
        self.logo_path = logo_path
        self.comment = comment
        self.cert = cert
        self.page_index = page_index
        self.width = width
        self.height = height
        self._sign_with_stamp = use_visual_stamp
        self.on_done = on_done

    def sign(self):
        # --- PODPIS CYFROWY ---
        # właściwe podpisanie certyfikatem
        # sprawdzenie śceżki pliku
        CERT_PATH = Path(self.cert)
        if not CERT_PATH.exists():
            msgbox.showerror(
                "Plik nie istnieje",
                f"Wskazany plik certyfikatu nie istnieje:\n{CERT_PATH}",
            )
            return
        elif not CERT_PATH.is_file():
            msgbox.showerror(
                "Nieprawidłowa ścieżka",
                "Wskazana ścieżka do certyfikatu nie jest plikiem.",
            )
            return
        elif CERT_PATH.suffix.lower() != ".p12":
            msgbox.showerror(
                "Nieprawidłowy format", "Wybrany plik nie jest certyfikatem p12."
            )
            return

        if pkcs12_needs_password(CERT_PATH):
            print_info(f"Certyfikat wymaga podania hasła {CERT_PATH}")
            cert_password = get_password(self.parent, CERT_PATH, max_attempts=3)
        else:
            cert_password = b""
        source_pdf_path = self.pdf_orig
        stamp_pdf_path = self.pdf_stamp_path
        output_pdf_path = self.pdf_final
        reason_text = self.comment
        field_name = self.get_next_signature_name(source_pdf_path)

        try:
            signer = signers.SimpleSigner.load_pkcs12(
                pfx_file=CERT_PATH, passphrase=cert_password
            )
            if self._sign_with_stamp and stamp_pdf_path.is_file():
                # podpis wraz z pdf_stamp
                with open(source_pdf_path, "rb") as inf:
                    writer = IncrementalPdfFileWriter(inf)
                    fields.append_signature_field(
                        writer, sig_field_spec=fields.SigFieldSpec(
                            field_name, box=(0, 0, self.width, self.height),on_page=self.page_index
                        )
                    )
                    meta = signers.PdfSignatureMetadata(field_name=field_name,reason=reason_text)
                    pdf_signer = signers.PdfSigner(
                        meta, signer=signer,
                        stamp_style=stamp.StaticStampStyle.from_pdf_file(stamp_pdf_path)
                    )
                    with open(output_pdf_path, 'wb') as outf:
                        pdf_signer.sign_pdf(writer, output=outf)
            else:
                # Sam podpis bez logo
                with open(source_pdf_path, "rb") as inf:
                    writer = IncrementalPdfFileWriter(inf)

                    with open(output_pdf_path, "wb") as outf:
                        signers.sign_pdf(
                            writer,
                            signers.PdfSignatureMetadata(
                                field_name=field_name,
                                reason=reason_text,
                                location="dilmark sp. z o.o.",
                            ),
                            signer=signer,
                            output=outf,  # wynikowy PDF
                        )

            logging.info(f"Podpisano plik {source_pdf_path} i zapisano jako: {output_pdf_path}")
            # zapamiętujemy ścieżkę do dalszego podpisu
            if self.on_done:
                self.on_done(output_pdf_path)
        except Exception as exc:
            msgbox.showerror(
                "Błąd podpisu elektronicznego",
                f"Wystąpił błąd podczas podpisywania dokumentu.\n\nSzczegóły:\n{exc}",
            )

    def get_next_signature_name(self, pdf_path, base="Signature"):
        existing = self.list_signature_fields(pdf_path)
        i = 1
        while f"{base}{i}" in existing:
            i += 1
        return f"{base}{i}"

    def list_signature_fields(self, pdf_path):
        with open(pdf_path, "rb") as f:
            reader = PdfFileReader(f)

            root = reader.root
            if "/AcroForm" not in root:
                return []  # brak formularza = brak podpisów

            acroform = root["/AcroForm"]
            if "/Fields" not in acroform:
                return []

            fields = acroform["/Fields"]

            sig_fields = []
            for field in fields:
                field_obj = field.get_object()
                if field_obj.get("/FT") == "/Sig":
                    sig_fields.append(field_obj.get("/T"))

            return sig_fields
