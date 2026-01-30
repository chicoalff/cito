"""
Módulo para extração de dados de jurisprudência do STF a partir de arquivos HTML.

Este script processa arquivos HTML contendo decisões do STF, extrai informações
estruturadas e as salva em formato JSON.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup
from lxml import html as lxml_html

# =============================================================================
# CONFIGURAÇÕES E PARÂMETROS
# =============================================================================

# Configurações de diretórios
DIR_CONFIG = {
    'input_html': Path('sd-data/projects/CITO/cito/poc/v01-a33/data/html'),
    'output_json': Path('sd-data/projects/CITO/cito/poc/v01-a33/data/json'),
    'processed_html': Path('sd-data/projects/CITO/cito/poc/v01-a33/data/html/processed')
}

# Configurações da URL base
URL_CONFIG = {
    'base_url': 'https://jurisprudencia.stf.jus.br',
    'url_placeholder': 'N/A'
}

# Configurações de seletores HTML/XPath
SELECTORS = {
    'container': 'div.result-container',
    'link': 'a.mat-tooltip-trigger',
    'titulo': 'h4.ng-star-inserted',
    'xpath_base': '/html/body/app-root/app-home/main/search/div/div/div/div[2]/div/div[2]/div[{}]'
}

# Configurações de arquivos
FILE_CONFIG = {
    'input_pattern': '*.html',
    'output_filename': 'jurisprudencia.json'
}

# =============================================================================
# FUNÇÕES DE EXTRAÇÃO
# =============================================================================

def extrair_dados_stf(html_content):
    """
    Analisa o conteúdo HTML de uma página de jurisprudência do STF e extrai
    as informações estruturadas de cada decisão.

    Args:
        html_content (str): O conteúdo HTML da página.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma decisão.
    """
    # Inicializa parsers HTML
    soup = BeautifulSoup(html_content, "lxml")
    tree = lxml_html.fromstring(html_content)
    resultados = []
    
    # Encontra todos os contêineres de resultados de decisão
    containers = soup.find_all("div", class_=SELECTORS['container'].split('.')[-1])
    
    # Itera sobre cada contêiner para extrair os dados
    for indice, container in enumerate(containers, start=1):
        dados_decisao = _extrair_dados_container(container, tree, indice)
        resultados.append(dados_decisao)
    
    return resultados


def _extrair_dados_container(container, tree, indice):
    """
    Extrai dados de um único container de decisão.

    Args:
        container: Elemento BeautifulSoup do container
        tree: Element tree do lxml para XPath
        indice (int): Índice numérico da decisão

    Returns:
        dict: Dicionário com todos os dados extraídos da decisão
    """
    # Extrai URL e ID único
    url_completa, id_decisao_stf = _extrair_url_id(container)
    
    # Extrai título da decisão
    titulo = _extrair_titulo(container)
    
    # Extrai informações via XPath
    orgao_colegiado = _extrair_via_xpath(tree, indice, 1, "orgao_colegiado")
    relator = _extrair_via_xpath(tree, indice, 2, "relator")
    julgamento = _extrair_via_xpath(tree, indice, 1, "julgamento")
    publicacao = _extrair_via_xpath(tree, indice, 2, "publicacao")
    
    # Monta o dicionário com os dados extraídos
    return {
        "id_unico": indice,
        "id_decisao_stf": id_decisao_stf,
        "decisao": titulo,
        "url": url_completa,
        "orgao_colegiado": orgao_colegiado,
        "relator": relator,
        "julgamento": julgamento,
        "publicacao": publicacao,
    }


def _extrair_url_id(container):
    """
    Extrai URL completa e ID único da decisão a partir do container.

    Args:
        container: Elemento BeautifulSoup do container

    Returns:
        tuple: (url_completa, id_decisao_stf)
    """
    link_element = container.find("a", class_=SELECTORS['link'].split('.')[-1])
    
    if not link_element or not link_element.has_attr('href'):
        return URL_CONFIG['url_placeholder'], URL_CONFIG['url_placeholder']
    
    url_parcial = link_element['href']
    url_completa = f"{URL_CONFIG['base_url']}{url_parcial}"
    
    # Extrai ID da decisão da URL
    partes_url = url_parcial.split('/')
    id_decisao_stf = partes_url[-2] if len(partes_url) > 2 else URL_CONFIG['url_placeholder']
    
    return url_completa, id_decisao_stf


def _extrair_titulo(container):
    """
    Extrai o título da decisão do container.

    Args:
        container: Elemento BeautifulSoup do container

    Returns:
        str: Título da decisão ou 'N/A' se não encontrado
    """
    titulo_element = container.find("h4", class_=SELECTORS['titulo'].split('.')[-1])
    return titulo_element.text.strip() if titulo_element else URL_CONFIG['url_placeholder']


def _extrair_via_xpath(tree, indice, posicao, tipo_dado):
    """
    Extrai dados específicos usando XPath.

    Args:
        tree: Element tree do lxml
        indice (int): Índice do container
        posicao (int): Posição do elemento no XPath
        tipo_dado (str): Tipo de dado sendo extraído

    Returns:
        str: Dado extraído ou 'N/A' se não encontrado
    """
    xpath_mappings = {
        "orgao_colegiado": f"{SELECTORS['xpath_base'].format(indice)}/div[2]/h4[{posicao}]/span",
        "relator": f"{SELECTORS['xpath_base'].format(indice)}/div[2]/h4[{posicao}]/span",
        "julgamento": f"{SELECTORS['xpath_base'].format(indice)}/div[2]/span/h4[{posicao}]/span",
        "publicacao": f"{SELECTORS['xpath_base'].format(indice)}/div[2]/span/h4[{posicao}]/span"
    }
    
    xpath = xpath_mappings.get(tipo_dado)
    if not xpath:
        return URL_CONFIG['url_placeholder']
    
    elemento = tree.xpath(xpath)
    return elemento[0].text.strip() if elemento else URL_CONFIG['url_placeholder']


# =============================================================================
# FUNÇÕES DE GERENCIAMENTO DE ARQUIVOS
# =============================================================================

def inicializar_diretorios():
    """
    Cria os diretórios necessários para o processamento.

    Returns:
        bool: True se os diretórios foram criados/verificados com sucesso
    """
    try:
        DIR_CONFIG['processed_html'].mkdir(parents=True, exist_ok=True)
        DIR_CONFIG['output_json'].mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Erro ao criar diretórios: {e}")
        return False


def listar_arquivos_html():
    """
    Lista todos os arquivos HTML no diretório de entrada.

    Returns:
        list: Lista de Path objects para arquivos HTML
    """
    html_files = list(DIR_CONFIG['input_html'].glob(FILE_CONFIG['input_pattern']))
    
    if html_files:
        print(f"Arquivos HTML encontrados para processamento em '{DIR_CONFIG['input_html']}':")
        for arquivo in html_files:
            print(f"- {arquivo.name}")
    else:
        print(f"Nenhum arquivo HTML encontrado em '{DIR_CONFIG['input_html']}'.")
    
    return html_files


def processar_arquivos(arquivos_html):
    """
    Processa todos os arquivos HTML e extrai os dados.

    Args:
        arquivos_html (list): Lista de caminhos para arquivos HTML

    Returns:
        list: Lista com todos os dados extraídos
    """
    all_extracted_data = []
    
    for indice, caminho_arquivo in enumerate(arquivos_html, start=1):
        print(f"\nProcessando arquivo {indice}/{len(arquivos_html)}: {caminho_arquivo.name}")
        
        dados_extraidos = _processar_arquivo_individual(caminho_arquivo)
        all_extracted_data.extend(dados_extraidos)
        
        # Move o arquivo processado
        _mover_arquivo_processado(caminho_arquivo)
    
    return all_extracted_data


def _processar_arquivo_individual(caminho_arquivo):
    """
    Processa um arquivo HTML individual e extrai os dados.

    Args:
        caminho_arquivo (Path): Caminho para o arquivo HTML

    Returns:
        list: Dados extraídos do arquivo
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            html_content = arquivo.read()
        
        return extrair_dados_stf(html_content)
    except Exception as e:
        print(f"Erro ao processar arquivo {caminho_arquivo.name}: {e}")
        return []


