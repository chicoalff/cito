
Hoje o script realiza primeiro o processamento e extração das  doutrinas de todos os processos, para somente então realizar a extração das citações de legislação.

Altere o script, para que o processamento realize a extração das doutrinas e da legislação de cada processo.

Exemplo de fluxo:
- Iniciar processamento do processo x
    - Informar usuário: "Iniciando extração de doutrinas e legislações do processo xxx..."
- Obter conteúdo rawDoctrine do processo x
- Solicitar a API Mistral que identifique e extraia as doutrinas existentes no conteúdo rawDoctrine.
- Receber resposta, realizar validações e inserir os itens identificados no documento
- Obter conteúdo rawLegislation do processo x
- Solicitar a API Mistral que identifique e extraia as legislações existentes no conteúdo rawLegislation.
- Receber resposta, realizar validações e inserir os itens identificados no documento

- informar usuário dos resultados da extração do processo: 
    "   Total de doutrinas extraídas: xx. 
        Total de legislações extraídas: yy.
        Processamento do item xxx finalizado com sucesso. 
    "
Continuar fluxo de extração para o próximo processo. (conforme preferencia do usuário: todos os processos ou confirmação individual)


# ANALISAR E EXTRAIR DOUTRINAS CITADAS NOS PROCESSOS

Utilizar modelo de IA Mistral via API para analisar o conteúdo da seção "Doutrinas" de cada processo.

## ETAPA 1: EXTRAIR DOUTRINAS COM API IA MISTRAL

1. Consultar na collection `case_data` do MongoDB todos os documentos com status do pipeline `"htmlFetched"`.
    - 1.1. Informar ao usuário a quantidade de documentos encontrados.

2. Solicitar ao usuário se deseja prosseguir com o processamento de todos os documentos ou se deseja confirmar individualmente cada documento antes de processá-lo.

3. Para cada documento confirmado pelo usuário, obter o conteúdo do campo `rawData.rawDoctrine`.

4. Iniciar uma nova requisição à API Mistral, enviando o system prompt e o user prompt com o conteúdo extraído do campo `rawData.rawDoctrine`.
    - **4.1. System Prompt:**
      ```
      # SYSTEM PROMPT — Extração de Doutrina (Mistral, token-efficient)
      
      Você é um **extrator de referências doutrinárias jurídicas** em português (padrão ABNT aproximado).
      
      ## Tarefa
      Identificar **cada citação individual** em um texto e extrair dados estruturados para `caseData.caseDoctrineReferences`.
      
      ## Segmentação
      - Uma citação pode estar em uma linha ou colada a outra na mesma linha.
      - **Não use vírgulas** como separador de citações.
      - Nova citação normalmente inicia por `SOBRENOME, Nome.`.
      - Após `ano.` ou `p. ...`, se surgir novo padrão `SOBRENOME, Nome.`, iniciar nova citação.
      
      ## Regras
      - Não inventar dados.
      - Campos ausentes → `null`.
      - `year`: inteiro (4 dígitos) ou `null`.
      - `edition`: normalizar para `"X ed"`.
      - `page`: string (ex.: `"181"`, `"233-234"`, `"233-234 e 1.561"`).
      - Múltiplos autores: usar **apenas o primeiro** em `author`.
      - `rawCitation`: citação completa, preservando o texto original.
      
      ## Campos por item
      - `author`
      - `publicationTitle`
      - `edition`
      - `publicationPlace`
      - `publisher`
      - `year`
      - `page`
      - `rawCitation`
      
      ## Exemplo
      
      **Entrada:**
      ```
      ALEXY, Robert. Teoria dos direitos fundamentais. 2. ed. Trad. Virgílio Afonso da Silva. São Paulo: Malheiros, 2015, p. 582.  
      CANOTILHO, José Joaquim Gomes. Direito constitucional. 6. ed. Coimbra: Almedina, 1993, p. 139.
      ```
      
      **Saída esperada:**
      ```json
      {
         "caseData": {
            "caseDoctrineReferences": [
              {
                 "author": "ALEXY, Robert",
                 "publicationTitle": "Teoria dos direitos fundamentais",
                 "edition": "2 ed",
                 "publicationPlace": "São Paulo",
                 "publisher": "Malheiros",
                 "year": 2015,
                 "page": "582",
                 "rawCitation": "ALEXY, Robert. Teoria dos direitos fundamentais. 2. ed. Trad. Virgílio Afonso da Silva. São Paulo: Malheiros, 2015, p. 582."
              },
              {
                 "author": "CANOTILHO, José Joaquim Gomes",
                 "publicationTitle": "Direito constitucional",
                 "edition": "6 ed",
                 "publicationPlace": "Coimbra",
                 "publisher": "Almedina",
                 "year": 1993,
                 "page": "139",
                 "rawCitation": "CANOTILHO, José Joaquim Gomes. Direito constitucional. 6. ed. Coimbra: Almedina, 1993, p. 139."
              }
            ]
         }
      }
      ```
      ```

    - **4.2. User Prompt:**
      ```
      # USER MESSAGE — Extração de Doutrina
      
      Extraia as referências doutrinárias do texto abaixo e retorne **apenas JSON válido**, conforme definido no SYSTEM PROMPT.
      
      [conteúdo do campo 'rawData.rawDoctrine']
      
      ## Saída obrigatória
      Retornar **somente JSON válido**, exatamente na estrutura acima.  
      Não incluir markdown, comentários ou texto adicional.
      ```

