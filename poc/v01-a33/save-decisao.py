import re
import json
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Any

def extract_metadata(soup: BeautifulSoup, label_text: str) -> Optional[str]:
    """
    Função auxiliar para extrair o valor de um campo de metadado (ex: Relator, Julgamento)
    onde o rótulo e o valor são elementos HTML vizinhos em uma estrutura comum.
    Usado para campos de linha única (Relator, Órgão Julgador, etc.).
    """
    # 1. Procura pelo elemento que contém o texto do rótulo
    label_element = soup.find(lambda tag: tag.name == 'div' and label_text in tag.get_text(strip=True))

    if label_element:
        # O valor está tipicamente no próximo elemento <div>
        next_sibling = label_element.find_next_sibling('div')
        if next_sibling:
            return next_sibling.get_text(strip=True)
    return None

def extract_multi_line_metadata(soup: BeautifulSoup, start_text: str, end_text: Optional[str] = None) -> List[str]:
    """
    Extrai um bloco de metadados ou conteúdo que pode se estender por várias linhas/elementos
    irmãos, parando no rótulo de 'end_text' (se fornecido).
    Usado para Partes, Legislação, Ementa, Decisão, etc.
    """
    # Procura pelo elemento que contém o rótulo da seção (ex: "Publicação:", "EMENTA:")
    start_element = soup.find(lambda tag: tag.name in ['div', 'p'] and start_text in tag.get_text(strip=True))

    # Caso especial para 'Partes', onde o rótulo de seção "Partes:" não existe, mas sim "REQTE.(S)"
    if "REQTE.(S)" in start_text:
        start_element = soup.find(lambda tag: tag.name in ['div', 'p'] and "REQTE.(S)" in tag.get_text(strip=True))
    
    if not start_element:
        return []

    lines: List[str] = []
    
    current_element = start_element
    
    # Se o rótulo for de uma seção, o conteúdo útil começa no próximo elemento.
    if start_text.endswith(':') and not start_text.startswith("EMENTA"):
        # Adiciona o texto do próprio rótulo se ele contiver valor (ex: "Decisão: Texto")
        if current_element and start_text in current_element.get_text(strip=True) and current_element.get_text(strip=True).replace(start_text, '').strip():
             lines.append(current_element.get_text(strip=True))
             
        # Move para o próximo elemento que deve conter o bloco de dados
        current_element = start_element.find_next_sibling(['div', 'p'])
    
    # Itera sobre os elementos irmãos a partir do ponto de partida
    while current_element:
        content_stripped = current_element.get_text(strip=True)
        
        # Critério de Parada: Encontrou um novo rótulo de seção principal (em CAPS e com :)
        # Isso evita que a extração de 'Partes' continue na 'EMENTA' ou 'Decisão'.
        is_major_section = (
            content_stripped.isupper() and 
            content_stripped.endswith(':') and 
            len(content_stripped) > 5 and 
            not any(abbr in content_stripped for abbr in ["ADV.", "PROC.", "REQTE.", "INTDO.", "AM. CURIAE."])
        )

        if is_major_section and content_stripped != start_text.strip():
            break
            
        # Parada explícita por texto (usado para Ementa que para em Decisão:)
        if end_text and end_text in content_stripped:
            break

        if content_stripped:
            lines.append(content_stripped)
        
        # Move para o próximo elemento irmão
        current_element = current_element.find_next_sibling(['div', 'p'])
        
    # Remove duplicatas e linhas vazias
    cleaned_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines if line.strip()]
    return list(dict.fromkeys(cleaned_lines))

