from pyhanko import stamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers


CERT_PASSWORD = b""
CERT_PATH ="/home/mariusz/.openssl/MariuszDyla.p12"
signer = signers.SimpleSigner.load_pkcs12(
                pfx_file=CERT_PATH, passphrase=CERT_PASSWORD
            )

with open('document.pdf', 'rb') as inf:
    writer = IncrementalPdfFileWriter(inf)
    fields.append_signature_field(
        writer, sig_field_spec=fields.SigFieldSpec(
            'Signature2', box=(0, 0, 550, 760)
        )
    )

    meta = signers.PdfSignatureMetadata(field_name='Signature2')
    pdf_signer = signers.PdfSigner(
        meta, signer=signer,
        stamp_style=stamp.StaticStampStyle.from_pdf_file('sign.pdf')
    )
    with open('document-signed.pdf', 'wb') as outf:
        pdf_signer.sign_pdf(writer, output=outf)
