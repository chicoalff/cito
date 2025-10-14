import json
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Any

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES
# Define caminhos e URLs fixas usadas pela aplicação, agrupando todos os
# parâmetros de configuração no início do script.
# ==============================================================================

# URL base para completar links relativos encontrados no HTML
BASE_URL_STF: str = "https://jurisprudencia.stf.jus.br"

# Caminho do diretório de entrada contendo os arquivos HTML a serem processados
INPUT_HTML_PATH: Path = Path('sd-data/projects/CITO/cito/poc/v01-a33/data/html')

# Caminho do subdiretório para onde os arquivos HTML processados serão movidos
PROCESSED_HTML_PATH: Path = INPUT_HTML_PATH / 'processed'

# Caminho do diretório de saída para o arquivo JSON
OUTPUT_JSON_PATH: Path = Path('sd-data/projects/CITO/cito/poc/v01-a33/data/json')

# Nome do arquivo de saída JSON
OUTPUT_JSON_FILENAME: str = 'jurisprudencia.json'

# ==============================================================================
# 2. FUNÇÃO DE EXTRAÇÃO DE DADOS
# ==============================================================================

def _get_text_safe(element: BeautifulSoup, selector: str, default: str = "N/A") -> str:
    """
    Função auxiliar para extrair o texto de um elemento usando um seletor CSS,
    retornando um valor padrão ("N/A") em caso de falha ou elemento não encontrado.
    
    Args:
        element (BeautifulSoup): O elemento base para a busca (ex: o container da decisão).
        selector (str): O seletor CSS a ser aplicado.
        default (str): O valor de retorno se o elemento não for encontrado.

    Returns:
        str: O texto extraído e limpo, ou o valor padrão.
    """
    el = element.select_one(selector)
    return el.text.strip() if el else default

def extrair_dados_stf(html_content: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Analisa o conteúdo HTML de uma página de jurisprudência do STF.
    Utiliza Beautiful Soup e seletores CSS para extração robusta dos dados
    estruturados de cada decisão.

    Args:
        html_content (str): O conteúdo HTML da página.
        base_url (str): A URL base para construir links completos.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma decisão.
    """
    # Inicializa o parser Beautiful Soup com o parser 'lxml' para velocidade
    soup = BeautifulSoup(html_content, "lxml")
    resultados = []
    
    # Encontra todos os contêineres de resultados de decisão. Este é o ponto
    # de partida para todas as extrações relativas.
    containers = soup.find_all("div", class_="result-container")
    
    # Itera sobre cada contêiner para extrair os dados
    for i, container in enumerate(containers, start=1):
        
        # 1. Extração de URL e ID Único (link principal)
        link_element = container.find("a", class_="mat-tooltip-trigger")
        url_parcial = link_element.get('href', "") if link_element else ""
        url_completa = f"{base_url}{url_parcial}" if url_parcial else "N/A"
        
        # Extrai o ID da decisão a partir do caminho da URL (ex: "ID" de /jurisprudencia/ID/nome)
        url_parts = url_parcial.split('/')
        id_decisao_stf = url_parts[-2] if len(url_parts) > 2 else "N/A"

        # 2. Extração do Título da Decisão (h4 principal)
        titulo_element = container.find("h4", class_="ng-star-inserted")
        titulo = titulo_element.text.strip() if titulo_element else "N/A"

        # 3. Extração dos Metadados (Órgão, Relator, Datas)
        # Utilizamos seletores CSS relativos ao 'container', que são mais
        # estáveis do que o XPath absoluto.
        
        # Órgão Colegiado (h4:nth-child(1) dentro do div:nth-child(2))
        orgao_colegiado = _get_text_safe(container, "div:nth-child(2) > h4:nth-child(1) > span")

        # Relator (h4:nth-child(2) dentro do div:nth-child(2))
        relator = _get_text_safe(container, "div:nth-child(2) > h4:nth-child(2) > span")

        # Data de Julgamento (Assumindo a estrutura: div > span > h4:nth-child(1) > span)
        julgamento = _get_text_safe(container, "div:nth-child(2) > span > h4:nth-child(1) > span")

        # Data de Publicação (Assumindo a estrutura: div > span > h4:nth-child(2) > span)
        publicacao = _get_text_safe(container, "div:nth-child(2) > span > h4:nth-child(2) > span")

        # Monta o dicionário com os dados extraídos
        decisao = {
            "id_unico": i,
            "id_decisao_stf": id_decisao_stf,
            "decisao": titulo,
            "url": url_completa,
            "orgao_colegiado": orgao_colegiado,
            "relator": relator,
            "julgamento": julgamento,
            "publicacao": publicacao,
        }
        resultados.append(decisao)

    return resultados

# ==============================================================================
# 3. FUNÇÃO PRINCIPAL (MAIN)
# ==============================================================================

def main():
    """
    Função principal que coordena o fluxo de trabalho:
    1. Prepara os diretórios de entrada e saída.
    2. Encontra os arquivos HTML.
    3. Itera, extrai dados de cada arquivo e o move.
    4. Salva todos os dados extraídos em um único arquivo JSON.
    """
    
    # Cria os diretórios de saída se não existirem
    PROCESSED_HTML_PATH.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.mkdir(parents=True, exist_ok=True)
    
    # Lista todos os arquivos HTML no diretório de entrada
    html_files = list(INPUT_HTML_PATH.glob('*.html'))
    
    if not html_files:
        print(f"Nenhum arquivo HTML encontrado em '{INPUT_HTML_PATH}'.")
        return
    
    print(f"--- Processamento Iniciado ---")
    print(f"Arquivos HTML encontrados: {len(html_files)}")

    all_extracted_data = []
    
    # Processa cada arquivo HTML
    for i, html_file_path in enumerate(html_files):
        print(f"\n[Arquivo {i+1}/{len(html_files)}]: Processando '{html_file_path.name}'...")
        
        try:
            # Leitura do conteúdo HTML
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            # Execução da extração
            dados_extraidos = extrair_dados_stf(html, BASE_URL_STF)
            all_extracted_data.extend(dados_extraidos)
            print(f"-> {len(dados_extraidos)} decisões extraídas.")
            
            # Movimentação do arquivo após processamento bem-sucedido
            new_path = PROCESSED_HTML_PATH / html_file_path.name
            html_file_path.rename(new_path)
            print(f"-> Arquivo movido para '{PROCESSED_HTML_PATH.name}'.")

        except Exception as e:
            # Captura e loga erros específicos de leitura ou parsing
            print(f"*** ERRO ao processar o arquivo '{html_file_path.name}': {e} ***")


    # 4. Salvamento dos Resultados Finais
    
    output_filepath = OUTPUT_JSON_PATH / OUTPUT_JSON_FILENAME
    
    print(f"\n--- Salvando Resultados ---")
    print(f"Total de decisões encontradas: {len(all_extracted_data)}")
    
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            # Usa 'ensure_ascii=False' para garantir que caracteres acentuados sejam salvos corretamente
            json.dump(all_extracted_data, f, ensure_ascii=False, indent=4)
        
        print(f"Dados salvos com sucesso em '{output_filepath}'.")
    except Exception as e:
        print(f"*** ERRO ao salvar o arquivo JSON: {e} ***")

    print("\nProcesso concluído.")

if __name__ == "__main__":
    main()
