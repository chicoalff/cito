import time
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlunparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError
# Substituindo BeautifulSoup por lxml para suportar XPath
from lxml import html as lxml_html
from typing import List, Dict, Any, Tuple

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES DA APLICAÇÃO
# Agrupamento de todos os parâmetros configuráveis, URLs e paths.
# ==============================================================================

# --- Parâmetros de Busca (Configuráveis) ---
QUERY_STRING: str = "homoafetiva"
PAGE_SIZE: int = 10
PESQUISA_INTEIRO_TEOR: str = "true"
HEADED_MODE: bool = False # False para modo headless, True para visível

# --- Configurações de Paths e Saída ---
# URL base para completar links relativos encontrados no HTML
BASE_URL_STF: str = "https://jurisprudencia.stf.jus.br"
# Caminho do diretório de destino para o arquivo JSON.
OUTPUT_JSON_PATH: Path = Path("sd-data/projects/CITO/cito/poc/v01-a33/data/json")
# Nome do arquivo de saída JSON.
OUTPUT_JSON_FILENAME: str = 'jurisprudencia.json'

# --- Configurações de URL e Parâmetros Fixos ---
URL_SCHEME: str = "https"
URL_NETLOC: str = "jurisprudencia.stf.jus.br"
URL_PATH: str = "/pages/search"

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

# --- Configurações do Playwright ---
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
VIEWPORT_SIZE: Dict[str, int] = {"width": 1280, "height": 800}
LOCALE: str = "pt-BR"

# --- Selectors XPath para Extração de Metadados da Decisão (relativos ao container) ---
# Mapeia as chaves do dicionário de saída (JSON) para seus respectivos XPaths.
# Estes XPaths são relativos ao elemento 'div.result-container' (o bloco de cada decisão).
DECISION_METADATA_SELECTORS: Dict[str, str] = {
    "orgao_colegiado": "./div[2]/h4[1]/span",
    "relator": "./div[2]/h4[2]/span",
    "dt_julgamento": "./div[2]/span/h4[1]/span",
    "dt_publicacao": "./div[2]/span/h4[2]/span"
}


# ==============================================================================
# 2. FUNÇÕES AUXILIARES DE PERSISTÊNCIA E PARSING
# ==============================================================================

def build_target_url() -> str:
    """
    Constrói a URL de busca final combinando parâmetros fixos e configuráveis.
    """
    dynamic_params = {
        "pesquisa_inteiro_teor": PESQUISA_INTEIRO_TEOR,
        "pageSize": PAGE_SIZE,
        "queryString": QUERY_STRING
    }
    
    all_params = FIXED_QUERY_PARAMS.copy()
    classes = all_params.pop("processo_classe_processual_unificada_classe_sigla", [])
    all_params.update(dynamic_params)
    
    query_list = []
    for key, value in all_params.items():
        query_list.append((key, str(value)))
            
    for class_name in classes:
        query_list.append(("processo_classe_processual_unificada_classe_sigla", class_name))

    query_string = urlencode(query_list)
    url_tuple = (URL_SCHEME, URL_NETLOC, URL_PATH, "", query_string, "")
    return urlunparse(url_tuple)

def _get_xpath_text_safe(element: lxml_html.HtmlElement, xpath_selector: str, default: str = "N/A") -> str:
    """
    Função auxiliar para extrair o texto de um elemento usando XPath,
    retornando um valor padrão em caso de falha.
    """
    try:
        # Usa o método xpath nativo do lxml
        el_list = element.xpath(xpath_selector)
        if el_list and isinstance(el_list[0].text, str):
            return el_list[0].text.strip()
    except Exception:
        pass # Retorna o valor padrão em caso de erro na extração
    return default

