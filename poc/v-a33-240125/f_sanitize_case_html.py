#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f_sanitize_case_html.py

Objetivo:
- Loop: buscar em case_data o documento mais antigo com status="caseScraped"
- Ler campo caseHtml
- Sanitizar mantendo apenas o conteúdo correspondente ao XPath:
  /html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]
- Salvar em caseHtmlSanitized
- Atualizar status para "caseSanitized"
- Repetir até não haver mais documentos "caseScraped"

Dependências:
pip install pymongo beautifulsoup4 lxml

Observação:
- XPath "estrito" é aplicado via lxml.html, que suporta xpath() corretamente.
"""

import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from lxml import html as lxml_html
from lxml.etree import tostring


# =========================
# Mongo (fixo)
# =========================
MONGO_USER = "cito"
MONGO_PASS = "fyu9WxkHakGKHeoq"
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gb8bzlp.mongodb.net/?appName=Cluster0"
DB_NAME = "cito-v-a33-240125"
COLLECTION = "case_data"

STATUS_INPUT = "caseScraped"
STATUS_OK = "caseSanitized"
STATUS_ERROR = "caseSanitizeError"

XPATH_KEEP = "/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]"


# =========================
# Mongo helpers
# =========================
def get_collection() -> Collection:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION]


def fetch_oldest_to_sanitize(col: Collection) -> Optional[Dict[str, Any]]:
    return col.find_one({"status": STATUS_INPUT}, sort=[("_id", 1)])


def mark_success(col: Collection, doc_id, *, sanitized_html: str) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "caseHtmlSanitized": sanitized_html,
            "caseHtmlSanitizedAt": datetime.now(timezone.utc),
            "status": STATUS_OK,
        }}
    )


def mark_error(col: Collection, doc_id, *, error_msg: str) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "caseHtmlSanitizedError": error_msg,
            "caseHtmlSanitizedAt": datetime.now(timezone.utc),
            "status": STATUS_ERROR,
        }}
    )


# =========================
# Sanitização via XPath
# =========================
def sanitize_html_keep_xpath(full_html: str) -> str:
    """
    Mantém apenas o nó retornado pelo XPATH_KEEP.
    Retorna um HTML mínimo contendo só o fragmento sanitizado.
    """
    if not full_html or not full_html.strip():
        raise ValueError("caseHtml vazio ou ausente")

    # Parse tolerante de HTML
    doc = lxml_html.fromstring(full_html)

    nodes = doc.xpath(XPATH_KEEP)
    if not nodes:
        raise ValueError(f"XPath não encontrado no HTML: {XPATH_KEEP}")

    node = nodes[0]

    # Serializa apenas o fragmento selecionado
    fragment_html = tostring(node, encoding="unicode", method="html")

    # Envolve em um documento HTML mínimo (facilita armazenamento/visualização)
    sanitized = (
        "<!doctype html>\n"
        "<html>\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\" />\n"
        "    <title>caseHtmlSanitized</title>\n"
        "  </head>\n"
        "  <body>\n"
        f"{fragment_html}\n"
        "  </body>\n"
        "</html>\n"
    )

    return sanitized


# =========================
# Loop principal
# =========================
def run_loop() -> int:
    col = get_collection()
    processed = 0

    while True:
        doc = fetch_oldest_to_sanitize(col)
        if not doc:
            print(f"✅ Nenhum documento restante com status='{STATUS_INPUT}'. Encerrando.")
            break

        doc_id = doc["_id"]
        html_raw = doc.get("caseHtml") or ""

        print("=" * 70)
        print(f"Sanitizando: _id={doc_id} status={doc.get('status')}")
        print(f"caseHtml len={len(html_raw)}")

        try:
            sanitized = sanitize_html_keep_xpath(html_raw)
            mark_success(col, doc_id, sanitized_html=sanitized)
            processed += 1
            print(f"✔ OK: status='{STATUS_OK}' | caseHtmlSanitized len={len(sanitized)}")

        except Exception as e:
            mark_error(col, doc_id, error_msg=str(e))
            print(f"✖ ERRO: {e}")

    print(f"🏁 Finalizado. Total processado: {processed}")
    return 0


if __name__ == "__main__":
    sys.exit(run_loop())
