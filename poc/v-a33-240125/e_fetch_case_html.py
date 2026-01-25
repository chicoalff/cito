#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
e_fetch_case_html.py

Requisitos atendidos:
- Buscar na collection "case_data" o documento mais antigo com status="extracted"
- Ler o campo caseUrl
- Acessar caseUrl e obter o HTML integral (renderizado, se necessário)
- Atualizar o documento em "case_data":
    - caseHtml: HTML completo
    - caseHtmlScrapedAt (UTC)
    - status: "caseScraped"

Correção para Codespaces/SSL:
- NÃO usa requests por padrão (evita SSLCertVerificationError no container).
- Usa Playwright headless para obter o HTML (navegador lida com SSL/JS melhor nesse ambiente).
- Opcional: habilitar fallback requests com env USE_REQUESTS_FIRST=true

Env vars:
- USE_REQUESTS_FIRST=true|false (default false)
- STF_SSL_VERIFY=true|false (default true)  # usado apenas no requests
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

import certifi
import requests
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


# =========================
# Mongo (fixo)
# =========================
MONGO_USER = "cito"
MONGO_PASS = "fyu9WxkHakGKHeoq"
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gb8bzlp.mongodb.net/?appName=Cluster0"
DB_NAME = "cito-v-a33-240125"
COLLECTION = "case_data"

STATUS_INPUT = "extracted"
STATUS_OK = "caseScraped"
STATUS_ERROR = "caseScrapeError"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


USE_REQUESTS_FIRST = _env_bool("USE_REQUESTS_FIRST", False)
SSL_VERIFY = _env_bool("STF_SSL_VERIFY", True)


# =========================
# Mongo helpers
# =========================
def get_collection() -> Collection:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION]


def fetch_oldest_extracted(col: Collection) -> Optional[Dict[str, Any]]:
    return col.find_one({"status": STATUS_INPUT}, sort=[("_id", 1)])


def mark_success(col: Collection, doc_id, *, html: str) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "caseHtml": html,
            "caseHtmlScrapedAt": datetime.now(timezone.utc),
            "status": STATUS_OK,
        }}
    )


def mark_error(col: Collection, doc_id, *, error_msg: str) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "caseHtmlError": error_msg,
            "caseHtmlScrapedAt": datetime.now(timezone.utc),
            "status": STATUS_ERROR,
        }}
    )


# =========================
# requests (opcional)
# =========================
def fetch_html_requests(url: str) -> Tuple[str, int]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://jurisprudencia.stf.jus.br/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    verify_opt = certifi.where() if SSL_VERIFY else False
    if not SSL_VERIFY:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    resp = requests.get(url, headers=headers, timeout=60, verify=verify_opt)
    resp.raise_for_status()
    resp.encoding = resp.encoding or "utf-8"
    return resp.text, resp.status_code


# =========================
# Playwright (principal)
# =========================
async def fetch_html_playwright(url: str) -> str:
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise RuntimeError(
            "Playwright não disponível. Instale com: pip install playwright && playwright install"
        ) from e

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=USER_AGENT,
            extra_http_headers={"accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"},
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60_000)
            await page.wait_for_timeout(3000)
            return await page.content()
        finally:
            await browser.close()


# =========================
# Main
# =========================
async def main() -> int:
    col: Optional[Collection] = None
    doc_id = None

    try:
        col = get_collection()
        doc = fetch_oldest_extracted(col)

        if not doc:
            print(f"Nenhum documento em {DB_NAME}.{COLLECTION} com status='{STATUS_INPUT}'.")
            return 0

        doc_id = doc["_id"]
        case_url = (doc.get("caseUrl") or "").strip()

        print(f"Mongo: db={DB_NAME} collection={COLLECTION}")
        print(f"Doc: _id={doc_id} status={doc.get('status')}")
        print(f"caseUrl: {case_url}")

        if not case_url:
            msg = "Documento não possui 'caseUrl'."
            print(f"❌ {msg}")
            mark_error(col, doc_id, error_msg=msg)
            return 1

        html = ""

        # Preferência: Playwright (evita SSL do requests no Codespaces)
        if USE_REQUESTS_FIRST:
            try:
                print("🌐 Buscando HTML via requests...")
                html, http_status = fetch_html_requests(case_url)
                print(f"📶 HTTP {http_status} | HTML len={len(html)}")
            except Exception as e:
                print(f"⚠️ requests falhou ({e}). Tentando Playwright...")

        if not html:
            print("🌐 Buscando HTML via Playwright...")
            html = await fetch_html_playwright(case_url)
            print(f"✅ Playwright HTML len={len(html)}")

        mark_success(col, doc_id, html=html)
        print(f"🗃️ Atualizado no MongoDB: status='{STATUS_OK}' (caseHtml gravado)")
        return 0

    except PyMongoError as e:
        msg = f"Erro MongoDB: {e}"
        print(f"❌ {msg}")
        if col is not None and doc_id is not None:
            mark_error(col, doc_id, error_msg=msg)
        return 2

    except Exception as e:
        msg = str(e)
        print(f"❌ Erro: {msg}")
        if col is not None and doc_id is not None:
            mark_error(col, doc_id, error_msg=msg)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    print(f"Exit code: {exit_code}")
