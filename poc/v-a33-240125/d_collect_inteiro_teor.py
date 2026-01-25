#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
d_collect_inteiro_teor.py

Pipeline:
1) Buscar na collection "case_data" o documento mais antigo com status="extracted"
2) Obter caseUrl (URL real da decisão)
3) Playwright headless: clicar em "Inteiro teor" e capturar a URL do popup (JSP)
4) Contornar bloqueios/403 usando a MESMA estratégia do seu coletor:
   - Resolver redirect com requests.Session() usando headers (User-Agent/Accept/Referer)
   - (Opcional) SSL via certifi / STF_SSL_VERIFY=false
5) Fazer download do PDF usando requests com stream=True
6) Atualizar o documento em case_data com URLs e metadados do arquivo

Env vars:
- STF_SSL_VERIFY=true|false (default true)
- STF_PDF_DIR=/caminho/para/salvar/pdfs (default /workspaces/cito/poc/v-a33-240125/data/pdfs)
"""

import asyncio
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import certifi
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
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
CASE_DATA_COLLECTION = "case_data"

STATUS_INPUT = "extracted"
STATUS_OK = "pdf_collected"
STATUS_ERROR = "pdf_error"

# =========================
# Playwright
# =========================
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1920, "height": 1080}

# Mesma lógica do seu coletor: múltiplos seletores (inclui xpath genérico)
SELECTORS = [
    "[mattooltip='Inteiro teor']",
    "mat-icon[mattooltip='Inteiro teor']",
    "//*[@mattooltip='Inteiro teor']",
]

# =========================
# Download settings
# =========================
DOWNLOAD_DIR = Path(os.getenv("STF_PDF_DIR", "/workspaces/cito/poc/v-a33-240125/data/pdfs"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# Helpers
# =========================
def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _requests_verify_opt() -> Any:
    """
    - certifi.where() por padrão
    - False se STF_SSL_VERIFY=false
    """
    ssl_verify = _env_bool("STF_SSL_VERIFY", True)
    if not ssl_verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False
    return certifi.where()


def _safe_filename(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", (s or "").strip())
    return s[:180] if s else "documento"


def _build_requests_session(referer: str) -> requests.Session:
    """
    Replica a estratégia do seu coletor: requests.Session com headers.
    Importante: inclui Referer para reduzir chance de 403.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": referer,
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    })
    return session


# =========================
# Mongo helpers
# =========================
def get_case_data_collection() -> Collection:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[CASE_DATA_COLLECTION]


def fetch_oldest_case_extracted(col: Collection) -> Optional[Dict[str, Any]]:
    return col.find_one({"status": STATUS_INPUT}, sort=[("_id", 1)])


def mark_case_pdf_error(col: Collection, doc_id, *, error_msg: str) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "inteiroTeorError": error_msg,
            "inteiroTeorCollectedAt": datetime.now(timezone.utc),
            "status": STATUS_ERROR,
        }}
    )


def mark_case_pdf_success_with_download(
    col: Collection,
    doc_id,
    *,
    jsp_url: str,
    pdf_final_url: str,
    download_meta: Dict[str, Any],
) -> None:
    col.update_one(
        {"_id": doc_id},
        {"$set": {
            "inteiroTeorJspUrl": jsp_url,
            "inteiroTeorPdfUrl": pdf_final_url,
            "inteiroTeorCollectedAt": datetime.now(timezone.utc),

            "inteiroTeorPdfFinalUrl": pdf_final_url,
            "inteiroTeorPdfFilePath": download_meta.get("filePath", ""),
            "inteiroTeorPdfSizeBytes": int(download_meta.get("sizeBytes") or 0),
            "inteiroTeorPdfSha256": download_meta.get("sha256", ""),
            "inteiroTeorPdfContentType": download_meta.get("contentType", ""),
            "inteiroTeorPdfDownloadedAt": datetime.now(timezone.utc),

            "status": STATUS_OK,
        }}
    )


# =========================
# Core: resolve redirect + download (MESMA abordagem do seu coletor)
# =========================
def resolve_final_url_from_jsp(jsp_url: str, *, referer: str) -> str:
    """
    MESMA solução do seu coletor:
    - requests.Session()
    - allow_redirects=True
    - headers (User-Agent/Accept/Referer)
    Retorna a URL final após redirects.
    """
    session = _build_requests_session(referer)
    resp = session.get(
        jsp_url,
        allow_redirects=True,
        timeout=45,
        verify=_requests_verify_opt(),
    )
    resp.raise_for_status()
    return resp.url


