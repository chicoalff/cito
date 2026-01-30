import os
import json
import re
from bs4 import BeautifulSoup
from mistralai import Mistral
import warnings

warnings.filterwarnings('ignore')

class AnalisadorCOTSTF:
    def __init__(self, api_key):
        self.client = Mistral(api_key=api_key)
        self.texto_original = None
        self.resultados_parciais = {}
    
    def carregar_e_processar_html(self, caminho_arquivo):
        """Carrega e processa o arquivo HTML"""
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extrair texto completo
            texto_completo = soup.get_text()
            
            # Limpar texto
            lines = (line.strip() for line in texto_completo.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            texto_limpo = ' '.join(chunk for chunk in chunks if chunk)
            
            self.texto_original = texto_limpo
            print(f"✅ Texto carregado: {len(texto_limpo)} caracteres")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar HTML: {e}")
            return False
    
    def executar_passo_cot(self, passo, prompt, max_tokens=2000):
        """Executa um passo individual da chain of thought"""
        print(f"🔄 Executando passo: {passo}")
        
        try:
            resposta = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            # Limpar resposta
            resposta_limpa = resposta.choices[0].message.content.strip()
            resposta_limpa = re.sub(r'^```json\s*', '', resposta_limpa)
            resposta_limpa = re.sub(r'\s*```$', '', resposta_limpa)
            
            # Tentar parsear JSON
            try:
                dados_json = json.loads(resposta_limpa)
                self.resultados_parciais[passo] = dados_json
                print(f"✅ {passo} - Concluído")
                return dados_json
            except json.JSONDecodeError:
                print(f"⚠️ {passo} - JSON inválido, salvando como texto")
                self.resultados_parciais[passo] = {"resposta_bruta": resposta_limpa}
                return {"resposta_bruta": resposta_limpa}
                
        except Exception as e:
            print(f"❌ Erro no passo {passo}: {e}")
            self.resultados_parciais[passo] = {"erro": str(e)}
            return {"erro": str(e)}
    
    def passo_1_identificacao_processo(self):
        """Passo 1: Identificação básica do processo"""
        prompt = f"""
        PRIMEIRO PASSO - IDENTIFICAÇÃO DO PROCESSO
        
        Analise o texto abaixo e identifique as informações básicas do processo:
        
        {self.texto_original[:3000]}
        
        Extraia APENAS:
        {{
            "identificacao_processo": {{
                "numero_completo": "texto",
                "classe_processual": "texto (ex: ADI, ADC, etc)",
                "assunto_principal": "texto resumido"
            }},
            "partes_principais": {{
                "autor_requerente": "nome completo",
                "reus_principais": ["nome1", "nome2"]
            }},
            "relator": "nome completo",
            "orgao_julgador": "texto"
        }}
        
        Retorne APENAS JSON.
        """
        
        return self.executar_passo_cot("01_identificacao_processo", prompt)
    
    def passo_2_extrair_todas_partes(self):
        """Passo 2: Extração detalhada de TODAS as partes"""
        prompt = f"""
        SEGUNDO PASSO - EXTRAÇÃO COMPLETA DE PARTES
        
        Com base no texto completo, extraia TODAS as partes, entidades, intervenientes e representantes:
        
        {self.texto_original[:5000]}
        
        Liste CADA PARTE individualmente. NÃO OMITA NINGUÉM.
        
        {{
            "partes_detalhadas": {{
                "autores_requerentes": [
                    {{
                        "nome_completo": "texto",
                        "qualificacao": "texto",
                        "papel_processual": "texto"
                    }}
                ],
                "requeridos_resistentes": [
                    {{
                        "nome_completo": "texto",
                        "cargo_funcao": "texto", 
                        "representacao": "texto"
                    }}
                ],
                "intervenientes_amicus_curiae": [
                    {{
                        "nome_entidade": "texto",
                        "sigla": "texto se houver",
                        "tipo_intervencao": "texto",
                        "posicionamento": "texto"
                    }}
                ],
                "advogados_procuradores": [
                    {{
                        "nome": "texto",
                        "parte_representada": "texto",
                        "qualificacao": "texto"
                    }}
                ],
                "entidades_organizacoes": [
                    {{
                        "nome": "texto completo",
                        "tipo": "partido/associação/órgão"
                    }}
                ]
            }},
            "contagem_total": {{
                "total_autores": "número",
                "total_requeridos": "número",
                "total_intervenientes": "número",
                "total_advogados": "número",
                "total_entidades": "número"
            }}
        }}
        
        IMPORTANTE: Inclua TODAS as partes, mesmo que sejam dezenas.
        Retorne APENAS JSON.
        """
        
        return self.executar_passo_cot("02_partes_detalhadas", prompt, max_tokens=3000)
    
    def passo_3_datas_prazos(self):
        """Passo 3: Datas e prazos importantes"""
        prompt = f"""
        TERCEIRO PASSO - LINHA DO TEMPO
        
        Extraia todas as datas importantes do processo:
        
        {self.texto_original[:4000]}
        
        {{
            "cronologia_processo": {{
                "data_distribuicao": "texto",
                "data_relatoramento": "texto", 
                "data_julgamento": "texto",
                "data_publicacao": "texto",
                "outras_datas_importantes": [
                    {{
                        "evento": "texto",
                        "data": "texto"
                    }}
                ]
            }},
            "prazos_vencimentos": [
                {{
                    "tipo_prazo": "texto",
                    "prazo": "texto",
                    "status": "cumprido/vencido"
                }}
            ]
        }}
        
        Retorne APENAS JSON.
        """
        
        return self.executar_passo_cot("03_datas_cronologia", prompt)
    
    def passo_4_decisao_resultado(self):
        """Passo 4: Análise da decisão e resultado"""
        prompt = f"""
        QUARTO PASSO - ANÁLISE DA DECISÃO
        
        Analise o resultado e a decisão do processo:
        
        {self.texto_original[:4000]}
        
        {{
            "decisao_final": {{
                "resultado": "texto detalhado",
                "tese_principal": "texto completo",
                "unanimidade_ou_maioria": "texto",
                "acordao": "texto se disponível"
            }},
            "votacao_ministros": [
                {{
                    "ministro": "nome",
                    "voto": "resumo completo",
                    "decisao": "favorável/contrário",
                    "fundamentacao_principal": "texto"
                }}
            ],
            "medidas_decretadas": [
                {{
                    "tipo_medida": "texto",
                    "descricao": "texto",
                    "alcance": "texto"
                }}
            ]
        }}
        
        Retorne APENAS JSON.
        """
        
        return self.executar_passo_cot("04_decisao_resultado", prompt, max_tokens=2500)
    
    def passo_5_fundamentos_juridicos(self):
        """Passo 5: Fundamentos jurídicos e base legal"""
        prompt = f"""
        QUINTO PASSO - FUNDAMENTOS JURÍDICOS
        
        Extraia a base legal e fundamentação jurídica:
        
        {self.texto_original[:5000]}
        
        {{
            "fundamentacao_completa": {{
                "inconstitucionalidades_apontadas": [
                    {{
                        "tipo": "formal/material",
                        "descricao_detalhada": "texto",
                        "artigos_cf_afetados": ["artigo1", "artigo2"]
                    }}
                ],
                "principais_argumentos": [
                    "texto completo do argumento 1",
                    "texto completo do argumento 2"
                ],
                "base_legal_citada": [
                    {{
                        "dispositivo_legal": "ex: Art. 1º da CF/88",
                        "conteudo_relevante": "texto da aplicação"
                    }}
                ],
                "precedentes_jurisprudenciais": [
                    {{
                        "processo_precedente": "número",
                        "tribunal": "texto",
                        "aplicacao_no_caso": "texto"
                    }}
                ]
            }},
            "efeitos_da_decisao": {{
                "eficacia": "texto",
                "alcance": "texto",
                "modulacao_efeitos": "texto se houver"
            }}
        }}
        
        Retorne APENAS JSON.
        """
        
        return self.executar_passo_cot("05_fundamentos_juridicos", prompt, max_tokens=3000)
    
    def passo_6_ementa_indexacao(self):
        """Passo 6: Ementa e indexação"""
        prompt = f"""
        SEXTO PASSO - EMENTA E INDEXAÇÃO
        
        Extraia a ementa e informações de indexação:
        
        {self.texto_original[:3000]}
        
        {{
            "ementa_completa": "texto completo da ementa",
            "indexacao_tematicas": {{
                "temas_principais": ["tema1", "tema2", "tema3"],
                "palavras_chave": ["palavra1", "palavra2", "palavra3"],
                "repercussao_geral": "texto se houver",
                "tese_repercussao": "texto se houver"
            }},
            "informacoes_complementares": {{
                "valor_causa": "texto se houver",
                "segredo_justica": "sim/não",
                "urgência": "sim/não"
            }}
        }}
        
        Retorne APENAS JSON.
        """
        
        return self.executar_passo_cot("06_ementa_indexacao", prompt)
    
    def passo_7_consolidacao_final(self):
        """Passo 7: Consolidação final de todos os dados"""
        print("🔄 Consolidando dados de todos os passos...")
        
        dados_consolidados = {
            "processo_consolidado": {
                "identificacao": self.resultados_parciais.get("01_identificacao_processo", {}),
                "partes": self.resultados_parciais.get("02_partes_detalhadas", {}),
                "cronologia": self.resultados_parciais.get("03_datas_cronologia", {}),
                "decisao": self.resultados_parciais.get("04_decisao_resultado", {}),
                "fundamentos": self.resultados_parciais.get("05_fundamentos_juridicos", {}),
                "ementa_indexacao": self.resultados_parciais.get("06_ementa_indexacao", {})
            },
            "metadados_analise": {
                "total_passos_executados": len(self.resultados_parciais),
                "passos_com_sucesso": sum(1 for passo in self.resultados_parciais.values() 
                                        if not passo.get('erro') and not passo.get('resposta_bruta')),
                "timestamp_processamento": "2025-01-14",
                "estrategia_utilizada": "Chain of Thought (COT) - 7 passos"
            }
        }
        
        # Adicionar estatísticas de partes
        if "02_partes_detalhadas" in self.resultados_parciais:
            partes = self.resultados_parciais["02_partes_detalhadas"].get("partes_detalhadas", {})
            totais = self.resultados_parciais["02_partes_detalhadas"].get("contagem_total", {})
            
            dados_consolidados["estatisticas_partes"] = {
                "autores": len(partes.get("autores_requerentes", [])),
                "requeridos": len(partes.get("requeridos_resistentes", [])),
                "intervenientes": len(partes.get("intervenientes_amicus_curiae", [])),
                "advogados": len(partes.get("advogados_procuradores", [])),
                "entidades": len(partes.get("entidades_organizacoes", [])),
                "totais_extraidos": totais
            }
        
        return dados_consolidados
    
    def executar_chain_of_thought(self, caminho_arquivo):
        """Executa toda a chain of thought sequencialmente"""
        print("🚀 INICIANDO CHAIN OF THOUGHT (COT)")
        print("=" * 60)
        
        # Carregar arquivo
        if not self.carregar_e_processar_html(caminho_arquivo):
            return {"erro": "Falha ao carregar arquivo"}
        
        # Executar passos sequenciais
        passos = [
            self.passo_1_identificacao_processo,
            self.passo_2_extrair_todas_partes,
            self.passo_3_datas_prazos,
            self.passo_4_decisao_resultado,
            self.passo_5_fundamentos_juridicos,
            self.passo_6_ementa_indexacao
        ]
        
        for passo in passos:
            passo()
        
        # Consolidar resultados
        resultado_final = self.passo_7_consolidacao_final()
        
        return resultado_final
    
    def salvar_resultados(self, caminho_arquivo_html, dados_consolidados):
        """Salva os resultados consolidados"""
        try:
            diretorio = os.path.dirname(caminho_arquivo_html)
            nome_arquivo = os.path.basename(caminho_arquivo_html)
            nome_json = nome_arquivo.replace('.html', '_COT.json')
            caminho_json = os.path.join(diretorio, nome_json)
            
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados_consolidados, f, indent=2, ensure_ascii=False)
            
            print(f"✅ JSON consolidado salvo: {caminho_json}")
            
            # Também salvar resultados parciais para debug
            caminho_parciais = caminho_json.replace('_COT.json', '_COT_parciais.json')
            with open(caminho_parciais, 'w', encoding='utf-8') as f:
                json.dump(self.resultados_parciais, f, indent=2, ensure_ascii=False)
            
            return caminho_json
            
        except Exception as e:
            print(f"❌ Erro ao salvar JSON: {e}")
            return None

