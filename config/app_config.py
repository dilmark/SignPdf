"""
Program do podpisu elektronicznego dokumentów pdf
Copyright (C) styczeń 2026  autor - Mariusz Dyla - dilmark dla dilmark sp. z o.o.

GNU GPL v3
"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "app_config.json"


DEFAULT_CONFIG = {
    "config_orig_path": "document.pdf",
    "config_final_path": "document_sign.pdf",
    "config_comment": "PKCS#12 sign",
    "config_cert": "utils/sign.p12",
    "config_logo": "utils/sign.png"
}


class AppConfig:
    def __init__(self):
        self.data = DEFAULT_CONFIG.copy()
        self.config_load()

    def config_load(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self.data.update(loaded)

    def config_save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)


app_config = AppConfig()