def download_pdf(
    *,
    jsp_url: str,
    referer: str,
    output_dir: Path,
    filename_base: str,
) -> Dict[str, Any]:
    """
    Faz download via requests (stream=True) partindo do JSP, seguindo redirects.
    Contorna o problema usando a mesma estratégia do seu coletor (Session + headers + redirects).
    """
    session = _build_requests_session(referer)

    # Para download, ajusta Accept para PDF
    session.headers.update({
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
    })

    resp = session.get(
        jsp_url,
        allow_redirects=True,
        timeout=60,
        verify=_requests_verify_opt(),
        stream=True,
    )
    resp.raise_for_status()

    final_url = resp.url
    content_type = (resp.headers.get("Content-Type") or "").lower()

    ext = ".pdf" if (".pdf" in final_url.lower() or "pdf" in content_type) else ".bin"
    filename = _safe_filename(filename_base) + ext
    file_path = output_dir / filename

    sha = hashlib.sha256()
    size = 0

    with open(file_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if not chunk:
                continue
            f.write(chunk)
            sha.update(chunk)
            size += len(chunk)

    return {
        "finalUrl": final_url,
        "filePath": str(file_path),
        "sizeBytes": size,
        "sha256": sha.hexdigest(),
        "contentType": content_type,
    }


# =========================
# Playwright: capturar JSP via popup
# =========================
async def capture_jsp_url(case_url: str) -> str:
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
            await page.wait_for_timeout(5000)

            elemento = None
            for sel in SELECTORS:
                try:
                    if sel.startswith("//*"):
                        elemento = await page.wait_for_selector(f"xpath={sel}", timeout=12000)
                    else:
                        # no seu coletor, aqui era query_selector para CSS; wait_for_selector é mais robusto
                        elemento = await page.wait_for_selector(sel, timeout=12000)
                    if elemento:
                        break
                except PlaywrightTimeoutError:
                    continue

            if not elemento:
                raise Exception("Elemento 'Inteiro teor' não encontrado (selectors esgotados).")

            async with page.expect_popup(timeout=20000) as popup_info:
                await elemento.click()

            new_page = await popup_info.value
            await new_page.wait_for_load_state("networkidle", timeout=60000)
            await new_page.wait_for_timeout(2000)

            jsp_url = new_page.url
            await new_page.close()

            if not jsp_url:
                raise Exception("Popup abriu, mas não foi possível obter a URL JSP.")

            return jsp_url

        finally:
            await browser.close()


# =========================
# Main
# =========================
async def main() -> int:
    col: Optional[Collection] = None
    doc_id = None

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
        print("🌐 Iniciando coleta do Inteiro Teor (headless)...")

        if not case_url:
            msg = "Documento não possui 'caseUrl' preenchido."
            print(f"❌ {msg}")
            mark_case_pdf_error(col, doc_id, error_msg=msg)
            return 1

        # 1) Captura JSP via Playwright (igual ao seu coletor)
        jsp_url = await capture_jsp_url(case_url)
        print("✅ URL JSP:", jsp_url)

        # 2) Resolve URL final (opcional, mas útil para log)
        # (o download abaixo já retorna finalUrl)
        try:
            pdf_final_url = resolve_final_url_from_jsp(jsp_url, referer=case_url)
            print("✅ URL final (redirect):", pdf_final_url)
        except Exception as e:
            # Não bloqueia; o download pode ainda funcionar e descobrir a final
            print(f"⚠️ Falha ao resolver redirect antes do download: {e}")
            pdf_final_url = ""

        # 3) Download (stream) - mesma estratégia Session+headers+redirects
        stf_id = (doc.get("stfDecisionId") or "").strip()
        filename_base = f"{stf_id or str(doc_id)}_inteiro_teor"

        print(f"⬇️ Baixando PDF para: {DOWNLOAD_DIR} ...")
        dl_meta = download_pdf(
            jsp_url=jsp_url,
            referer=case_url,
            output_dir=DOWNLOAD_DIR,
            filename_base=filename_base,
        )

        pdf_final_url = dl_meta["finalUrl"] or pdf_final_url

        print("✅ URL PDF final:", pdf_final_url)
        print("✅ Download OK:", dl_meta["filePath"])
        print("📦 sizeBytes:", dl_meta["sizeBytes"])
        print("🔐 sha256:", dl_meta["sha256"])

        # 4) Atualiza Mongo
        mark_case_pdf_success_with_download(
            col,
            doc_id,
            jsp_url=jsp_url,
            pdf_final_url=pdf_final_url,
            download_meta=dl_meta,
        )

        print(f"🗃️ Atualizado no MongoDB: status='{STATUS_OK}'")
        return 0

    except PyMongoError as e:
        msg = f"Erro MongoDB: {e}"
        print(msg)
        if col is not None and doc_id is not None:
            mark_case_pdf_error(col, doc_id, error_msg=msg)
        return 2

    except Exception as e:
        msg = str(e)
        print(f"Erro: {msg}")
        if col is not None and doc_id is not None:
            mark_case_pdf_error(col, doc_id, error_msg=msg)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    print(f"Exit code: {exit_code}")
