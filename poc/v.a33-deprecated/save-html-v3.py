import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlunparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from typing import Dict, Any

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES DA APLICAÇÃO
# Agrupamento de todos os parâmetros configuráveis, URLs e paths no início.
# ==============================================================================

# --- Parâmetros de Busca (Configuráveis pelo Usuário/Execução) ---
# A string de consulta a ser utilizada na busca do STF.
QUERY_STRING: str = "homoafetiva"
# Número de resultados por página.
PAGE_SIZE: int = 30
# Indica se a busca deve ocorrer no inteiro teor ("true" ou "false").
PESQUISA_INTEIRO_TEOR: str = "true"
# Define se o navegador será visível (True - modo headed) ou em background (False - modo headless).
HEADED_MODE: bool = False

# --- Configurações de Paths e Saída ---
# Caminho do diretório de destino para salvar os arquivos HTML extraídos.
OUTPUT_DIR: Path = Path("sd-data/projects/CITO/cito/poc/v01-a33/data/html")

# --- Configurações de URL e Parâmetros Fixos ---
# Componentes de base da URL do STF
URL_SCHEME: str = "https"
URL_NETLOC: str = "jurisprudencia.stf.jus.br"
URL_PATH: str = "/pages/search"

# Parâmetros de filtro fixos que definem o escopo da busca (não mudam entre execuções).
# Nota: "processo_classe_processual_unificada_classe_sigla" é uma lista para ser
# tratada corretamente durante a codificação da URL.
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

# --- Configurações do Playwright (Robusto) ---
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
VIEWPORT_SIZE: Dict[str, int] = {"width": 1280, "height": 800}
LOCALE: str = "pt-BR"

# ==============================================================================
# 2. FUNÇÃO DE CONSTRUÇÃO DA URL
# ==============================================================================

def build_target_url() -> str:
    """
    Constrói a URL de busca final, combinando de forma segura os parâmetros fixos
    e os parâmetros configuráveis definidos. Lida com múltiplos valores por chave
    (como as classes processuais) usando a biblioteca urllib.

    Returns:
        str: A URL completa e formatada para a requisição de busca.
    """
    # Combina os parâmetros fixos e dinâmicos
    dynamic_params = {
        "pesquisa_inteiro_teor": PESQUISA_INTEIRO_TEOR,
        "pageSize": PAGE_SIZE,
        "queryString": QUERY_STRING
    }
    
    all_params = FIXED_QUERY_PARAMS.copy()
    
    # Extrai e remove as classes do dict principal para tratamento especial na serialização
    classes = all_params.pop("processo_classe_processual_unificada_classe_sigla", [])
    
    # Adiciona os parâmetros dinâmicos
    all_params.update(dynamic_params)
    
    # Prepara a lista de tuplas (chave, valor) para urlencode.
    query_list = []
    
    # Trata parâmetros simples
    for key, value in all_params.items():
        query_list.append((key, str(value)))
            
    # Adiciona as classes processuais que requerem repetição da chave na URL
    for class_name in classes:
        query_list.append(("processo_classe_processual_unificada_classe_sigla", class_name))

    # Usa urlencode para formatar a string de consulta
    query_string = urlencode(query_list)
    
    # Monta a URL completa usando urlunparse
    url_tuple = (URL_SCHEME, URL_NETLOC, URL_PATH, "", query_string, "")
    url_alvo = urlunparse(url_tuple)
    
    return url_alvo

# ==============================================================================
# 3. FUNÇÃO DE RASPAGEM (SCRAPER) E SALVAMENTO
# ==============================================================================

def scrape_and_save_html(url: str, output_path: Path):
    """
    Inicia o navegador Playwright (Chromium), navega até a URL alvo,
    aguarda a renderização completa do conteúdo JavaScript e salva o HTML
    da página em um arquivo com timestamp.

    Args:
        url (str): A URL completa a ser raspada.
        output_path (Path): O diretório de destino para salvar o HTML.
    """

    print(f"🔹 Iniciando raspagem do STF na URL:\n{url}")
    inicio = time.time()

    # Cria o diretório de saída, se não existir
    output_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        # 3.1 Configuração do Navegador
        try:
            # Argumentos para aumentar a robustez em ambientes de servidor
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
            browser = pw.chromium.launch(headless=not HEADED_MODE, args=launch_args)
        except PlaywrightError as e:
            print("❌ Falha ao iniciar o navegador Playwright. Verifique a instalação do Playwright/dependências.")
            print(f"Detalhes do erro: {e}")
            return

        # 3.2 Configuração do Contexto de Navegação (Para simular um usuário real)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport=VIEWPORT_SIZE,
            locale=LOCALE,
            extra_http_headers={"accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"},
        )

        # Scripts para evitar detecção de automação (anti-bot)
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        context.add_init_script("window.chrome = { runtime: {} };")
        context.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']})")

        page = context.new_page()

        # 3.3 Navegação e Espera
        try:
            print("🌐 Acessando página e aguardando rede ficar ociosa...")
            # 'networkidle' espera que a atividade de rede diminua significativamente.
            resp = page.goto(url, wait_until="networkidle")
            if resp:
                print(f"📶 Status HTTP da resposta: {resp.status}")
                if resp.status >= 400:
                    print(f"⚠️ Alerta: A requisição retornou o status {resp.status}.")
        except Exception as e:
            print(f"❌ Erro durante a navegação Playwright: {e}")
            browser.close()
            return
            
        # Atraso adicional para garantir a renderização de componentes JS dinâmicos
        print("⏳ Aguardando 3 segundos adicionais para renderização JS...")
        time.sleep(3) 

        # 3.4 Captura e Salvamento
        html = page.content()
        browser.close()

        # Nome do arquivo com timestamp para garantir unicidade
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"stf_html_{timestamp}.html"
        caminho = output_path / nome_arquivo

        # Salva o HTML
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)

        duracao = time.time() - inicio
        print(f"✅ HTML salvo com sucesso em: {caminho}")
        print(f"⏱️ Tempo total: {duracao:.2f} segundos.")

# ==============================================================================
# 4. EXECUÇÃO PRINCIPAL
# Define o ponto de entrada do script.
# ==============================================================================

if __name__ == "__main__":
    # Constrói a URL final usando a função dedicada
    url_alvo = build_target_url()
    
    # Executa a raspagem e salvamento do HTML
    scrape_and_save_html(url_alvo, OUTPUT_DIR)
