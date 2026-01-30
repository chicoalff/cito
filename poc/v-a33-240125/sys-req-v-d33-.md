

# CITO PROJECT- SYSTEM REQUIREMENTS

- Version: v-d33
- Start date: 20-01-2025

## IDENTIFICAR E EXTRAIR PROCESSOS 

### PIPELINE

1. Obter o HTML da página de resultados da query no site do STF
    - Collection: "case_query" 
    - Campo no documento: "htmlRaw"  
    - Filtrar por documentos com `pipelineStatus = "new"` na collection `case_query`
2. Identificar e xtrair os cards/Processos.
    1.1. Identificar dados de cada processo, e inserir/atualizar o documento na collection `case_data`  

## OBTER HTML DO PROCESSO

### PIPELINE 

1. Processar cada documento  da collection `case_data`, com `pippeLineStatus` = `caseScraped`, individualmente, um por vez.
2. Obter aurl da página do processo em `casr_data.caseIdentification.caseUrl`.
3. Realizar requisção da url e obter o html completo da página do processo. 
4. Inswerir o conteúdo integral do hml no campo
Buscar HTML completo de cada processo, e gravar o html completo no cammpo  `caseContent.caseHtml`do documento documento nSa collection `case_data`.
5 Atualiza/insere informações de status em `case_data.processing`.


## SCHEMA JSON DOCUMENTO COLLECTION `case_data`



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