def _mover_arquivo_processado(caminho_arquivo):
    """
    Move um arquivo processado para o diretório de processados.

    Args:
        caminho_arquivo (Path): Caminho do arquivo a ser movido
    """
    try:
        novo_caminho = DIR_CONFIG['processed_html'] / caminho_arquivo.name
        caminho_arquivo.rename(novo_caminho)
        print(f"Arquivo '{caminho_arquivo.name}' movido para '{DIR_CONFIG['processed_html']}'")
    except Exception as e:
        print(f"Erro ao mover arquivo {caminho_arquivo.name}: {e}")


def salvar_dados_json(dados_extraidos):
    """
    Salva os dados extraídos em arquivo JSON.

    Args:
        dados_extraidos (list): Lista de dicionários com dados extraídos

    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        caminho_saida = DIR_CONFIG['output_json'] / FILE_CONFIG['output_filename']
        
        with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
            json.dump(dados_extraidos, arquivo, ensure_ascii=False, indent=4)
        
        print(f"\nSalvos {len(dados_extraidos)} decisões em '{caminho_saida}'")
        return True
    except Exception as e:
        print(f"Erro ao salvar arquivo JSON: {e}")
        return False


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """
    Função principal que orquestra todo o processo de extração e salvamento.
    """
    print("Iniciando processo de extração de dados do STF...")
    
    # Inicializa diretórios
    if not inicializar_diretorios():
        return
    
    # Lista arquivos para processamento
    arquivos_html = listar_arquivos_html()
    
    if not arquivos_html:
        return
    
    # Processa arquivos e extrai dados
    dados_extraidos = processar_arquivos(arquivos_html)
    
    if not dados_extraidos:
        print("Nenhum dado foi extraído dos arquivos.")
        return
    
    # Salva dados em JSON
    if salvar_dados_json(dados_extraidos):
        print("Processo concluído com sucesso!")
    else:
        print("Processo concluído com erros.")


if __name__ == "__main__":
    main()