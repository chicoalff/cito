from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlencode, urlunparse

from playwright.sync_api import sync_playwright, Error as PlaywrightError
from pymongo import MongoClient
from pymongo.errors import PyMongoError, DocumentTooLarge

from a_load_configs import load_configs


# =========================
# Mongo helpers
# =========================

def get_mongo_collection() -> Any:
    """
    Ajuste MONGO_URI, DB_NAME e COLLECTION_NAME para o seu ambiente.
    Evite hardcode de senha.
    """
    # Exemplo de URI (substitua host/porta/replicaSet/atlas conforme seu caso):
    # mongodb://cito:fyu9WxkHakGKHeoq@localhost:27017/?authSource=admin
    MONGO_URI = "mongodb://cito:fyu9WxkHakGKHeoq@localhost:27017/?authSource=admin"
    DB_NAME = "cito"
    COLLECTION_NAME = "stf_html_raw"

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


def insert_extraction_doc(
    *,
    collection: Any,
    extraction_timestamp: datetime,
    query_string: str,
    page_size: int,
    inteiro_teor: bool,
    html_raw: str,
) -> None:
    doc = {
        "extractionTimestamp": extraction_timestamp,  # Date no Mongo
        "queryString": query_string,
        "pageSize": str(page_size),                   # conforme seu schema
        "inteiroTeor": bool(inteiro_teor),
        "htmlRaw": html_raw,
    }

    try:
        result = collection.insert_one(doc)
        # _id é gerado automaticamente
        print(f"✅ Inserido no MongoDB. _id={result.inserted_id}")
    except DocumentTooLarge:
        print("❌ Documento excede 16MB (limite do MongoDB). Considere GridFS ou outra estratégia.")
        raise
    except PyMongoError as e:
        print(f"❌ Erro ao inserir no MongoDB: {e}")
        raise


# ==============================================================================
# 1) DEFAULTS (vindos do Google Sheets via load_configs())
# ==============================================================================

_HARD_DEFAULT_QUERY_STRING: str = "homoafetiva"
_HARD_DEFAULT_PAGE_SIZE: int = 30
_HARD_DEFAULT_INTEIRO_TEOR_BOOL: bool = True
_HARD_DEFAULT_HEADED_MODE: bool = False
_HARD_DEFAULT_OUTPUT_DIR: Path = Path("poc/v-a33-240125/data/html")
_HARD_DEFAULT_URL_SCHEME: str = "https"
_HARD_DEFAULT_URL_NETLOC: str = "jurisprudencia.stf.jus.br"
_HARD_DEFAULT_URL_PATH: str = "/pages/search"


def _bool_to_str(value: bool) -> str:
    return "true" if value else "false"


def _safe_int(v: Any, default: int) -> int:
    try:
        if v is None:
            return default
        s = str(v).strip()
        if s == "":
            return default
        return int(float(s.replace(",", ".")))
    except Exception:
        return default


def load_defaults_from_sheet() -> Dict[str, Any]:
    cfg = load_configs()

    default_query_string = cfg.query_string or _HARD_DEFAULT_QUERY_STRING
    default_page_size = _safe_int(cfg.page_size, _HARD_DEFAULT_PAGE_SIZE)

    default_pesquisa_inteiro_teor = _bool_to_str(
        cfg.inteiro_teor if cfg.inteiro_teor is not None else _HARD_DEFAULT_INTEIRO_TEOR_BOOL
    )
    default_headed_mode = cfg.headed_mode if cfg.headed_mode is not None else _HARD_DEFAULT_HEADED_MODE

    default_output_dir = Path(cfg.output_dir) if cfg.output_dir else _HARD_DEFAULT_OUTPUT_DIR

    default_url_scheme = cfg.url_scheme or _HARD_DEFAULT_URL_SCHEME
    default_url_netloc = cfg.url_netloc or _HARD_DEFAULT_URL_NETLOC
    default_url_path = cfg.url_path or _HARD_DEFAULT_URL_PATH

    return {
        "DEFAULT_QUERY_STRING": default_query_string,
        "DEFAULT_PAGE_SIZE": default_page_size,
        "DEFAULT_PESQUISA_INTEIRO_TEOR": default_pesquisa_inteiro_teor,
        "DEFAULT_HEADED_MODE": default_headed_mode,
        "DEFAULT_OUTPUT_DIR": default_output_dir,
        "DEFAULT_URL_SCHEME": default_url_scheme,
        "DEFAULT_URL_NETLOC": default_url_netloc,
        "DEFAULT_URL_PATH": default_url_path,
    }


_DEFAULTS = load_defaults_from_sheet()

DEFAULT_QUERY_STRING: str = _DEFAULTS["DEFAULT_QUERY_STRING"]
DEFAULT_PAGE_SIZE: int = _DEFAULTS["DEFAULT_PAGE_SIZE"]
DEFAULT_PESQUISA_INTEIRO_TEOR: str = _DEFAULTS["DEFAULT_PESQUISA_INTEIRO_TEOR"]
DEFAULT_HEADED_MODE: bool = _DEFAULTS["DEFAULT_HEADED_MODE"]
DEFAULT_OUTPUT_DIR: Path = _DEFAULTS["DEFAULT_OUTPUT_DIR"]
DEFAULT_URL_SCHEME: str = _DEFAULTS["DEFAULT_URL_SCHEME"]
DEFAULT_URL_NETLOC: str = _DEFAULTS["DEFAULT_URL_NETLOC"]
DEFAULT_URL_PATH: str = _DEFAULTS["DEFAULT_URL_PATH"]


