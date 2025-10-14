import os
import json
import re
from bs4 import BeautifulSoup
from mistralai import Mistral
import warnings

warnings.filterwarnings('ignore')

class AnalisadorDecisoesSTF:
    def __init__(self, api_key):
        self.client = Mistral(api_key=api_key)
    
    def processar_decisao_html(self, caminho_arquivo):
        """Processa especificamente decisões do STF"""
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            textos_importantes = []
            secoes_potenciais = soup.find_all(['div', 'section', 'article', 'main'])
            
            for secao in secoes_potenciais:
                texto = secao.get_text().strip()
                if len(texto) > 100:
                    textos_importantes.append(texto)
            
            if not textos_importantes:
                texto_completo = soup.get_text()
                textos_importantes = [texto_completo]
            
            texto_final = ' '.join(textos_importantes)[:5000]
            return texto_final
            
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def limpar_resposta_json(self, resposta):
        """Limpa a resposta do Mistral para extrair JSON puro"""
        try:
            # Remover blocos de código markdown
            resposta_limpa = re.sub(r'```json\s*', '', resposta)
            resposta_limpa = re.sub(r'\s*```', '', resposta_limpa)
            
            # Remover espaços extras no início e fim
            resposta_limpa = resposta_limpa.strip()
            
            return resposta_limpa
        except Exception as e:
            print(f"Erro ao limpar resposta: {e}")
            return resposta
    
    def analisar_decisao_juridica(self, texto):
        """Análise especializada para decisões jurídicas"""
        prompt = f"""
        Você é um especialista em direito constitucional brasileiro. Analise esta decisão do STF e extraia:

        {{
            "processo": {{
                "numero": "string",
                "tipo": "string (ex: ADI, ADC, etc)"
            }},
            "partes": {{
                "autor": "string",
                "reu": "string ou array"
            }},
            "relator": "string",
            "data_julgamento": "string",
            "decisao": {{
                "resultado": "string",
                "tese_principal": "string",
                "votos": "resumo dos votos se disponível"
            }},
            "fundamentos": {{
                "principais_argumentos": "array de strings",
                "base_legal": "array de dispositivos legais citados"
            }},
            "ementa": "string (se disponível)",
            "tema_repercussao": "string"
        }}

        Conteúdo para análise:
        {texto}

        Retorne APENAS JSON válido, sem nenhum texto adicional, sem markdown, sem ```json.
        """
        
        try:
            resposta = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Limpar a resposta
            resposta_limpa = self.limpar_resposta_json(resposta.choices[0].message.content)
            return resposta_limpa
            
        except Exception as e:
            return f"Erro: {e}"
    
    def salvar_json(self, caminho_arquivo_html, dados):
        """Salva os dados em JSON na mesma pasta com mesma nomenclatura"""
        try:
            diretorio = os.path.dirname(caminho_arquivo_html)
            nome_arquivo = os.path.basename(caminho_arquivo_html)
            nome_json = nome_arquivo.replace('.html', '.json')
            caminho_json = os.path.join(diretorio, nome_json)
            
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            print(f"JSON salvo com sucesso: {caminho_json}")
            return caminho_json
            
        except Exception as e:
            print(f"Erro ao salvar JSON: {e}")
            return None
    
    def executar_analise(self, caminho_arquivo):
        """Executa análise completa e salva JSON"""
        print(f"Analisando: {os.path.basename(caminho_arquivo)}")
        
        texto = self.processar_decisao_html(caminho_arquivo)
        if not texto:
            return {"erro": "Falha ao processar arquivo"}
        
        print("Texto extraído. Consultando Mistral...")
        resultado_bruto = self.analisar_decisao_juridica(texto)
        
        # Processar resultado - agora já limpo
        try:
            dados_json = json.loads(resultado_bruto)
            status_json = "json_valido"
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            print(f"Resposta bruta: {resultado_bruto}")
            dados_json = {"resultado_bruto": resultado_bruto}
            status_json = "json_invalido"
        
        # Adicionar metadados
        if isinstance(dados_json, dict):
            dados_json["_metadados"] = {
                "arquivo_origem": os.path.basename(caminho_arquivo),
                "data_processamento": "2025-01-14",
                "modelo_ia": "mistral-large-latest",
                "tipo_analise": "juridica",
                "status_json": status_json
            }
        
        # Salvar JSON
        caminho_json = self.salvar_json(caminho_arquivo, dados_json)
        
        return {
            "status": "sucesso" if caminho_json else "erro_salvamento",
            "arquivo_json": caminho_json,
            "dados": dados_json
        }