def extract_decision_data(html_content: str, base_url: str, next_id_start: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Analisa o conteúdo HTML da busca e extrai as decisões para o formato JSON desejado.
    Utiliza lxml e XPaths relativos para os metadados.

    Args:
        html_content (str): O conteúdo HTML renderizado.
        base_url (str): A URL base para construir links completos.
        next_id_start (int): O ID sequencial a partir do qual as novas decisões devem começar.

    Returns:
        tuple: Uma lista de dicionários de decisões recém-extraídas e o próximo ID sequencial.
    """
    # 1. Parsing com lxml.html
    tree = lxml_html.fromstring(html_content)
    
    resultados = []
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_id = next_id_start
    
    # Encontra todos os contêineres de resultados usando XPath
    containers = tree.xpath("//div[contains(@class, 'result-container')]")
    
    print(f"Número de containers de decisão encontrados: {len(containers)}")

    for container in containers:
        # 1. Extração de URL e ID Único (link principal)
        # XPath para o link: ./a[contains(@class, 'mat-tooltip-trigger')]
        link_element = container.xpath("./a[contains(@class, 'mat-tooltip-trigger')]")
        
        # O atributo 'href' é obtido usando o método .get() do elemento lxml
        url_parcial = link_element[0].get('href', "") if link_element else ""
        url_completa = f"{base_url}{url_parcial}" if url_parcial else "N/A"
        
        url_parts = url_parcial.split('/')
        id_decisao_stf = url_parts[-2] if len(url_parts) > 2 else "N/A"

        # 2. Extração do Título (decisao)
        # XPath para o título: .//h4[contains(@class, 'ng-star-inserted')]
        titulo_el = container.xpath(".//h4[contains(@class, 'ng-star-inserted')]")
        titulo = titulo_el[0].text.strip() if titulo_el and titulo_el[0].text else "N/A"

        # 3. Extração da Classe (Primeira palavra do título)
        classe = titulo.split()[0] if titulo != "N/A" else "N/A"

        # Monta o dicionário base
        decisao = {
            "id": current_id,
            "id_stf": id_decisao_stf,
            "decisao": titulo,
            "classe": classe,
            "url_decisao": url_completa,
            "status": "novo",  # Status inicial fixo
            "criado": current_time_str,
            "atualizado": current_time_str,
        }
        
        # 4. Extração de Metadados usando o Mapeamento de Seletores XPath
        # As chaves 'orgao_colegiado', 'relator', 'dt_julgamento', 'dt_publicacao'
        # são preenchidas usando os XPaths relativos definidos em DECISION_METADATA_SELECTORS.
        for key, selector in DECISION_METADATA_SELECTORS.items():
            decisao[key] = _get_xpath_text_safe(container, selector)

        resultados.append(decisao)
        current_id += 1

    return resultados, current_id

def load_existing_data(filepath: Path) -> Tuple[List[Dict[str, Any]], int]:
    """
    Carrega os dados existentes do arquivo JSON e determina o próximo ID sequencial.

    Args:
        filepath (Path): Caminho completo para o arquivo JSON.

    Returns:
        tuple: Uma lista de dicionários de dados existentes e o próximo ID a ser usado.
    """
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    return [], 1
                
                # O próximo ID é o máximo ID encontrado + 1
                max_id = max(item.get("id", 0) for item in data)
                return data, max_id + 1
        except json.JSONDecodeError:
            print(f"⚠️ Aviso: Arquivo JSON '{filepath.name}' corrompido ou vazio. Iniciando do zero.")
            return [], 1
    return [], 1

def save_json(filepath: Path, data: List[Dict[str, Any]]):
    """
    Salva a lista completa de decisões no arquivo JSON de saída.

    Args:
        filepath (Path): Caminho completo para o arquivo JSON.
        data (list): A lista de dicionários contendo todas as decisões.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Dados salvos com sucesso em: {filepath.name} (Total: {len(data)} decisões).")
    except Exception as e:
        print(f"❌ ERRO ao salvar o arquivo JSON: {e}")

# ==============================================================================
# 3. FUNÇÃO DE RASPAGEM (SCRAPER)
# ==============================================================================

def scrape_html(url: str) -> str:
    """
    Inicia o navegador Playwright, navega e retorna o conteúdo HTML renderizado.
    """
    html_content = ""
    print(f"🔹 Iniciando raspagem do STF na URL...")
    inicio = time.time()

    with sync_playwright() as pw:
        # 3.1 Configuração do Navegador
        try:
            launch_args = [
                "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
            ]
            browser = pw.chromium.launch(headless=not HEADED_MODE, args=launch_args)
        except PlaywrightError as e:
            print(f"❌ Falha ao iniciar o navegador Playwright: {e}")
            return html_content

        # 3.2 Configuração do Contexto de Navegação (Anti-bot measures)
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

        # 3.3 Navegação e Espera
        try:
            print("🌐 Acessando página e aguardando rede ficar ociosa...")
            resp = page.goto(url, wait_until="networkidle")
            if resp:
                print(f"📶 Status HTTP da resposta: {resp.status}")
                if resp.status >= 400:
                    print(f"⚠️ Alerta: A requisição retornou o status {resp.status}.")
            
            print("⏳ Aguardando 3 segundos adicionais para renderização JS...")
            time.sleep(3) 

            # 3.4 Captura
            html_content = page.content()

        except Exception as e:
            print(f"❌ Erro durante a navegação Playwright: {e}")
        finally:
            browser.close()

    duracao = time.time() - inicio
    if html_content:
        print(f"✅ Raspagem concluída. Tempo total: {duracao:.2f} segundos.")
    return html_content

# ==============================================================================
# 4. EXECUÇÃO PRINCIPAL
# ==============================================================================

def main():
    """
    Função principal que orquestra o processo completo: 
    1. Constrói a URL.
    2. Raspa o HTML.
    3. Carrega os dados JSON existentes e determina o próximo ID.
    4. Extrai os novos dados do HTML e os mescla com os dados existentes.
    5. Salva a lista consolidada no arquivo JSON.
    """
    
    # 1. Construir URL
    url_alvo = build_target_url()

    # 2. Raspagem do HTML
    html_content = scrape_html(url_alvo)
    
    if not html_content:
        print("❌ Não foi possível obter o conteúdo HTML. Abortando extração.")
        return

    # 3. Carregar dados existentes
    output_filepath = OUTPUT_JSON_PATH / OUTPUT_JSON_FILENAME
    OUTPUT_JSON_PATH.mkdir(parents=True, exist_ok=True)
    
    existing_data, next_id = load_existing_data(output_filepath)
    print(f"Dados existentes carregados: {len(existing_data)} decisões. Próximo ID a ser usado: {next_id}.")

    # 4. Extrair e Mesclar novos dados
    print(f"\nExtraindo novas decisões...")
    new_data, next_id_after_extraction = extract_decision_data(html_content, BASE_URL_STF, next_id)
    
    if new_data:
        # Mescla os dados: existentes + novos
        all_data = existing_data + new_data
        print(f"Total de {len(new_data)} novas decisões adicionadas.")
        
        # 5. Salvar o arquivo JSON consolidado
        save_json(output_filepath, all_data)
    else:
        print("⚠️ Nenhuma nova decisão encontrada ou extraída nesta página. Arquivo JSON não alterado.")

if __name__ == "__main__":
    main()
