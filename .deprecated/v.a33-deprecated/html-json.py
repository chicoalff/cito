import json
from bs4 import BeautifulSoup
from lxml import html as lxml_html
from pathlib import Path

def extrair_dados_stf(html_content):
    """
    Analisa o conteúdo HTML de uma página de jurisprudência do STF e extrai
    as informações estruturadas de cada decisão.

    Args:
        html_content (str): O conteúdo HTML da página.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa uma decisão.
    """
    soup = BeautifulSoup(html_content, "lxml")
    tree = lxml_html.fromstring(html_content)
    resultados = []
    
    # Encontra todos os contêineres de resultados de decisão
    containers = soup.find_all("div", class_="result-container")
    
    # Itera sobre cada contêiner para extrair os dados
    for i, container in enumerate(containers, start=1):
        # --- URL e ID Único ---
        link_element = container.find("a", class_="mat-tooltip-trigger")
        url_parcial = link_element['href'] if link_element and link_element.has_attr('href') else ""
        url_completa = f"https://jurisprudencia.stf.jus.br{url_parcial}" if url_parcial else "N/A"
        id_decisao_stf = url_parcial.split('/')[-2] if url_parcial and len(url_parcial.split('/')) > 2 else "N/A"

        # --- Título da Decisão ---
        titulo_element = container.find("h4", class_="ng-star-inserted")
        titulo = titulo_element.text.strip() if titulo_element else "N/A"

        # --- Extração via XPath para Órgão e Relator ---
        # O XPath fornecido é absoluto, então precisamos adaptá-lo para cada container
        xpath_base_container = f"/html/body/app-root/app-home/main/search/div/div/div/div[2]/div/div[2]/div[{i}]"
        
        orgao_el = tree.xpath(f"{xpath_base_container}/div[2]/h4[1]/span")
        orgao_colegiado = orgao_el[0].text.strip() if orgao_el else "N/A"

        relator_el = tree.xpath(f"{xpath_base_container}/div[2]/h4[2]/span")
        relator = relator_el[0].text.strip() if relator_el else "N/A"

        # --- Extração de Datas via XPath ---
        julgamento_el = tree.xpath(f"{xpath_base_container}/div[2]/span/h4[1]/span")
        julgamento = julgamento_el[0].text.strip() if julgamento_el else "N/A"

        publicacao_el = tree.xpath(f"{xpath_base_container}/div[2]/span/h4[2]/span")
        publicacao = publicacao_el[0].text.strip() if publicacao_el else "N/A"

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

def main():
    """
    Função principal para ler o arquivo HTML, extrair os dados e salvar em JSON.
    """
    html_input_dir = Path('poc/v01-a33/data/html')
    processed_output_dir = html_input_dir / 'processed'
    processed_output_dir.mkdir(parents=True, exist_ok=True)
    
    html_files = list(html_input_dir.glob('*.html'))
    
    if not html_files:
        print(f"Nenhum arquivo HTML encontrado em '{html_input_dir}'.")
        return
    
    print(f"Arquivos HTML encontrados para processamento em '{html_input_dir}':")
    for f in html_files:
        print(f"- {f.name}")

    all_extracted_data = []
    for i, html_file_path in enumerate(html_files):
        print(f"\nProcessando arquivo {i+1}/{len(html_files)}: {html_file_path.name}")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        dados_extraidos = extrair_dados_stf(html)
        all_extracted_data.extend(dados_extraidos)
        
        # Mover o arquivo HTML processado
        new_path = processed_output_dir / html_file_path.name
        html_file_path.rename(new_path)
        print(f"Arquivo '{html_file_path.name}' movido para '{processed_output_dir}'")

    print(f"\nSalvando {len(all_extracted_data)} decisões totais encontradas em 'jurisprudencia.json'")
    
    json_output_dir = Path('poc/v01-a33/data/json')
    json_output_dir.mkdir(parents=True, exist_ok=True)
    with open(json_output_dir / 'jurisprudencia.json', 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, ensure_ascii=False, indent=4)
    
    print("Processo concluído com sucesso!")

if __name__ == "__main__":
    main()
