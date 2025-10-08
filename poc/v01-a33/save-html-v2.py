import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Error as PlaywrightError


# --- Parâmetros Configuráveis ---
QUERY_STRING = "ambiental"  # Termo de busca para a jurisprudência.
PAGE_SIZE = "100"  # Quantidade de resultados por página.
PESQUISA_INTEIRO_TEOR = "true"  # Define se a busca deve ser realizada no inteiro teor dos documentos.

# --- URL Base e Parâmetros Fixos ---
# URL base para a pesquisa de jurisprudência do STF.
BASE_URL = "https://jurisprudencia.stf.jus.br/pages/search" 
# Parâmetros fixos da URL que definem o escopo da busca (base de acórdãos, classes processuais, etc.).
FIXED_PARAMS = (
    "base=acordaos&"
    "sinonimo=true&plural=true&radicais=false&buscaExata=true&"
    "processo_classe_processual_unificada_classe_sigla=ADC&"
    "processo_classe_processual_unificada_classe_sigla=ADI&"
    "processo_classe_processual_unificada_classe_sigla=ADO&"
    "processo_classe_processual_unificada_classe_sigla=ADPF&"  # Filtra por classes de ações de controle de constitucionalidade.
    "page=1&sort=_score&sortBy=desc") # Define a paginação inicial e a ordenação por relevância.


def salvar_html_completo(url: str, headed=False):
    """
    Acessa a URL usando Playwright, espera o carregamento total,
    captura o HTML renderizado e salva em disco com timestamp.
    """

    # Imprime a URL alvo e marca o tempo de início para medir a duração.
    print(f"🔹 Iniciando scraping do STF: {url}")
    inicio = time.time()

    # Utiliza o gerenciador de contexto do Playwright para garantir que os recursos sejam liberados.
    with sync_playwright() as pw:
        try:
            # Argumentos para execução em ambientes de contêiner (ex: Docker, Codespaces).
            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
            # Inicia uma instância do navegador Chromium. 'headless=not headed' permite rodar com ou sem interface gráfica.
            browser = pw.chromium.launch(headless=not headed, args=launch_args)
        except PlaywrightError as e:
            # Tratamento de erro caso o navegador não possa ser iniciado.
            print("❌ Falha ao iniciar o navegador:", str(e))
            if headed:
                print("Use o modo headless ou instale o X server.")
            return

        # Cria um novo contexto de navegador com configurações para simular um usuário real.
        # Isso ajuda a evitar bloqueios por mecanismos anti-automação.
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

        # Adiciona scripts para ocultar sinais de que um robô está sendo usado.
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        context.add_init_script("window.chrome = { runtime: {} };")
        context.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']})")

        # Abre uma nova página no contexto configurado.
        page = context.new_page()

        # Navega para a URL especificada e aguarda o carregamento completo da rede.
        print("🌐 Acessando página...")
        resp = page.goto(url, wait_until="networkidle")
        if resp:
            print(f"📶 Status HTTP: {resp.status}")

        # Pausa adicional para garantir que scripts JavaScript dinâmicos terminem de renderizar o conteúdo.
        print("⏳ Aguardando renderização completa...")
        time.sleep(3)

        # Captura o conteúdo HTML da página após a renderização.
        html = page.content()
        # Fecha o navegador, liberando os recursos.
        browser.close()

    # Define o diretório onde os arquivos HTML serão salvos.
    out_dir = Path("poc/v01-a33/data/html")
    # Cria o diretório se ele não existir, sem gerar erro caso já exista.
    out_dir.mkdir(exist_ok=True)

    # Gera um timestamp para criar um nome de arquivo único.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"stf_html_{timestamp}.html"
    caminho = out_dir / nome_arquivo

    # Abre o arquivo em modo de escrita com codificação UTF-8 e salva o conteúdo HTML.
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)

    # Calcula e exibe o tempo total da operação.
    duracao = time.time() - inicio
    print(f"✅ HTML salvo com sucesso em: {caminho}")
    print(f"⏱️ Tempo total: {duracao:.2f}s")

# Bloco principal que é executado quando o script é chamado diretamente.
if __name__ == "__main__":
    # Monta a URL final da pesquisa combinando a URL base com os parâmetros fixos e configuráveis.
    url_alvo = (
        f"{BASE_URL}?"
        f"pesquisa_inteiro_teor={PESQUISA_INTEIRO_TEOR}&"
        f"{FIXED_PARAMS}&"
        f"pageSize={PAGE_SIZE}&"
        f"queryString={QUERY_STRING}")
    
    # Chama a função principal para iniciar o processo de scraping e salvamento do HTML.
    salvar_html_completo(url_alvo)