FIXED_QUERY_PARAMS: Dict[str, Any] = {
    "base": "acordaos",
    "sinonimo": "true",
    "plural": "true",
    "radicais": "false",
    "buscaExata": "true",
    "processo_classe_processual_unificada_classe_sigla": ["ADC", "ADI", "ADO", "ADPF"],
    "page": 1,
    "sort": "_score",
    "sortBy": "desc",
}

USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
VIEWPORT_SIZE = {"width": 1280, "height": 800}
LOCALE: str = "pt-BR"


def build_target_url(
    *,
    query_string: str,
    page_size: int,
    pesquisa_inteiro_teor: str,
    url_scheme: str,
    url_netloc: str,
    url_path: str,
) -> str:
    dynamic_params = {
        "pesquisa_inteiro_teor": pesquisa_inteiro_teor,
        "pageSize": page_size,
        "queryString": query_string,
    }

    all_params = FIXED_QUERY_PARAMS.copy()
    classes = all_params.pop("processo_classe_processual_unificada_classe_sigla", [])
    all_params.update(dynamic_params)

    query_list = [(k, str(v)) for k, v in all_params.items()]
    for class_name in classes:
        query_list.append(("processo_classe_processual_unificada_classe_sigla", class_name))

    query = urlencode(query_list)
    return urlunparse((url_scheme, url_netloc, url_path, "", query, ""))


def scrape_save_and_insert_html(
    *,
    url: str,
    output_path: Path,
    headed_mode: bool,
    query_string: str,
    page_size: int,
    inteiro_teor: bool,
) -> None:
    print(f"🔹 Iniciando raspagem do STF na URL:\n{url}")
    inicio = time.time()

    output_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        try:
            launch_args = ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            browser = pw.chromium.launch(headless=not headed_mode, args=launch_args)
        except PlaywrightError as e:
            print("❌ Falha ao iniciar o Playwright.")
            print(f"Detalhes do erro: {e}")
            return

        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport=VIEWPORT_SIZE,
            locale=LOCALE,
            extra_http_headers={"accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"},
        )

        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        context.add_init_script("window.chrome = { runtime: {} };")
        context.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']})")

        page = context.new_page()

        try:
            print("🌐 Acessando página e aguardando rede ficar ociosa...")
            resp = page.goto(url, wait_until="networkidle")
            if resp:
                print(f"📶 Status HTTP da resposta: {resp.status}")
                if resp.status >= 400:
                    print(f"⚠️ Alerta: A requisição retornou o status {resp.status}.")
        except Exception as e:
            print(f"❌ Erro durante navegação Playwright: {e}")
            browser.close()
            return

        print("⏳ Aguardando 3 segundos adicionais para renderização JS...")
        time.sleep(3)

        html = page.content()
        browser.close()

    # Salva em arquivo (como você já faz)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"stf_html_{timestamp_str}.html"
    caminho = output_path / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)

    # Insere no Mongo
    collection = get_mongo_collection()
    extraction_ts = datetime.now(timezone.utc)

    insert_extraction_doc(
        collection=collection,
        extraction_timestamp=extraction_ts,
        query_string=query_string,
        page_size=page_size,
        inteiro_teor=inteiro_teor,
        html_raw=html,
    )

    duracao = time.time() - inicio
    print(f"✅ HTML salvo em: {caminho}")
    print(f"⏱️ Tempo total: {duracao:.2f} segundos.")


def resolve_runtime_vars() -> Dict[str, Any]:
    return {
        "QUERY_STRING": DEFAULT_QUERY_STRING,
        "PAGE_SIZE": DEFAULT_PAGE_SIZE,
        "PESQUISA_INTEIRO_TEOR": DEFAULT_PESQUISA_INTEIRO_TEOR,  # "true"/"false"
        "HEADED_MODE": DEFAULT_HEADED_MODE,
        "OUTPUT_DIR": DEFAULT_OUTPUT_DIR,
        "URL_SCHEME": DEFAULT_URL_SCHEME,
        "URL_NETLOC": DEFAULT_URL_NETLOC,
        "URL_PATH": DEFAULT_URL_PATH,
    }


def main() -> None:
    v = resolve_runtime_vars()

    url_alvo = build_target_url(
        query_string=v["QUERY_STRING"],
        page_size=v["PAGE_SIZE"],
        pesquisa_inteiro_teor=v["PESQUISA_INTEIRO_TEOR"],
        url_scheme=v["URL_SCHEME"],
        url_netloc=v["URL_NETLOC"],
        url_path=v["URL_PATH"],
    )

    inteiro_teor_bool = (str(v["PESQUISA_INTEIRO_TEOR"]).lower() == "true")

    scrape_save_and_insert_html(
        url=url_alvo,
        output_path=v["OUTPUT_DIR"],
        headed_mode=v["HEADED_MODE"],
        query_string=v["QUERY_STRING"],
        page_size=v["PAGE_SIZE"],
        inteiro_teor=inteiro_teor_bool,
    )


if __name__ == "__main__":
    main()
