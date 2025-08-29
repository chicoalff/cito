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

O projeto visa garantir a integridade, organização e acessibilidade das decisões do STF, facilitando o acompanhamento e