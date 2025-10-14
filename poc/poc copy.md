# PROJETO CITO - RADAR DE JURISPRUDÊNCIA


# Objetivos do Projeto

Este projeto tem como objetivo principal monitorar e processar sentenças publicadas pelo Superior Tribunal Federal (STF), focando especialmente nas decisões de jurisprudência que atendam a critérios específicos.

## Funcionalidades

- **Monitoramento de Sentenças:** Acompanhar as publicações de sentenças do STF.
- **Obtenção do Inteiro Teor:** Capturar o conteúdo integral das decisões de jurisprudência.
- **Persistência em Base de Dados:** Armazenar todas as decisões coletadas em uma base de dados para consulta e análise futura.
- **Identificação de Documentos:** Detectar documentos anexos em formato PDF ou imagem, realizando extração de texto via OCR para inclusão no banco de dados.
- **Arquivamento de Arquivos Originais:** Manter e arquivar os arquivos originais e anexos no servidor, preservando o formato original.

## Processamento das Sentenças

Cada sentença coletada será analisada individualmente para classificação e identificação de informações relevantes, incluindo:

- Número do processo
- Classe da sentença:
  - ADI (Ação Direta de Inconstitucionalidade)
  - ADC (Ação Declaratória de Constitucionalidade)
  - ADPF (Arguição de Descumprimento de Preceito Fundamental)
  - ADO (Ação Direta de Inconstitucionalidade por Omissão)
- Órgão julgador
- Relator(a)
- Data do julgamento
- Data da publicação
- Envolvidos

O projeto visa garantir a integridade, organização e acessibilidade das decisões do STF, facilitando o acompanhamento 



### **1. Funcionalidades Principais**

1. **Monitoramento de Decisões do STF**


### Fontes de Jurisprudência
- Base Histórica
- Scraping retroativo
- Novas Jurisprudências
- Monitoramento e Coleta contínua

### Modelo de Dados
- Armazenamento Integral das Decisões (para evidência)
- Análise, Mineração e Extração de Dados

   * Coleta automática diária de novas publicações.
   * Identificação do inteiro teor e anexos.

2. **Gestão de Documentos Jurídicos**

   * Download e arquivamento dos originais (HTML, PDF, imagens).
   * OCR para documentos não textuais.
   * Preservação da integridade e rastreabilidade dos arquivos.

3. **Estruturação de Metadados Jurídicos**

   * Número do processo.
   * Classe da decisão (ADI, ADC, ADPF, ADO).
   * Relator(a) e órgão julgador.
   * Datas (julgamento e publicação).
   * Partes envolvidas.

4. **Extração de Citações Doutrinárias**

   * Identificação automática de autores, obras, artigos, livros.
   * Classificação da citação (corpo do texto, bibliografia, notas).
   * Normalização de dados: autor, título da obra, ano, edição, páginas.

5. **Banco de Dados Jurídico-Doutrinário**

   * Estrutura relacional para decisões, documentos, citações, obras e autores.
   * Rastreabilidade completa entre citações ↔ obras ↔ autores ↔ decisões.
   * Suporte a filtros avançados (classe, relator, período, órgão julgador).

6. **Consultas e Busca Avançada**

   * Pesquisa por processo, classe, relator, autor, obra, período.
   * Indexação full-text (ElasticSearch/OpenSearch).
   * Filtros combinados para análises jurídicas específicas.

7. **Analytics e Dashboards**

   * Evolução temporal de citações por obra/autor.
   * Ranking de autores/obras mais citados.
   * Distribuição por classe processual, relator ou órgão julgador.
   * Correlação entre tipos de ação e doutrinas mais influentes.

8. **Alertas e Integrações**

   * Notificações automáticas de novas citações/decisões.
   * API REST para integração com sistemas jurídicos externos.
   * Exportação de dados e relatórios em formatos padrão (CSV, JSON, PDF).
