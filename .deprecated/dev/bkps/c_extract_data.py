import json
import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import pymongo
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from pymongo import ReturnDocument

class STFExtractor:
    def __init__(self, mongo_uri: str, db_name: str):
        """
        Inicializa o extrator de dados do STF com conexão ao MongoDB.
        
        Args:
            mongo_uri (str): URI de conexão com o MongoDB
            db_name (str): Nome do banco de dados
        """
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.raw_html_collection = self.db["raw_html"]
        self.case_data_collection = self.db["case_data"]
        
    def extract_single_document(self, html_content: str, source_doc_id: str) -> List[Dict[str, Any]]:
        """
        Analisa o conteúdo HTML completo e extrai todas as decisões encontradas.
        
        Args:
            html_content (str): Conteúdo HTML completo da página
            source_doc_id (str): ID do documento MongoDB original
            
        Returns:
            list: Lista de dicionários com os dados extraídos de cada decisão
        """
        soup = BeautifulSoup(html_content, "html.parser")
        resultados = []
        
        # Encontra todos os contêineres de resultados
        containers = soup.find_all("div", class_="result-container")
        
        print(f"Encontrados {len(containers)} containers de resultado")
        
        for i, container in enumerate(containers, start=1):
            print(f"Processando container {i}/{len(containers)}...")
            # Extrai dados de cada container
            decisao_data = self._extract_container_data(container, i, source_doc_id)
            if decisao_data:
                resultados.append(decisao_data)
        
        return resultados
    
    def _extract_container_data(self, container, local_index: int, source_doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Extrai todos os campos especificados de um único container de resultado.
        
        Args:
            container: Objeto BeautifulSoup do container
            local_index (int): Índice sequencial local
            source_doc_id (str): ID do documento fonte
            
        Returns:
            dict: Dicionário com todos os campos extraídos
        """
        try:
            # 1. localIndex - Gerado programaticamente
            localIndex = local_index
            
            # 2. stfDecisionId - Extraído do link "Dados completos"
            stfDecisionId = self._extract_stf_decision_id(container)
            
            # 3. caseTitle - Título da decisão
            caseTitle = self._extract_case_title(container)
            
            # 4. caseUrl - URL completa
            caseUrl = self._extract_case_url(container)
            
            # 5. judgingBody - Órgão julgador
            judgingBody = self._extract_judging_body(container)
            
            # 6. rapporteur - Relator
            rapporteur = self._extract_rapporteur(container)
            
            # 7. opinionWriter - Redator do acórdão
            opinionWriter = self._extract_opinion_writer(container)
            
            # 8. judgmentDate - Data de julgamento
            judgmentDate = self._extract_judgment_date(container)
            
            # 9. publicationDate - Data de publicação
            publicationDate = self._extract_publication_date(container)
            
            # 10. caseClass - Classe processual
            caseClass = self._extract_case_class(container)
            
            # 11. caseNumber - Número do processo
            caseNumber = self._extract_case_number(container)
            
            # 12. fullTextOccurrences - Ocorrências de inteiro teor
            fullTextOccurrences = self._extract_full_text_occurrences(container)
            
            # 13. indexingOccurrences - Ocorrências de indexação
            indexingOccurrences = self._extract_indexing_occurrences(container)
            
            # 14. domResultContainerId - ID DOM do container
            domResultContainerId = self._extract_dom_result_container_id(container)
            
            # 15. domClipboardId - ID DOM do clipboard
            domClipboardId = self._extract_dom_clipboard_id(container)
            
            # Cria o dicionário com todos os dados
            decisao_data = {
                "localIndex": localIndex,
                "stfDecisionId": stfDecisionId,
                "caseTitle": caseTitle,
                "caseUrl": caseUrl,
                "judgingBody": judgingBody,
                "rapporteur": rapporteur,
                "opinionWriter": opinionWriter,
                "judgmentDate": judgmentDate,
                "publicationDate": publicationDate,
                "caseClass": caseClass,
                "caseNumber": caseNumber,
                "fullTextOccurrences": fullTextOccurrences,
                "indexingOccurrences": indexingOccurrences,
                "domResultContainerId": domResultContainerId,
                "domClipboardId": domClipboardId,
                "extractionDate": datetime.now().isoformat(),
                "sourceDocumentId": source_doc_id,
                "status": "extracted"
            }
            
            print(f"  ✓ Container {localIndex}: {caseTitle}")
            return decisao_data
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair dados do container {local_index}: {e}")
            return None
    
    def _extract_stf_decision_id(self, container) -> str:
        """Extrai o ID da decisão do STF."""
        link = container.find("a", class_="mat-tooltip-trigger")
        if link and 'href' in link.attrs:
            href = link['href']
            href_parts = href.split('/')
            # Procura por segmento que comece com 'sjur'
            for part in reversed(href_parts):
                if part.startswith('sjur'):
                    return part
            # Se não encontrar 'sjur', retorna penúltimo segmento
            if len(href_parts) >= 2:
                return href_parts[-2] if href_parts[-1] else href_parts[-2]
        return "N/A"
    
    def _extract_case_title(self, container) -> str:
        """Extrai o título da decisão."""
        # Primeiro tenta encontrar via h4 direto
        h4_element = container.find("h4", class_="ng-star-inserted")
        if h4_element:
            return h4_element.text.strip()
        
        # Tenta encontrar via link
        link = container.find("a", class_="mat-tooltip-trigger")
        if link:
            h4_in_link = link.find("h4", class_="ng-star-inserted")
            if h4_in_link:
                return h4_in_link.text.strip()
        
        return "N/A"
    
    def _extract_case_url(self, container) -> str:
        """Extrai a URL completa da decisão."""
        link = container.find("a", class_="mat-tooltip-trigger")
        if link and 'href' in link.attrs:
            href = link['href']
            if href and not href.startswith('http'):
                return f"https://jurisprudencia.stf.jus.br{href}"
            return href
        return "N/A"
    
    def _extract_judging_body(self, container) -> str:
        """Extrai o órgão julgador."""
        # Procura por texto contendo "Órgão julgador"
        elements = container.find_all(["h4", "span", "div"])
        for element in elements:
            if "Órgão julgador" in element.text:
                # Tenta encontrar o valor no próximo elemento ou no próprio
                if element.find_next("span"):
                    return element.find_next("span").text.strip()
                # Tenta extrair texto após os dois pontos
                text_parts = element.text.split(":")
                if len(text_parts) > 1:
                    return text_parts[1].strip()
        return "N/A"
    
    def _extract_rapporteur(self, container) -> str:
        """Extrai o relator da decisão."""
        elements = container.find_all(["h4", "span", "div"])
        for element in elements:
            if "Relator" in element.text:
                if element.find_next("span"):
                    return element.find_next("span").text.strip()
                text_parts = element.text.split(":")
                if len(text_parts) > 1:
                    return text_parts[1].strip()
        return "N/A"
    
    def _extract_opinion_writer(self, container) -> str:
        """Extrai o redator do acórdão."""
        elements = container.find_all(["h4", "span", "div"])
        for element in elements:
            if "Redator" in element.text:
                if element.find_next("span"):
                    return element.find_next("span").text.strip()
                text_parts = element.text.split(":")
                if len(text_parts) > 1:
                    return text_parts[1].strip()
        return "N/A"
    
    def _extract_judgment_date(self, container) -> str:
        """Extrai a data de julgamento."""
        elements = container.find_all(["h4", "span", "div"])
        for element in elements:
            if "Julgamento" in element.text:
                if element.find_next("span"):
                    return element.find_next("span").text.strip()
                # Tenta extrair data com regex
                date_match = re.search(r'\d{2}/\d{2}/\d{4}', element.text)
                if date_match:
                    return date_match.group()
        return "N/A"
    
    def _extract_publication_date(self, container) -> str:
        """Extrai a data de publicação."""
        elements = container.find_all(["h4", "span", "div"])
        for element in elements:
            if "Publicação" in element.text:
                if element.find_next("span"):
                    return element.find_next("span").text.strip()
                # Tenta extrair data com regex
                date_match = re.search(r'\d{2}/\d{2}/\d{4}', element.text)
                if date_match:
                    return date_match.group()
        return "N/A"
    
    def _extract_case_class(self, container) -> str:
        """Extrai a classe processual."""
        # Procura link de acompanhamento processual
        links = container.find_all("a")
        for link in links:
            if 'href' in link.attrs and "classe=" in link['href']:
                parsed_url = urlparse(link['href'])
                query_params = parse_qs(parsed_url.query)
                if 'classe' in query_params:
                    return query_params['classe'][0]
        
        # Tenta extrair do título
        title = self._extract_case_title(container)
        if title and " " in title:
            return title.split()[0]
        
        return "N/A"
    
    def _extract_case_number(self, container) -> str:
        """Extrai o número do processo."""
        links = container.find_all("a")
        for link in links:
            if 'href' in link.attrs and "numeroProcesso=" in link['href']:
                parsed_url = urlparse(link['href'])
                query_params = parse_qs(parsed_url.query)
                if 'numeroProcesso' in query_params:
                    return query_params['numeroProcesso'][0]
        
        # Tenta extrair do título
        title = self._extract_case_title(container)
        if title:
            # Procura por números no título
            numbers = re.findall(r'\d+', title)
            if numbers:
                return numbers[-1]
        
        return "N/A"
    
    def _extract_full_text_occurrences(self, container) -> int:
        """Extrai o número de ocorrências de 'Inteiro teor'."""
        # Procura por texto "Inteiro teor"
        elements = container.find_all(text=re.compile(r'Inteiro teor', re.IGNORECASE))
        for element in elements:
            parent = element.parent
            if parent:
                # Procura por número entre parênteses
                text = parent.text if hasattr(parent, 'text') else str(parent)
                match = re.search(r'\((\d+)\)', text)
                if match:
                    return int(match.group(1))
        
        return 0
    
    def _extract_indexing_occurrences(self, container) -> int:
        """Extrai o número de ocorrências de indexação."""
        # Similar à extração de inteiro teor, mas para "Indexação"
        elements = container.find_all(text=re.compile(r'Indexação', re.IGNORECASE))
        for element in elements:
            parent = element.parent
            if parent:
                text = parent.text if hasattr(parent, 'text') else str(parent)
                match = re.search(r'\((\d+)\)', text)
                if match:
                    return int(match.group(1))
        
        return 0
    
    def _extract_dom_result_container_id(self, container) -> str:
        """Extrai o ID DOM do container de resultado."""
        if 'id' in container.attrs:
            return container['id']
        
        # Procura por ID nos elementos pais
        parent = container.parent
        while parent and parent.name != 'body':
            if 'id' in parent.attrs:
                return parent['id']
            parent = parent.parent
        
        return "N/A"
    
    def _extract_dom_clipboard_id(self, container) -> str:
        """Extrai o ID DOM do clipboard."""
        # Procura botão com tooltip relacionado a copiar
        buttons = container.find_all("button")
        for button in buttons:
            if 'mattooltip' in button.attrs and any(word in button['mattooltip'].lower() 
                                                   for word in ['copiar', 'copy', 'link']):
                if 'id' in button.attrs:
                    return button['id']
        
        return "N/A"
    def claim_next_raw_html(self) -> Optional[Dict]:
        """
        Claim atômico do próximo raw_html com status=new.
        Troca new -> extracting na mesma operação (evita 2 workers pegarem o mesmo doc).
        """
        try:
            now = datetime.now().isoformat()
            return self.raw_html_collection.find_one_and_update(
                {"status": "new"},
                {"$set": {"status": "extracting", "extractingAt": now}},
                sort=[("_id", 1)],
                return_document=ReturnDocument.AFTER,
            )
        except Exception as e:
            print(f"Erro ao buscar/claim documento: {e}")
            return None

    # def get_next_raw_html(self) -> Optional[Dict]:
    #     """
    #     Obtém o próximo documento raw_html com status "new" mais antigo.
        
    #     Returns:
    #         dict: Documento do MongoDB ou None se não houver documentos
    #     """
    #     try:
    #         query = {"status": "new"}
    #         # Ordena por data de criação mais antiga primeiro
    #         sort = [("_id", 1)]
    #         return self.raw_html_collection.find_one(query, sort=sort)

    #     except Exception as e:
    #         print(f"Erro ao buscar documento: {e}")
    #         return None
        
    def save_extracted_data(self, extracted_data: List[Dict[str, Any]]) -> bool:
        """
        Salva os dados extraídos na collection case_data usando UPSERT por stfDecisionId.
        
        Regras:
        - Se já existir documento com o mesmo stfDecisionId: atualiza campos ($set)
        - Se não existir: insere novo documento ($setOnInsert) + $set
        
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            if not extracted_data:
                print("Nenhum dado para salvar.")
                return False

            inserted = 0
            updated = 0
            skipped = 0

            for item in extracted_data:
                stf_id = item.get("stfDecisionId")
                if not stf_id or stf_id == "N/A":
                    skipped += 1
                    continue

                now = datetime.now().isoformat()

                # Campos que sempre atualizam (extraídos do HTML)
                set_fields = dict(item)
                set_fields["lastExtractedAt"] = now
                # Opcional: mantém a data original de extração também
                # set_fields["extractionDate"] = now  # (se você quiser sobrescrever sempre)

                # Campos apenas na criação do documento
                set_on_insert_fields = {
                    "createdAt": now,
                }

                result = self.case_data_collection.update_one(
                    {"stfDecisionId": stf_id},
                    {
                        "$set": set_fields,
                        "$setOnInsert": set_on_insert_fields,
                    },
                    upsert=True,
                )

                # Métricas:
                if result.upserted_id is not None:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1

            print(
                "Persistência concluída em case_data: "
                f"{inserted} inseridos, {updated} atualizados, {skipped} ignorados (stfDecisionId inválido)."
            )
            return True

        except Exception as e:
            print(f"Erro ao salvar dados (upsert): {e}")
            return False

    
    def update_raw_html_status(self, doc_id: ObjectId) -> bool:
        """
        Atualiza o status do documento raw_html para "extracted".
        
        Args:
            doc_id (ObjectId): ID do documento a ser atualizado
            
        Returns:
            bool: True se atualizou com sucesso, False caso contrário
        """
        try:
            result = self.raw_html_collection.update_one(
                {"_id": doc_id, "status": "extracting"},
                {"$set": {
                    "status": "extracted",
                    "processedDate": datetime.now().isoformat(),
                    "extractedCount": self.case_data_collection.count_documents({"sourceDocumentId": str(doc_id)}),
                }}
            )
            
            if result.modified_count > 0:
                print(f"Status do documento {doc_id} atualizado para 'extracted'.")
                return True
            else:
                print(f"Documento {doc_id} não encontrado ou já processado.")
                return False
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            return False
    
    def count_new_documents(self) -> int:
        """Conta quantos documentos com status 'new' existem."""
        try:
            return self.raw_html_collection.count_documents({"status": "new"})
        except Exception as e:
            print(f"Erro ao contar documentos: {e}")
            return 0
    
    def process_single_document(self) -> bool:
        """
        Processa um único documento raw_html.
        
        Returns:
            bool: True se processou com sucesso, False caso contrário
        """
        print("\n" + "="*60)
        print("Buscando próximo documento para processamento...")
        
        # # 1. Obter o próximo documento raw_html
        # raw_doc = self.get_next_raw_html()
        raw_doc = self.claim_next_raw_html()

        if not raw_doc:
            print("Nenhum documento com status 'new' encontrado.")
            return False
        
        doc_id = raw_doc["_id"]
        html_content = raw_doc.get("htmlRaw", "")
        
        print(f"Documento encontrado: {doc_id}")
        print(f"Título do documento: {raw_doc.get('title', 'Sem título')}")
        
        if not html_content:
            print(f"Documento {doc_id} não possui conteúdo HTML.")
            # Marca como erro
            self.raw_html_collection.update_one(
                {"_id": doc_id},
                {"$set": {"status": "error", 
                         "error": "Sem conteúdo HTML",
                         "processedDate": datetime.now().isoformat()}}
            )
            return False
        
        print(f"Processando {len(html_content)} caracteres de HTML...")
        
        # 2. Extrair dados do HTML
        try:
            extracted_data = self.extract_single_document(html_content, str(doc_id))
        except Exception as e:
            print(f"Erro na extração de dados: {e}")
            # Marca como erro
            self.raw_html_collection.update_one(
                {"_id": doc_id},
                {"$set": {"status": "error", 
                         "error": str(e),
                         "processedDate": datetime.now().isoformat()}}
            )
            return False
        
        if not extracted_data:
            print("Nenhum dado extraído do HTML.")
            # Marca como vazio
            self.raw_html_collection.update_one(
                {"_id": doc_id},
                {"$set": {"status": "empty", 
                         "processedDate": datetime.now().isoformat()}}
            )
            return True
        
        print(f"Extraídos {len(extracted_data)} registros de decisão.")
        
        # 3. Salvar dados extraídos na collection case_data
        save_success = self.save_extracted_data(extracted_data)
        
        if not save_success:
            print("Falha ao salvar dados extraídos.")
            # Marca como erro
            self.raw_html_collection.update_one(
                {"_id": doc_id},
                {"$set": {"status": "error", 
                         "error": "Falha ao salvar dados extraídos",
                         "processedDate": datetime.now().isoformat()}}
            )
            return False
        
        # 4. Atualizar status do documento raw_html
        update_success = self.update_raw_html_status(doc_id)
        
        if not update_success:
            print("Falha ao atualizar status do documento.")
            return False
        
        print(f"Processamento do documento {doc_id} concluído com sucesso!")
        return True
    
    def close(self):
        """Fecha a conexão com o MongoDB."""
        self.client.close()


def main():
    """
    Função principal para executar o processo de extração.
    """
    # Configuração da conexão com MongoDB
    DB_USERNAME = "cito"
    DB_PASSWORD = "fyu9WxkHakGKHeoq"
    DB_NAME = "cito-v-a33-240125"
    
    # Construir URI de conexão
    MONGO_URI = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.gb8bzlp.mongodb.net/?appName=Cluster0"
    
    print("="*60)
    print("INICIANDO PROCESSO DE EXTRAÇÃO DE DADOS DO STF")
    print("="*60)
    print(f"Conectando ao banco de dados: {DB_NAME}")
    print(f"Collection origem: raw_html")
    print(f"Collection destino: case_data")
    print("="*60)
    
    try:
        # Inicializar extrator
        extractor = STFExtractor(MONGO_URI, DB_NAME)
        
        # Verificar quantos documentos novos existem
        new_docs_count = extractor.count_new_documents()
        print(f"\nDocumentos pendentes (status='new'): {new_docs_count}")
        
        if new_docs_count == 0:
            print("Nenhum documento para processar. Encerrando.")
            extractor.close()
            return
        
        # Processar documentos enquanto houver novos
        processed_count = 0
        max_documents = min(new_docs_count, 50)  # Limite de segurança
        
        print(f"\nProcessando até {max_documents} documentos...")
        
        while processed_count < max_documents:
            success = extractor.process_single_document()
            
            if not success:
                print("Nenhum documento para processar ou erro no processamento.")
                break
            
            processed_count += 1
            
            # Atualizar contagem de documentos restantes
            remaining = extractor.count_new_documents()
            print(f"\nProgresso: {processed_count}/{max_documents} processados")
            print(f"Documentos restantes: {remaining}")
            
            if remaining == 0:
                print("Todos os documentos foram processados!")
                break
        
        print("\n" + "="*60)
        print(f"PROCESSAMENTO CONCLUÍDO")
        print(f"Total de documentos processados: {processed_count}")
        print("="*60)
        
        # Fechar conexão
        extractor.close()
        
    except pymongo.errors.ConnectionFailure as e:
        print(f"ERRO DE CONEXÃO: Não foi possível conectar ao MongoDB: {e}")
        print("Verifique as credenciais e a conexão com a internet.")
    except Exception as e:
        print(f"ERRO NO PROCESSAMENTO: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Instalar dependências se necessário
    try:
        import pymongo
        import bs4
    except ImportError:
        print("Instalando dependências necessárias...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo", "beautifulsoup4"])
        print("Dependências instaladas com sucesso!")
    
    main()