5. Receber a resposta da API Mistral, validar se o JSON retornado está correto e em conformidade com o schema esperado.

6. Atualizar o documento na collection `case_data`, salvando os dados extraídos em `caseData.caseDoctrineReferences`.
    - 6.1. Cada citação deve ser salva como um objeto dentro de uma lista em `caseData.caseDoctrineReferences`.

7. Atualizar o status do pipeline para `"doctrineExtracted"` e registrar a data/hora da extração em `processing.caseDoctrineRefsAt`.

---

## ETAPA 2: EXTRAIR DADOS DE LEGISLAÇÃO CITADA

Incluir no script uma nova funcionalidade para extrair referências legislativas citadas nos processos, utilizando o modelo de IA Mistral via API.

1. Consultar na collection `case_data` do MongoDB todos os documentos com status do pipeline `"doctrineExtracted"`.
    - 1.1. Informar ao usuário a quantidade de documentos encontrados.

2. Solicitar ao usuário se deseja prosseguir com o processamento de todos os documentos ou se deseja confirmar individualmente cada documento antes de processá-lo.

3. Para cada documento confirmado pelo usuário, obter o conteúdo do campo `rawData.rawLegislation`.

4. Iniciar uma nova requisição à API Mistral, enviando o system prompt e o user prompt com o conteúdo extraído do campo `rawData.rawLegislation`.
    - **4.1. System Prompt:**
      ```
      # SYSTEM — CITO | Legislação → JSON
      
      **Tarefa:** extrair referências legislativas de texto jurídico (PT-BR) e retornar SOMENTE JSON válido.
      
      ## Estrutura de Saída
      ```json
      {
         "caseLegislationReferences": [
            {
              "jurisdictionLevel": "federal|state|municipal|unknown",
              "normType": "CF|EC|LC|LEI|DECRETO|RESOLUÇÃO|PORTARIA|OUTRA",
              "normIdentifier": "string",
              "normYear": 0,
              "normDescription": "string",
              "normReferences": [
                 {
                    "articleNumber": 0,
                    "isCaput": true,
                    "incisoNumber": 0,
                    "paragraphNumber": 0,
                    "isParagraphSingle": false,
                    "letterCode": "a"
                 }
              ]
            }
         ]
      }
      ```
      
      ## Regras
      - Responder apenas com JSON (sem markdown/texto).
      - Agrupar por norma; deduplicar normas e dispositivos.
      - Permitir múltiplas normas e dispositivos.
      
      ## Normalização
      - `articleNumber`: inteiro de "art./artigo".
      - `isCaput`: true se "caput" OU se apenas "art. X" (sem inciso/parágrafo/alínea).
      - `incisoNumber`: romano → inteiro; ausente = null.
      - `paragraphNumber`: "§ nº" → inteiro; ausente = null.
      - `isParagraphSingle`: true se "parágrafo único".
      - `letterCode`: "alínea a / a)" → "a"; ausente = null.
      
      ## Identificação de Normas
      - `normIdentifier`: CF-1988; EC-n-ano; LC-n-ano; LEI-n-ano; DECRETO-n-ano (remover ponto do número).
      - `normYear`: inteiro; ausente = 0.
      - `normDescription`: nome curto se explícito; senão "".
      - `jurisdictionLevel`: inferir; senão "unknown".
      
      ## Caso-limite
      Norma sem dispositivo explícito: `normReferences` com um item:
      ```json
      {"articleNumber": null, "isCaput": false, "incisoNumber": null, "paragraphNumber": null, "isParagraphSingle": false, "letterCode": null}
      ```
      
      ## Exemplo
      
      **Texto:**
      ```
      CF/88, art. 5º, caput, inc. III; Lei 8.112/1990 (RJU), art. 1º, parágrafo único, alínea a.
      ```
      
      **Saída:**
      ```json
      {
         "caseLegislationReferences": [
            {
              "jurisdictionLevel": "federal",
              "normType": "CF",
              "normIdentifier": "CF-1988",
              "normYear": 1988,
              "normDescription": "Constituição Federal",
              "normReferences": [
                 {"articleNumber": 5, "isCaput": true, "incisoNumber": 3, "paragraphNumber": null, "isParagraphSingle": false, "letterCode": null}
              ]
            },
            {
              "jurisdictionLevel": "federal",
              "normType": "LEI",
              "normIdentifier": "LEI-8112-1990",
              "normYear": 1990,
              "normDescription": "Regime Jurídico Único",
              "normReferences": [
                 {"articleNumber": 1, "isCaput": false, "incisoNumber": null, "paragraphNumber": null, "isParagraphSingle": true, "letterCode": "a"}
              ]
            }
         ]
      }
      ```
      
      ## Validação
      - JSON parseável; usar null (não strings).
      ```

    - **4.2. User Prompt:**
      ```
      # USER MESSAGE — Extração de Legislação
      
      Extraia as referências legislativas do texto abaixo e retorne **apenas JSON válido**, conforme definido no SYSTEM PROMPT.
      
      [conteúdo do campo 'rawData.rawLegislation']
      
      ## Saída obrigatória
      Retornar **somente JSON válido**, exatamente na estrutura acima.  
      Não incluir markdown, comentários ou texto adicional.
      ```

