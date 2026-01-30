import os
import json
import re
from bs4 import BeautifulSoup
from mistralai import Mistral
import warnings

warnings.filterwarnings('ignore')

class AnalisadorDecisoesSTFCompleto:
    def __init__(self, api_key):
        self.client = Mistral(api_key=api_key)
    
    def processar_decisao_html(self, caminho_arquivo):
        """Processa especificamente decisões do STF mantendo mais conteúdo"""
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extrair texto completo sem muitas limitações
            texto_completo = soup.get_text()
            
            # Limpar texto mas manter conteúdo
            lines = (line.strip() for line in texto_completo.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            texto_limpo = ' '.join(chunk for chunk in chunks if chunk)
            
            print(f"Texto extraído: {len(texto_limpo)} caracteres")
            return texto_limpo[:8000]  # Aumentei o limite para capturar mais informações
            
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def analisar_decisao_completa(self, texto):
        """Análise especializada que extrai TODAS as informações"""
        prompt = f"""
        ANALISE JURÍDICA COMPLETA - STF

        CONTEÚDO PARA ANÁLISE:
        {texto}

        EXTRAIA TODAS AS INFORMAÇÕES DISPONÍVEIS EM FORMATO JSON:

        {{
            "processo": {{
                "numero": "texto completo",
                "tipo": "texto",
                "classe_processual": "texto"
            }},
            "partes_envolvidas": {{
                "autor": {{
                    "nome": "texto",
                    "tipo": "partido político/estado/etc"
                }},
                "requerente": "texto se diferente do autor",
                "requeridos": [
                    {{
                        "nome": "texto completo",
                        "cargo_ou_funcao": "texto"
                    }}
                ],
                "intervenientes_amicus_curiae": [
                    {{
                        "nome": "texto completo",
                        "tipo": "organização/entidade"
                    }}
                ],
                "impulsionadores": [
                    {{
                        "nome": "texto completo",
                        "funcao": "texto"
                    }}
                ]
            }},
            "relatoria": {{
                "relator": "nome completo",
                "presidente": "nome se houver",
                "orgao_julgador": "texto"
            }},
            "datas_importantes": {{
                "data_julgamento": "texto",
                "data_publicacao": "texto",
                "data_registro": "texto"
            }},
            "decisao": {{
                "resultado": "texto detalhado",
                "tese_principal": "texto completo",
                "decisao_monocratica": "texto se houver",
                "acordao": "texto",
                "votos": [
                    {{
                        "ministro": "nome",
                        "voto": "resumo completo",
                        "posicionamento": "favorável/contrário"
                    }}
                ]
            }},
            "fundamentos_juridicos": {{
                "inconstitucionalidades_apontadas": [
                    {{
                        "tipo": "formal/material",
                        "descricao": "texto detalhado",
                        "artigos_cf": ["artigos"]
                    }}
                ],
                "principais_argumentos": [
                    "texto completo do argumento 1",
                    "texto completo do argumento 2"
                ],
                "base_legal_citada": [
                    {{
                        "dispositivo": "ex: Art. 1º da CF",
                        "descricao": "texto da citação"
                    }}
                ],
                "precedentes_citados": [
                    {{
                        "processo": "número",
                        "tema": "texto"
                    }}
                ]
            }},
            "ementa": "texto completo da ementa",
            "indexacao": {{
                "temas_principais": ["tema1", "tema2"],
                "palavras_chave": ["palavra1", "palavra2"],
                "repercussao_geral": "texto se houver"
            }},
            "andamento_processual": {{
                "fase_atual": "texto",
                "despachos_importantes": ["texto1", "texto2"],
                "medidas_cautelares": "texto se houver"
            }}
        }}

        REGRAS CRÍTICAS:
        1. EXTRAIA TODAS AS PARTES ENVOLVIDAS - não limite a apenas 3 ou 4
        2. Se houver dezenas de partes, inclua TODAS
        3. Mantenha os textos COMPLETOS, não resumidos
        4. Para arrays, inclua TODOS os itens encontrados
        5. Se uma informação se repetir em formatos diferentes, inclua todas as versões
        6. Prefira incluir informação redundante a omitir informação importante

        Retorne APENAS o JSON válido, sem nenhum texto adicional.
        """
        
        try:
            resposta = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,  # Aumentei tokens para respostas maiores
                temperature=0.1
            )
            
            # Limpar resposta
            resposta_limpa = resposta.choices[0].message.content.strip()
            resposta_limpa = re.sub(r'^```json\s*', '', resposta_limpa)
            resposta_limpa = re.sub(r'\s*```$', '', resposta_limpa)
            
            return resposta_limpa
            
        except Exception as e:
            return f"Erro: {e}"
    
    def processar_partes_detalhadas(self, texto):
        """Processamento específico para extrair TODAS as partes"""
        prompt_parts = f"""
        EXTRAÇÃO DETALHADA DE PARTES ENVOLVIDAS

        Conteúdo:
        {texto[:6000]}

        Sua tarefa é EXTRAIR TODAS AS PARTES, INTERVENIENTES, ASSISTENTES, AMICUS CURIAE 
        e qualquer pessoa ou entidade mencionada no processo.

        Retorne APENAS um JSON com esta estrutura:

        {{
            "partes_completas": {{
                "autores_requerentes": [
                    {{
                        "nome": "nome completo",
                        "qualificacao": "tipo/qualificação",
                        "papel": "autor/requerente/etc"
                    }}
                ],
                "requeridos_resistentes": [
                    {{
                        "nome": "nome completo", 
                        "qualificacao": "cargo/função",
                        "papel": "réu/requerido/etc"
                    }}
                ],
                "intervenientes_atores": [
                    {{
                        "nome": "nome completo",
                        "tipo_intervencao": "adhoc/amicus/etc",
                        "posicionamento": "favorável/contrário"
                    }}
                ],
                "advogados_procuradores": [
                    {{
                        "nome": "nome completo",
                        "parte_representada": "nome da parte",
                        "qualificacao": "advogado/procurador"
                    }}
                ],
                "entidades_organizacoes": [
                    {{
                        "nome": "nome completo",
                        "sigla": "se houver",
                        "tipo": "partido/associação/órgão"
                    }}
                ]
            }},
            "total_partes_autores": "número",
            "total_partes_requeridos": "número", 
            "total_intervenientes": "número"
        }}

        IMPORTANTE: 
        - Liste TODAS as partes, mesmo que sejam dezenas
        - Não resuma, não agrupe, não omita
        - Inclua cada parte individualmente
        - Mantenha os nomes completos como aparecem no texto
        """
        
        try:
            resposta = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt_parts}],
                max_tokens=3000,
                temperature=0.1
            )
            
            resposta_limpa = resposta.choices[0].message.content.strip()
            resposta_limpa = re.sub(r'^```json\s*', '', resposta_limpa)
            resposta_limpa = re.sub(r'\s*```$', '', resposta_limpa)
            
            return resposta_limpa
            
        except Exception as e:
            return f"Erro partes: {e}"
    
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
    
    def executar_analise_completa(self, caminho_arquivo):
        """Executa análise completa com extração detalhada"""
        print(f"Analisando COMPLETAMENTE: {os.path.basename(caminho_arquivo)}")
        
        texto = self.processar_decisao_html(caminho_arquivo)
        if not texto:
            return {"erro": "Falha ao processar arquivo"}
        
        print("Extraindo informações principais...")
        resultado_principal = self.analisar_decisao_completa(texto)
        
        print("Extraindo partes envolvidas detalhadamente...")
        resultado_partes = self.processar_partes_detalhadas(texto)
        
        # Processar resultados
        dados_finais = {}
        
        # Processar análise principal
        try:
            dados_principal = json.loads(resultado_principal)
            dados_finais.update(dados_principal)
            status_principal = "sucesso"
        except json.JSONDecodeError as e:
            print(f"Erro no JSON principal: {e}")
            dados_finais["analise_principal_erro"] = resultado_principal
            status_principal = "erro"
        
        # Processar partes detalhadas
        try:
            dados_partes = json.loads(resultado_partes)
            dados_finais["partes_detalhadas"] = dados_partes
            status_partes = "sucesso"
        except json.JSONDecodeError as e:
            print(f"Erro no JSON partes: {e}")
            dados_finais["partes_detalhadas_erro"] = resultado_partes
            status_partes = "erro"
        
        # Adicionar metadados
        dados_finais["_metadados"] = {
            "arquivo_origem": os.path.basename(caminho_arquivo),
            "data_processamento": "2025-01-14",
            "modelo_ia": "mistral-large-latest",
            "tipo_analise": "completa_detalhada",
            "status_analise_principal": status_principal,
            "status_analise_partes": status_partes,
            "tamanho_texto_analisado": len(texto)
        }
        
        # Salvar JSON
        caminho_json = self.salvar_json(caminho_arquivo, dados_finais)
        
        # Estatísticas
        if status_principal == "sucesso" and status_partes == "sucesso":
            total_partes = 0
            if "partes_detalhadas" in dados_finais:
                partes = dados_finais["partes_detalhadas"].get("partes_completas", {})
                total_partes = sum(len(partes.get(key, [])) for key in partes)
            
            print(f"\n✅ Análise completa concluída!")
            print(f"📊 Total de partes extraídas: {total_partes}")
        
        return {
            "status": "sucesso" if caminho_json else "erro_salvamento",
            "arquivo_json": caminho_json,
            "dados": dados_finais
        }