# Função principal
def main():
    # Caminho para o arquivo HTML
    caminho_arquivo = "sd-data/projects/CITO/cito/poc/v01-a33/data/decisoes/adi-7200/adi-7200-14-10-2025-11-53-03.html"
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return
    
    print("🎯 ANALISADOR COT - STF")
    print("📋 Estratégia: Chain of Thought com 7 passos sequenciais")
    print("⏳ Iniciando processamento...\n")
    
    # Inicializar analisador
    analisador = AnalisadorCOTSTF("5ypcOr0mRKUCz9rdsHAp5RbYFRMoPBS6")
    
    # Executar chain of thought
    resultado = analisador.executar_chain_of_thought(caminho_arquivo)
    
    # Salvar resultados
    if "erro" not in resultado:
        caminho_json = analisador.salvar_resultados(caminho_arquivo, resultado)
        
        # Exibir resumo
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO FINAL - CHAIN OF THOUGHT")
        print("=" * 80)
        
        metadados = resultado.get("metadados_analise", {})
        print(f"✅ Passos executados: {metadados.get('total_passos_executados', 0)}")
        print(f"✅ Passos com sucesso: {metadados.get('passos_com_sucesso', 0)}")
        
        # Estatísticas de partes
        if "estatisticas_partes" in resultado:
            stats = resultado["estatisticas_partes"]
            print(f"👥 PARTES EXTRAÍDAS:")
            print(f"   • Autores/Requerentes: {stats.get('autores', 0)}")
            print(f"   • Requeridos/Rés: {stats.get('requeridos', 0)}")
            print(f"   • Intervenientes: {stats.get('intervenientes', 0)}")
            print(f"   • Advogados: {stats.get('advogados', 0)}")
            print(f"   • Entidades: {stats.get('entidades', 0)}")
            print(f"   📈 TOTAL: {sum([stats.get(k, 0) for k in ['autores', 'requeridos', 'intervenientes', 'advogados', 'entidades']])}")
        
        print(f"💾 Arquivo salvo: {caminho_json}")
        
    else:
        print(f"❌ Processamento falhou: {resultado['erro']}")

# Executar
if __name__ == "__main__":
    main()