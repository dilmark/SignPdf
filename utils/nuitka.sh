python -m nuitka --standalone --onefile \
--enable-plugin=tk-inter \
--include-package-data=customtkinter \
--include-data-files=image/icon.png=image/icon.png \
--include-data-files=utils/Roboto-MediumItalic.ttf=utils/Roboto-MediumItalic.ttf \
--remove-output \
--output-dir=dist \
-o SignPdf SignPdf.py