5. Receber a resposta da API Mistral, validar se o JSON retornado está correto e em conformidade com o schema esperado.
    - 5.1. Exibir ao usuário a resposta integral recebida da API para conferência.

6. Atualizar o documento na collection `case_data`, salvando os dados extraídos em `caseData.caseLegislationReferences`.
    - 6.1. Cada citação deve ser salva como um objeto dentro de uma lista em `caseData.caseLegislationReferences`.

7. Atualizar o status do pipeline para `"legislationExtracted"` e registrar a data/hora da extração em `processing.caseLegislationRefsAt`.

---

# SCRIPT UNIFICADO PARA BUSCA, EXTRAÇÃO E SALVAMENTO DE DADOS DO STF NO MONGODB

Utilizando o código dos seguintes scripts como contexto: `b_search_save_html-old.py`, `c_extract_data.py`, `e_fetch_case_html.py`.

Desejo unificar todas as funções, recursos, funcionalidades e estruturas desses scripts em um único script Python que execute todo o processo de busca, extração e salvamento de dados em um único documento JSON na collection `case_data` do MongoDB.

## Requisitos Gerais

### Comportamento Global

- Após a execução da etapa inicial, o sistema deverá sempre informar ao usuário a quantidade de processos novos e já existentes, solicitando que o usuário informe se deseja prosseguir com a extração apenas dos novos ou de todos (novos e atualizando os existentes).
- O processamento individual de cada processo deverá ser informado ao usuário com mensagens claras sobre o andamento, sucesso ou falha de cada etapa.
- A cada processamento de um processo, solicite a confirmação do usuário para prosseguir para o próximo processo ou interromper o processamento.

## Funcionalidades do Script Unificado

### ETAPA 1: PESQUISAR STF E IDENTIFICAR PROCESSOS

1. Montar a URL de busca com base em parâmetros fornecidos (ex.: termos de busca, datas, etc.) — baseado em `b_search_save_html-old.py`.

2. Realizar a busca utilizando a URL montada, obter o HTML completo da página de resultados.
    - 2.1. Salvar o HTML bruto da página de resultados na collection `case_query` do MongoDB — baseado em `b_search_save_html-old.py`.
    - 2.2. Definir o status do pipeline como `"new"` na collection `case_query`.

3. Analisar o conteúdo do HTML bruto e identificar/extrair os dados mínimos de identificação de cada processo listado na página de resultados, inserindo no documento JSON na collection `case_data`, utilizando o schema padrão — baseado em `c_extract_data.py`.
    - 3.1. Definir o status do pipeline como `"caseScraped"` na collection `case_data`.

### ETAPA 2: OBTER, SANITIZAR E CONVERTER HTML COMPLETO DOS PROCESSOS

1. Buscar na collection `case_data` os processos com status do pipeline `"caseScraped"`.

2. Para cada processo encontrado, obter a URL em `caseUrl` e realizar a requisição para obter o HTML completo do processo.
    - 2.1. Salvar o HTML bruto do processo na collection `case_data` no campo `caseContent.caseHtml`.
    - 2.2. Sanitizar o HTML bruto para remover scripts, estilos e elementos desnecessários, salvando no campo `caseContent.caseHtmlClean`.
    - 2.3. Converter o HTML sanitizado para markdown, salvando no campo `caseContent.caseMarkdown`.
    - 2.4. Definir o status do pipeline como `"htmlFetched"` na collection `case_data`.

### ETAPA 3: IDENTIFICAR E EXTRAIR SEÇÕES DO MARKDOWN

1. Buscar na collection `case_data` os processos com status do pipeline `"htmlFetched"`.

