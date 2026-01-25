# Projeto CITO  
**Monitoramento, Estruturação e Análise de Jurisprudência do STF**

---

## 1. Visão Geral

O **Projeto CITO** é uma plataforma de **coleta, processamento, estruturação e análise de jurisprudência do Supremo Tribunal Federal (STF)**, concebida para lidar com o alto volume, a dispersão e a complexidade dos documentos jurídicos publicados diariamente.

O sistema automatiza desde a **captura das decisões** até a **extração de metadados jurídicos estruturados**, permitindo buscas avançadas, análises históricas e geração de indicadores estratégicos. O foco principal é transformar decisões judiciais — originalmente não estruturadas — em **dados confiáveis, pesquisáveis e analíticos**, com rastreabilidade completa.

A concepção funcional e estratégica do CITO está descrita nos documentos de visão e discovery do projeto .

---

## 2. Problema que o Projeto Resolve

O ambiente jurídico brasileiro enfrenta desafios estruturais claros:

- Alto volume e dispersão das publicações do STF  
- Dificuldade de acesso sistemático ao inteiro teor das decisões  
- Falta de padronização de metadados jurídicos  
- Complexidade na identificação de citações doutrinárias  
- Ausência de mecanismos analíticos e dashboards consolidados  

O Projeto CITO atua diretamente nesses pontos, criando um **pipeline técnico confiável** para ingestão, normalização e análise dessas informações.

---

## 3. Objetivos do Sistema

- Automatizar o monitoramento contínuo da jurisprudência do STF  
- Preservar documentos originais (HTML/PDF) com rastreabilidade  
- Estruturar metadados jurídicos essenciais  
- Criar uma base integrada de decisões, autores, obras e citações  
- Permitir busca avançada e análises estatísticas  
- Servir como base para dashboards, relatórios e integrações externas  

---

## 4. Arquitetura Geral do Pipeline

O CITO adota uma arquitetura **ETL orientada a documentos**, com persistência intermediária e controle explícito de estados.

### Visão resumida do fluxo:

1. Coleta de páginas de resultado do STF  
2. Extração dos casos listados  
3. Coleta da página individual de cada decisão  
4. Sanitização do HTML relevante  
5. Processamento e extração de metadados  
6. Persistência estruturada e indexação  

Cada etapa é **idempotente**, rastreável e protegida contra concorrência indevida.

---

## 5. Estrutura do Repositório

### Arquivos principais do pipeline

#### `a_load_configs.py`
Responsável por:
- Ler configurações do sistema a partir do Google Sheets
- Normalizar valores (booleanos, inteiros, strings)
- Centralizar parâmetros operacionais (datas, flags, limites)

Função estratégica:
- Permite alterar o comportamento do pipeline **sem alteração de código**

---

#### `b_search_save_html.py`
Responsável por:
- Executar buscas no portal do STF
- Coletar o HTML bruto das páginas de resultado
- Persistir o conteúdo na coleção `raw_html`

Características:
- Usa Playwright para renderização confiável
- Armazena HTML original para auditoria e reprocessamento

---

#### `c_extract_data.py`
Responsável por:
- Consumir documentos `raw_html`
- Extrair a lista de decisões encontradas
- Criar documentos iniciais em `case_data`

Funcionalidades:
- Parsing com BeautifulSoup
- Extração de campos básicos (classe, relator, órgão, link)
- Associação entre resultado e documento de origem

Controle de concorrência:
- Implementa **lock atômico** (`new → extracting → extracted`)

---

#### `e_fetch_case_html.py`
Responsável por:
- Acessar a página individual de cada decisão
- Coletar o HTML completo do caso
- Persistir em `caseHtml`

Funcionalidades:
- Playwright (com fallback opcional via requests)
- Tratamento de erros de navegação
- Registro de timestamps e falhas

Controle de concorrência:
- Lock atômico (`extracted → caseScraping → caseScraped`)

---

#### `f_sanitize_case_html.py`
Responsável por:
- Isolar apenas o trecho relevante do HTML do caso
- Eliminar navegação, menus e ruído visual
- Gerar `caseHtmlSanitized`

Técnica:
- XPath com lxml
- Sanitização determinística

Controle de concorrência:
- Lock atômico (`caseScraped → caseSanitizing → caseSanitized`)

---

#### `g_process_case_html_sanitized.py`
Responsável por:
- Extrair metadados jurídicos detalhados
- Identificar blocos textuais relevantes
- Normalizar campos e remover dados vazios

Exemplos de dados extraídos:
- Número do processo
- Classe processual
- Relator
- Órgão julgador
- Datas
- Seções textuais (ementa, partes, publicações)

Controle de concorrência:
- Lock atômico (`caseSanitized → caseProcessing → caseHtmlProcessed`)

---

## 6. Modelo de Dados (Visão Lógica)

### Coleções principais

#### `raw_html`
- HTML bruto da busca
- Controle de status e origem

#### `case_data`
Documento central do sistema:
- Metadados da decisão
- HTML coletado
- HTML sanitizado
- Dados processados
- Histórico de status e erros

### Conceitualmente, o modelo suporta:
- Decisão
- Processo
- Classe
- Relator
- Órgão julgador
- (Futuro) Citação → Obra → Autor

---

## 7. Controle de Status e Lock Atômico

O pipeline utiliza **transições explícitas de status**, sempre realizadas de forma atômica no MongoDB, evitando que múltiplos workers processem o mesmo documento.

Exemplo de transição:

```

caseSanitized
↓ (claim atômico)
caseProcessing
↓ (sucesso)
caseHtmlProcessed

```

Benefícios:
- Execução paralela segura
- Reprocessamento controlado
- Rastreabilidade completa
- Redução de inconsistências

---

## 8. Escopo do MVP

- Coleta retroativa de decisões (últimos 6 meses)
- Extração de metadados essenciais
- Consulta por processo e relator
- Dashboard mínimo com:
  - Volume por classe processual
  - Ranking de relatores
- Base técnica preparada para NLP e citações doutrinárias

---

## 9. Roadmap Evolutivo

- **Fase 0**: Setup técnico e infraestrutura  
- **Fase 1**: MVP com pipeline ETL e dashboards básicos  
- **Fase 2**: NLP e normalização avançada de citações  
- **Fase 3**: Expansão para outros tribunais  

---

## 10. Conclusão

O Projeto CITO estabelece uma base sólida para **transformar jurisprudência em dados estruturados e analisáveis**, combinando engenharia de dados, rastreabilidade documental e visão jurídica. Sua arquitetura modular, orientada a etapas e protegida por locks atômicos, permite evolução incremental com segurança técnica e clareza operacional.

Este repositório representa o **núcleo técnico do pipeline**, preparado para escalar funcionalmente e integrar camadas analíticas mais avançadas no futuro.