# Função principal
def main():
    # Caminho para o arquivo HTML
    caminho_arquivo = "sd-data/projects/CITO/cito/poc/v01-a33/data/decisoes/adi-7200/adi-7200-14-10-2025-11-53-03.html"
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return
    
    print("🚀 INICIANDO ANÁLISE COMPLETA DO PROCESSO")
    print("📋 Este processo fará duas extrações:")
    print("   1. Análise jurídica completa")
    print("   2. Extração detalhada de TODAS as partes")
    print("⏳ Isso pode levar alguns segundos...\n")
    
    analisador = AnalisadorDecisoesSTFCompleto("5ypcOr0mRKUCz9rdsHAp5RbYFRMoPBS6")
    
    # Executar análise completa
    resultado = analisador.executar_analise_completa(caminho_arquivo)
    
    # Exibir resultados
    print("\n" + "="*80)
    print("RESUMO FINAL DO PROCESSAMENTO")
    print("="*80)
    
    print(f"📁 Arquivo processado: {os.path.basename(caminho_arquivo)}")
    print(f"✅ Status geral: {resultado['status']}")
    print(f"💾 JSON salvo em: {resultado['arquivo_json']}")
    
    if resultado['status'] == 'sucesso' and isinstance(resultado['dados'], dict):
        dados = resultado['dados']
        metadados = dados.get('_metadados', {})
        
        print(f"📊 Status análise principal: {metadados.get('status_analise_principal', 'N/A')}")
        print(f"📊 Status análise partes: {metadados.get('status_analise_partes', 'N/A')}")
        
        # Mostrar estatísticas de partes
        if 'partes_detalhadas' in dados:
            partes = dados['partes_detalhadas'].get('partes_completas', {})
            totais = {
                'autores': len(partes.get('autores_requerentes', [])),
                'requeridos': len(partes.get('requeridos_resistentes', [])),
                'intervenientes': len(partes.get('intervenientes_atores', [])),
                'advogados': len(partes.get('advogados_procuradores', [])),
                'entidades': len(partes.get('entidades_organizacoes', []))
            }
            
            print(f"👥 ESTATÍSTICAS DE PARTES:")
            for tipo, quantidade in totais.items():
                print(f"   {tipo.capitalize()}: {quantidade}")
            print(f"   TOTAL GERAL: {sum(totais.values())}")

# Executar
if __name__ == "__main__":
    main()