#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f_sanitize_case_html.py

Objetivo:
- Loop: buscar em case_data o documento mais antigo com status="caseScraped"
- Ler campo caseHtml
- Recortar o conteúdo correspondente ao XPath:
  /html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]
- Converter o conteúdo para TEXTO PURO (sem HTML, CSS ou JS)
- Salvar o texto em caseHtmlSanitized
- Atualizar status para "caseSanitized"
- Repetir até não haver mais documentos "caseScraped"

Dependências:
pip install pymongo lxml

Observação:
- XPath "estrito" é aplicado via lxml.html, que suporta xpath() corretamente.
"""

import re
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Iterable

from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from lxml import html as lxml_html
from lxml.etree import _Element  # type: ignore


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
STATUS_PROCESSING = "caseSanitizing"

XPATH_KEEP = "/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]"


# =========================
# Mongo helpers
# =========================
def get_collection() -> Collection:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION]


def claim_oldest_to_sanitize(col: Collection) -> Optional[Dict[str, Any]]:
    return col.find_one_and_update(
        {"status": STATUS_INPUT},  # caseScraped
        {"$set": {"status": STATUS_PROCESSING, "caseHtmlSanitizingAt": datetime.now(timezone.utc)}},
        sort=[("_id", 1)],
        return_document=ReturnDocument.AFTER,
    )


def mark_success(col: Collection, doc_id, *, sanitized_text: str) -> None:
    col.update_one(
        {"_id": doc_id, "status": STATUS_PROCESSING},
        {"$set": {
            "caseHtmlSanitized": sanitized_text,  # agora é TEXTO PURO
            "caseHtmlSanitizedAt": datetime.now(timezone.utc),
            "status": STATUS_OK,  # caseSanitized
        }}
    )


def mark_error(col: Collection, doc_id, *, error_msg: str) -> None:
    col.update_one(
        {"_id": doc_id, "status": STATUS_PROCESSING},
        {"$set": {
            "caseHtmlSanitizedError": error_msg,
            "caseHtmlSanitizedAt": datetime.now(timezone.utc),
            "status": STATUS_ERROR,
        }}
    )


# =========================
# Texto puro (helpers)
# =========================
_BLOCK_BREAK_TAGS = {
    "p", "div", "section", "article", "header", "footer", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "table", "thead", "tbody", "tfoot", "tr",
    "blockquote", "pre",
}

_LINE_BREAK_TAGS = {"br"}


def _normalize_text(s: str) -> str:
    # normaliza espaços por linha e remove excesso de linhas em branco
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t\f\v]+", " ", s)          # espaços repetidos
    s = re.sub(r"\n[ \t]+", "\n", s)           # espaços no início da linha
    s = re.sub(r"[ \t]+\n", "\n", s)           # espaços no fim da linha
    s = re.sub(r"\n{3,}", "\n\n", s)           # no máximo 1 linha em branco
    return s.strip()


def _element_to_text_preserve_breaks(root: _Element) -> str:
    """
    Converte um elemento HTML em TEXTO PURO, preservando quebras de linha
    aproximadas por tags de bloco e <br>.
    """
    parts: list[str] = []

    def emit(text: str) -> None:
        if text:
            parts.append(text)

    def walk(node: _Element) -> None:
        tag = (node.tag or "").lower() if isinstance(node.tag, str) else ""

        # remove conteúdos indesejados
        if tag in ("script", "style", "noscript"):
            return

        # texto direto antes dos filhos
        if node.text and node.text.strip():
            emit(node.text)

        # percorre filhos
        for child in node:
            ctag = (child.tag or "").lower() if isinstance(child.tag, str) else ""

            if ctag in _LINE_BREAK_TAGS:
                emit("\n")
            else:
                walk(child)

            # tail após o filho
            if child.tail and child.tail.strip():
                emit(child.tail)

            # quebra de bloco após certos elementos
            if ctag in _BLOCK_BREAK_TAGS:
                emit("\n")

        # quebra final para elementos de bloco
        if tag in _BLOCK_BREAK_TAGS:
            emit("\n")

    walk(root)
    return _normalize_text("".join(parts))


# =========================
# Sanitização via XPath -> TEXTO PURO
# =========================
def sanitize_html_keep_xpath(full_html: str) -> str:
    """
    - Mantém apenas o nó retornado pelo XPATH_KEEP
    - Remove JS/CSS pela própria conversão
    - Retorna TEXTO PURO (sem HTML)
    """
    if not full_html or not full_html.strip():
        raise ValueError("caseHtml vazio ou ausente")

    # Parse tolerante de HTML
    doc = lxml_html.fromstring(full_html)

    nodes = doc.xpath(XPATH_KEEP)
    if not nodes:
        raise ValueError(f"XPath não encontrado no HTML: {XPATH_KEEP}")

    node = nodes[0]

    # Converte para texto puro com preservação aproximada de quebras
    text = _element_to_text_preserve_breaks(node)

    if not text:
        raise ValueError("Conteúdo recortado pelo XPath resultou em texto vazio.")

    return text


# =========================
# Loop principal
# =========================
def run_loop() -> int:
    col = get_collection()
    processed = 0

    while True:
        doc = claim_oldest_to_sanitize(col)

        if not doc:
            print(f"✅ Nenhum documento restante com status='{STATUS_INPUT}'. Encerrando.")
            break

        doc_id = doc["_id"]
        html_raw = doc.get("caseHtml") or ""

        print("=" * 70)
        print(f"Sanitizando (texto puro): _id={doc_id} status={doc.get('status')}")
        print(f"caseHtml len={len(html_raw)}")

        try:
            sanitized_text = sanitize_html_keep_xpath(html_raw)
            mark_success(col, doc_id, sanitized_text=sanitized_text)
            processed += 1
            print(f"✔ OK: status='{STATUS_OK}' | caseHtmlSanitized(text) len={len(sanitized_text)}")

        except Exception as e:
            mark_error(col, doc_id, error_msg=str(e))
            print(f"✖ ERRO: {e}")

    print(f"🏁 Finalizado. Total processado: {processed}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_loop())
    except PyMongoError:
        sys.exit(2)
    except Exception:
        sys.exit(1)