2. Para cada processo encontrado, analisar o conteúdo em `caseContent.caseMarkdown` para identificar e extrair:
    - Publicação
    - Partes envolvidas
    - Ementa/Resumo
    - Decisão
    - Palavras-chave
    - Legislação citada
    - Doutrina citada

3. Salvar os dados extraídos nos campos correspondentes (estrutura `rawData`):
    - `rawData.rawPublication`
    - `rawData.rawParties`
    - `rawData.rawSummary`
    - `rawData.rawDecision`
    - `rawData.rawKeywords`
    - `rawData.rawLegislation`
    - `rawData.rawDoctrine`

4. Processar e estruturar os seguintes dados e salvá-los nos campos correspondentes (estrutura `caseData`):
    - `caseData.caseParties` — lista de partes envolvidas com tipo e nome
    - `caseData.caseKeywords` — lista de palavras-chave

---

## Estrutura do Documento JSON da Collection `case_data`

```json
{
  "_id": "65f0c9f0e1b2c3d4e5f67890",
  "caseStfId": "sjur12345",
  "caseIdentification": {
     "caseTitle": "ADI 7518 / ES - ESPÍRITO SANTO",
     "caseClassDetail": "ADI",
     "caseCode": "7518",
     "judgingBody": "Tribunal Pleno",
     "rapporteur": "Min. Gilmar Mendes",
     "caseUrl": "https://jurisprudencia.stf.jus.br/..."
  },
  "dates": {
     "judgmentDate": "16/09/2024",
     "publicationDate": "02/10/2024"
  },
  "caseContent": {
     "caseHtml": "<html>...</html>",
     "caseHtmlClean": "<div class=\"mat-tab-body-wrapper\">...</div>",
     "caseMarkdown": "#### Publicação\n..."
  },
  "rawData": {
     "rawPublication": "PROCESSO ELETRÔNICO\nDJe-s/n DIVULG 01-10-2024 PUBLIC 02-10-2024",
     "rawParties": "REQTE.(S): PROCURADORA-GERAL DA REPÚBLICA\nINTDO.(A/S): GOVERNADOR DO ESTADO DO ESPÍRITO SANTO",
     "rawSummary": "Ação direta de inconstitucionalidade. 2. Licença-parental...",
     "rawDecision": "Decisão ...",
     "rawKeywords": "NECESSIDADE, EXTINÇÃO, TRIBUNAL DO JÚRI, ...",
     "rawLegislation": "LEI-008112/1990 (RJU) ...",
     "rawNotes": "Observação ...",
     "rawDoctrine": "BARROSO, Luís Roberto..."
  },
  "caseData": {
     "caseParties": [
        { "partieType": "REQTE.(S)", "partieName": "PROCURADORA-GERAL DA REPÚBLICA" },
        { "partieType": "INTDO.(A/S)", "partieName": "GOVERNADOR DO ESTADO DO ESPÍRITO SANTO" }
     ],
     "caseKeywords": [
        "licença parental",
        "servidor público",
        "constitucionalidade"
     ],
     "caseDoctrineReferences": [
        {
          "author": "BARROSO, Luís Roberto",
          "publicationTitle": "O controle de constitucionalidade no direito brasileiro: exposição sistemática da doutrina e análise crítica da jurisprudência",
          "edition": "4 ed",
          "publicationPlace": "São Paulo",
          "publisher": "Saraiva",
          "year": 2009,
          "page": "181",
          "rawCitation": "BARROSO, Luís Roberto. O controle de constitucionalidade... p. 181."
        }
     ],
     "caseLegislationReferences": [
        {
          "jurisdictionLevel": "federal",
          "normType": "CF",
          "normIdentifier": "CF-1988",
          "normYear": 1988,
          "normDescription": "Constituição Federal",
          "normReferences": [
             {
                "articleNumber": 5,
                "isCaput": true,
                "incisoNumber": 3,
                "paragraphNumber": null,
                "isParagraphSingle": false,
                "letterCode": null
             }
          ]
        }
     ]
  },
  "processing": {
     "pipelineStatus": "enriched",
     "caseHtmlScrapedAt": "2026-01-26T22:10:00Z",
     "caseContentMinedAt": "2026-01-26T22:35:00Z",
     "caseDoctrineRefsAt": "2026-01-26T22:40:00Z",
     "caseLegislationRefsAt": "2026-01-26T22:41:00Z",
     "lastUpdatedAt": "2026-01-26T22:41:00Z",
     "errors": []
  },
  "status": {
     "pipelineStatus": "caseScraped"
  },
  "sourceIds": {
     "rawHtmlId": "65f0c9f0e1b2c3d4e5f11111"
  }
}
```

---

## Próximas Etapas

Desenvolva um novo script Python que realize todas as operações descritas, respeitando a estrutura do documento JSON padronizado fornecido anteriormente.
