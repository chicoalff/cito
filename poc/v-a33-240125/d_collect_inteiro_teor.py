#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor de URL "Inteiro Teor" (PDF) a partir do caseUrl salvo no MongoDB (case_data)

Fluxo:
1) Buscar na collection "case_data" o documento mais antigo com status="extracted"
2) Obter o campo caseUrl (URL REAL da decisão)
3) Abrir no Playwright (headless), localizar e clicar no botão "Inteiro teor"
4) Capturar a URL do popup (JSP) e resolver redirects até a URL final (PDF)
5) Atualizar o documento em case_data com:
   - inteiroTeorPdfUrl
   - inteiroTeorJspUrl
   - inteiroTeorCollectedAt (UTC)
   - status => "pdf_collected"
   (ou "pdf_error" em caso de falha, com inteiroTeorError)

Requisitos:
pip install playwright pymongo requests
playwright install
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


# =========================
# Mongo (fixo conforme seu projeto)
# =========================
MONGO_USER = "cito"
MONGO_PASS = "fyu9WxkHakGKHeoq"
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gb8bzlp.mongodb.net/?appName=Cluster0"
DB_NAME = "cito-v-a33-240125"
CASE_DATA_COLLECTION = "case_data"

STATUS_INPUT = "extracted"
STATUS_OK = "pdf_collected"
STATUS_ERROR = "pdf_error"


# =========================
# Playwright settings
# =========================
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1920, "height": 1080}

# Seletor principal (preferir atributo em vez de XPath absoluto)
SELECTORS = [
    "[mattooltip='Inteiro teor']",
    "mat-icon[mattooltip='Inteiro teor']",
    "//*[@mattooltip='Inteiro teor']",  # xpath genérico
]


# =========================
# Mongo helpers
# =========================
def get_case_data_collection() -> Collection:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[CASE_DATA_COLLECTION]


def fetch_oldest_case_extracted(col: Collection) -> Optional[Dict[str, Any]]:
    # mais antigo por _id asc
    return col.find_one({"status": STATUS_INPUT}, sort=[("_id", 1)])


def mark_case_pdf_success(
    col: Collection,
    doc_id,
    *,
    pdf_url: str,
    jsp_url: str,
) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "inteiroTeorPdfUrl": pdf_url,
            "inteiroTeorJspUrl": jsp_url,
            "inteiroTeorCollectedAt": datetime.now(timezone.utc),
            "status": STATUS_OK,
        }}
    )


def mark_case_pdf_error(
    col: Collection,
    doc_id,
    *,
    error_msg: str,
) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "inteiroTeorError": error_msg,
            "inteiroTeorCollectedAt": datetime.now(timezone.utc),
            "status": STATUS_ERROR,
        }}
    )


# =========================
# Network helper (redirect)
# =========================
def resolve_redirect_to_final_url(jsp_url: str) -> str:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    resp = session.get(jsp_url, allow_redirects=True, timeout=45)
    return resp.url


# =========================
# Playwright flow
# =========================
async def collect_pdf_from_case_url(case_url: str) -> Tuple[str, str]:
    """
    Retorna (jsp_url, pdf_url).
    Lança Exception em caso de falha.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )

        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT,
            extra_http_headers={"accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"},
        )
        page = await context.new_page()

        try:
            await page.goto(case_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(4000)

            elemento = None
            used_selector = None

            # tenta localizar com seletor CSS primeiro; se for xpath genérico, prefixa
            for sel in SELECTORS:
                try:
                    if sel.startswith("//*"):
                        elemento = await page.wait_for_selector(f"xpath={sel}", timeout=12000)
                    else:
                        # wait_for_selector é mais robusto que query_selector aqui
                        elemento = await page.wait_for_selector(sel, timeout=12000)
                    if elemento:
                        used_selector = sel
                        break
                except PlaywrightTimeoutError:
                    continue

            if not elemento:
                raise Exception("Elemento 'Inteiro teor' não encontrado (selectors esgotados).")

            # clique e captura do popup
            async with page.expect_popup(timeout=20000) as popup_info:
                await elemento.click()

            new_page = await popup_info.value
            await new_page.wait_for_load_state("networkidle", timeout=60000)
            await new_page.wait_for_timeout(1500)

            jsp_url = new_page.url
            await new_page.close()

            if not jsp_url:
                raise Exception("Popup abriu, mas não foi possível obter a URL JSP.")

            # resolve redirect para URL final
            pdf_url = resolve_redirect_to_final_url(jsp_url)
            if not pdf_url:
                raise Exception("Falha ao resolver redirecionamento para URL final.")

            # validação leve
            if ".pdf" not in pdf_url.lower():
                # não bloqueia: alguns endpoints podem servir PDF sem extensão
                pass

            return jsp_url, pdf_url

        finally:
            await browser.close()


# =========================
# Main
# =========================
async def main() -> int:
    try:
        col = get_case_data_collection()
        doc = fetch_oldest_case_extracted(col)

        if not doc:
            print(f"Nenhum documento em {DB_NAME}.{CASE_DATA_COLLECTION} com status='{STATUS_INPUT}'.")
            return 0

        doc_id = doc["_id"]
        case_url = (doc.get("caseUrl") or "").strip()

        print(f"Mongo target: db={DB_NAME} collection={CASE_DATA_COLLECTION}")
        print(f"Doc selecionado: _id={doc_id} status={doc.get('status')}")
        print(f"caseUrl: {case_url}")

        if not case_url:
            msg = "Documento não possui 'caseUrl' preenchido."
            print(f"❌ {msg}")
            mark_case_pdf_error(col, doc_id, error_msg=msg)
            return 1

        print("🌐 Iniciando coleta do Inteiro Teor (headless)...")
        jsp_url, pdf_url = await collect_pdf_from_case_url(case_url)

        print("✅ URL JSP:", jsp_url)
        print("✅ URL PDF:", pdf_url)

        mark_case_pdf_success(col, doc_id, pdf_url=pdf_url, jsp_url=jsp_url)
        print(f"🗃️ Atualizado no MongoDB: status='{STATUS_OK}'")
        return 0

    except PyMongoError as e:
        print(f"Erro MongoDB: {e}")
        return 2
    except Exception as e:
        # se já tivermos doc_id e col, marca erro
        try:
            col  # type: ignore
            doc_id  # type: ignore
            mark_case_pdf_error(col, doc_id, error_msg=str(e))  # type: ignore
        except Exception:
            pass
        print(f"Erro: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
