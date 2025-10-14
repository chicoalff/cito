import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# --- Parâmetros Configuráveis ---
QUERY_STRING = "direito"
PAGE_SIZE = "10"
PESQUISA_INTEIRO_TEOR = "true"

# --- URL Base e Parâmetros Fixos ---
BASE_URL = "https://jurisprudencia.stf.jus.br/pages/search"
FIXED_PARAMS = (
    "base=acordaos&"
    "sinonimo=true&plural=true&radicais=false&buscaExata=true&"
    "processo_classe_processual_unificada_classe_sigla=ADC&"
    "processo_classe_processual_unificada_classe_sigla=ADI&"
    "processo_classe_processual_unificada_classe_sigla=ADO&"
    "processo_classe_processual_unificada_classe_sigla=ADPF&"
    "page=1&sort=_score&sortBy=desc")


def salvar_html_completo(url: str, headed=False):
    """
    Acessa a URL usando Playwright, espera o carregamento total,
    captura o HTML renderizado e salva em disco com timestamp.
    """

    print(f"🔹 Iniciando scraping do STF: {url}")
    inicio = time.time()

    with sync_playwright() as pw:
        try:
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
            browser = pw.chromium.launch(headless=not headed, args=launch_args)
        except PlaywrightError as e:
            print("❌ Falha ao iniciar o navegador:", str(e))
            if headed:
                print("Use o modo headless ou instale o X server.")
            return

        # Cria contexto de navegação
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="pt-BR",
            extra_http_headers={"accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"},
        )

        # Oculta sinais de automação
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        context.add_init_script("window.chrome = { runtime: {} };")
        context.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']})")

        page = context.new_page()

        print("🌐 Acessando página...")
        resp = page.goto(url, wait_until="networkidle")
        if resp:
            print(f"📶 Status HTTP: {resp.status}")

        print("⏳ Aguardando renderização completa...")
        time.sleep(3)

        # Captura o HTML completo
        html = page.content()
        browser.close()

    # Cria diretório de saída
    out_dir = Path("sd-data/projects/CITO/cito/poc/v01-a33/data/html")
    out_dir.mkdir(exist_ok=True)

    # Nome do arquivo com data e hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"stf_html_{timestamp}.html"
    caminho = out_dir / nome_arquivo

    # Salva HTML
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)

    duracao = time.time() - inicio
    print(f"✅ HTML salvo com sucesso em: {caminho}")
    print(f"⏱️ Tempo total: {duracao:.2f}s")

if __name__ == "__main__":
    # Constrói a URL final com os parâmetros configuráveis
    url_alvo = (
        f"{BASE_URL}?"
        f"pesquisa_inteiro_teor={PESQUISA_INTEIRO_TEOR}&"
        f"{FIXED_PARAMS}&"
        f"pageSize={PAGE_SIZE}&"
        f"queryString={QUERY_STRING}")
    salvar_html_completo(url_alvo)