def processar_decisao(html_content: str) -> Dict[str, Any]:
    """
    Processa o HTML de uma página de detalhe de decisão do STF para extrair os dados
    e formatá-los conforme as especificações.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    data: Dict[str, Any] = {}

    # --- 1. Extração do Título, Classe, ID e UF ---
    title_text = ''
    try:
        title_element = soup.find('div', class_='title-detail')
        title_text = title_element.get_text(strip=True) if title_element else ''
        
        # Extrai Classe (sigla no início) e ID (número)
        match_title = re.match(r'([A-Z]+)\s+([A-Z\d\-\.]+)', title_text)
        data['classe'] = match_title.group(1).strip() if match_title else 'N/A'
        data['id_stf'] = match_title.group(2).strip() if match_title else 'N/A'
        
        # Para ADI/ADC/ADPF (Controle Concentrado), a UF é geralmente o Distrito Federal
        # se não for especificada, mantendo a regra de duas letras.
        data['uf'] = 'DF' if data['classe'] in ['ADI', 'ADC', 'ADPF'] else 'N/A' 
    except Exception as e:
        print(f"Erro ao extrair título/ID/classe: {e}")
        data['classe'] = 'N/A'
        data['id_stf'] = 'N/A'
        data['uf'] = 'N/A'

    # --- 2. Metadados de linha única (Relator, Órgão Julgador) ---
    data['relator'] = extract_metadata(soup, "Relator:")
    data['orgao_julgador'] = extract_metadata(soup, "Órgão julgador:")
    data['data_julgamento'] = extract_metadata(soup, "Julgamento:")
    
    # --- 3. Publicação (Bloco de texto com múltiplas linhas) ---
    data['publicacao'] = "\n".join(extract_multi_line_metadata(soup, "Publicação:"))
    
    # --- 4. Partes (Bloco de texto estruturado) ---
    # Partes começa geralmente com REQTE.(S) ou similar
    data['partes'] = extract_multi_line_metadata(soup, "REQTE.(S)")

    # --- 5. Ementa (Bloco de texto longo) ---
    ementa_lines = extract_multi_line_metadata(soup, "EMENTA:", end_text="Decisão:")
    # Remove o rótulo "EMENTA:" se ele vier na primeira linha para evitar duplicação no texto final.
    if ementa_lines and ementa_lines[0].startswith("EMENTA:"):
        ementa_lines[0] = ementa_lines[0].replace("EMENTA:", "", 1).strip()
    data['ementa'] = "\n\n".join(ementa_lines)

    # --- 6. Decisão (Bloco de texto) ---
    decisao_lines = extract_multi_line_metadata(soup, "Decisão:")
    # Remove o rótulo "Decisão:" se ele vier na primeira linha.
    if decisao_lines and decisao_lines[0].startswith("Decisão:"):
        decisao_lines[0] = decisao_lines[0].replace("Decisão:", "", 1).strip()
    data['decisao'] = "\n\n".join(decisao_lines)
    
    # --- 7. Tese Jurídica (Seção opcional, busca pelo rótulo "Tese:") ---
    # Retorna o texto se houver a seção, caso contrário, será vazio.
    data['tese'] = "\n".join(extract_multi_line_metadata(soup, "Tese:"))
    
    # --- 8. Indexação (Palavras-chave) ---
    data['indexacao'] = extract_multi_line_metadata(soup, "Indexação:")

    # --- 9. Legislação (Referências estruturadas) ---
    data['legislacao'] = extract_multi_line_metadata(soup, "Legislação:")

    # --- 10. Doutrina (Referências bibliográficas) ---
    data['doutrina'] = extract_multi_line_metadata(soup, "Doutrina:")

    # --- 11. URL do Arquivo PDF (Inteiro Teor) ---
    data['url_arquivo'] = 'N/A'
    try:
        # Busca por links com título "Inteiro Teor" ou que terminem em .pdf
        pdf_link = soup.find('a', title=re.compile(r'Inteiro Teor', re.I)) or soup.find('a', href=re.compile(r'\.pdf$', re.I))
        if pdf_link and pdf_link.get('href'):
            data['url_arquivo'] = pdf_link.get('href')
    except Exception:
        data['url_arquivo'] = 'N/A'
        
    # --- 12. Observações (Campo não presente no HTML, mantido vazio na estrutura) ---
    data['observacoes'] = "" 

    # --- 13. Limpeza Final em campos de texto simples ---
    for key in ['relator', 'orgao_julgador', 'data_julgamento']:
        if data[key] is None:
            data[key] = 'N/A'
        else:
            data[key] = re.sub(r'\s+', ' ', data[key]).strip()

    return data

# --- Exemplo de Uso do Script ---
if __name__ == "__main__":
    # O nome do arquivo a ser processado (HTML fornecido pelo usuário)
    input_file_path = "/home/chico/productnauta/sd-data/projects/CITO/cito/poc/v01-a33/data/decisoes/adi-7200/adi-7200-14-10-2025-11-53-03.html"
    
    # Regex para extrair a classe e o ID para o nome do arquivo JSON
    # Ex: adi-7200-....html -> ADI-7200_DADOS.json
    match_filename = re.search(r'([a-zA-Z]+)-([\d\-\.]+)', input_file_path, re.I)
    
    if match_filename:
        # Padrão de nomeclatura: <CLASSE>-<ID>_DADOS.json
        json_file_name = f"{match_filename.group(1).upper()}-{match_filename.group(2)}_DADOS.json"
    else:
        json_file_name = "dados_decisao_extraidos.json"

    print(f"Iniciando o processamento do arquivo: {input_file_path}")

    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        dados_extraidos = processar_decisao(html_content)

        # Salva o resultado no formato JSON
        with open(json_file_name, 'w', encoding='utf-8') as json_f:
            # ensure_ascii=False permite que caracteres como acentos e cedilha sejam salvos corretamente
            json.dump(dados_extraidos, json_f, indent=4, ensure_ascii=False)

        print("\n" + "="*70)
        print("EXTRAÇÃO CONCLUÍDA")
        print(f"Dados salvos com sucesso em: {json_file_name}")
        print("="*70)
        print("\nRESUMO DOS DADOS (JSON):")
        # Imprime o JSON formatado no console
        print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))

    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file_path}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro durante o processamento: {e}")