# Versão alternativa com prompt mais restritivo
class AnalisadorDecisoesSTFStrict:
    def __init__(self, api_key):
        self.client = Mistral(api_key=api_key)
    
    def processar_decisao_html(self, caminho_arquivo):
        """Processa especificamente decisões do STF"""
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extrair texto de forma mais específica
            texto_completo = soup.get_text()
            
            # Limpar texto
            lines = (line.strip() for line in texto_completo.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            texto_limpo = ' '.join(chunk for chunk in chunks if chunk)
            
            return texto_limpo[:4000]
            
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def analisar_decisao_juridica(self, texto):
        """Análise especializada com prompt mais restritivo"""
        prompt = f"""
        ANALISE JURÍDICA - FORMATO ESTRITO

        CONTEÚDO PARA ANÁLISE:
        {texto}

        EXTRAIA APENAS AS SEGUINTES INFORMAÇÕES EM FORMATO JSON:

        {{
            "processo": {{
                "numero": "texto",
                "tipo": "texto"
            }},
            "partes": {{
                "autor": "texto",
                "reu": ["texto1", "texto2"]
            }},
            "relator": "texto",
            "data_julgamento": "texto",
            "decisao": {{
                "resultado": "texto",
                "tese_principal": "texto",
                "votos": {{
                    "relator": "texto",
                    "demais_ministros": "texto"
                }}
            }},
            "fundamentos": {{
                "principais_argumentos": ["texto1", "texto2"],
                "base_legal": ["texto1", "texto2"]
            }},
            "ementa": "texto",
            "tema_repercussao": "texto"
        }}

        REGRAS:
        1. Retorne APENAS o JSON, sem nenhum texto adicional
        2. Não use markdown
        3. Não use ```json
        4. Se informação não existir, use null
        5. Mantenha a estrutura exata do JSON acima
        """
        
        try:
            resposta = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.0  # Temperatura zero para mais consistência
            )
            
            # Limpar resposta
            resposta_limpa = resposta.choices[0].message.content.strip()
            
            # Remover possíveis marcadores residuais
            resposta_limpa = re.sub(r'^```json\s*', '', resposta_limpa)
            resposta_limpa = re.sub(r'\s*```$', '', resposta_limpa)
            
            return resposta_limpa
            
        except Exception as e:
            return f"Erro: {e}"
    
    def salvar_json(self, caminho_arquivo_html, dados):
        """Salva os dados em JSON na mesma pasta com mesma nomenclatura"""
        try:
            diretorio = os.path.dirname(caminho_arquivo_html)
            nome_arquivo = os.path.basename(caminho_arquivo_html)
            nome_json = nome_arquivo.replace('.html', '.json')
            caminho_json = os.path.join(diretorio, nome_json)
            
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            print(f"JSON salvo com sucesso: {caminho_json}")
            return caminho_json
            
        except Exception as e:
            print(f"Erro ao salvar JSON: {e}")
            return None
    
    def executar_analise(self, caminho_arquivo):
        """Executa análise completa e salva JSON"""
        print(f"Analisando: {os.path.basename(caminho_arquivo)}")
        
        texto = self.processar_decisao_html(caminho_arquivo)
        if not texto:
            return {"erro": "Falha ao processar arquivo"}
        
        print("Texto extraído. Consultando Mistral...")
        resultado_bruto = self.analisar_decisao_juridica(texto)
        
        # Tentar parsear JSON
        try:
            dados_json = json.loads(resultado_bruto)
            status_json = "sucesso"
        except json.JSONDecodeError as e:
            print(f"ERRO JSON: {e}")
            print(f"Conteúdo recebido: {resultado_bruto}")
            
            # Tentativa de correção automática
            try:
                # Remover qualquer texto antes do primeiro { e depois do último }
                inicio = resultado_bruto.find('{')
                fim = resultado_bruto.rfind('}') + 1
                if inicio != -1 and fim != 0:
                    json_corrigido = resultado_bruto[inicio:fim]
                    dados_json = json.loads(json_corrigido)
                    status_json = "sucesso_corrigido"
                else:
                    raise ValueError("Não foi possível encontrar JSON")
            except:
                dados_json = {"erro": "Falha ao processar JSON", "resposta_bruta": resultado_bruto}
                status_json = "erro"
        
        # Adicionar metadados se for um dicionário
        if isinstance(dados_json, dict):
            dados_json["_metadados"] = {
                "arquivo_origem": os.path.basename(caminho_arquivo),
                "data_processamento": "2025-01-14",
                "modelo_ia": "mistral-large-latest",
                "tipo_analise": "juridica_strict",
                "status_processamento": status_json
            }
        
        # Salvar JSON
        caminho_json = self.salvar_json(caminho_arquivo, dados_json)
        
        return {
            "status": "sucesso" if caminho_json else "erro_salvamento",
            "arquivo_json": caminho_json,
            "dados": dados_json
        }

# Função principal
def main():
    # Caminho para o arquivo HTML
    caminho_arquivo = "sd-data/projects/CITO/cito/poc/v01-a33/data/decisoes/adi-7200/adi-7200-14-10-2025-11-53-03.html"
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return
    
    print("Escolha o método de análise:")
    print("1 - Analisador padrão")
    print("2 - Analisador estrito (recomendado)")
    
    opcao = input("Digite 1 ou 2: ").strip()
    
    if opcao == "2":
        analisador = AnalisadorDecisoesSTFStrict("5ypcOr0mRKUCz9rdsHAp5RbYFRMoPBS6")
    else:
        analisador = AnalisadorDecisoesSTF("5ypcOr0mRKUCz9rdsHAp5RbYFRMoPBS6")
    
    # Executar análise
    resultado = analisador.executar_analise(caminho_arquivo)
    
    # Exibir resultados
    print("\n" + "="*70)
    print("RESUMO DO PROCESSAMENTO")
    print("="*70)
    
    print(f"Status: {resultado['status']}")
    print(f"Arquivo JSON: {resultado['arquivo_json']}")
    
    if resultado['status'] == 'sucesso' and isinstance(resultado['dados'], dict):
        print("\nDados extraídos (primeiros níveis):")
        for chave, valor in resultado['dados'].items():
            if chave != "_metadados":
                print(f"  {chave}: {str(valor)[:100]}...")

# Executar
if __name__ == "__main__":
    main()