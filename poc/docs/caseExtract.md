


### SCRIPT PYTHON PARA OBTER O HTML DÁ PÁGINA DA SENTENÇA

- Obter o campo 'caseUrl' da collection "case_data"
    - Filtros: 
        - consultar por documentos com "status" = 'extracted'
        - retornar apenas o registro mais antigo com o "status" = 'extracted'
- Acessar a url (caseUrl) e obter o html integral.
- Inserir um campo chamado 'caseHtml' no respectivo documento na collection "case_data", contendo todo o conteúdo html obtido.
- Alterar o "status" para 'caseScraped'.

---

### SANITIZAR CASE HTML

Crie um novo script python para realizar a sanitização do html obtido no passo anterior.

- Obter o campo 'caseHtml' da collection "case_data"
    - Filtros: 
        - consultar por documentos com "status" = 'caseScraped'
        - retornar apenas o registro mais antigo com o "status" = 'caseScraped'
- O script deve realizar a sanitização do html obtido do caseUrl, mantendo apenas o conteúdo existente em '/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]'
- Salve o html sanitizado no campo 'caseHtmlSanitized' do respectivo documento na collection "case_data".
- Alterar o "status" para 'caseSanitized'.
- Repetir o processo para os próximos documentos com "status" = 'caseScraped'.


### PROCESSAR CASE HTML SANITIZADO E EXTRAIR INFORMAÇÕES

Crie um script que realize a identificação e todos os dados contidos em um caseHtmlSanitized e realize a extração de todos os dados existentes, e posteriormente faça a gravação dos dados na collection 

**DADOS A SEREM EXTRAÍDOS:**

Segue a **tabela revisada**, substituindo **`caseHeader`** por **`caseCode`** e mantendo todo o restante consistente com o HTML sanitizado e com a modelagem da collection `case_data`.

| dado                               | descrição                                                                                                      | como extrair                                                                                                                                                      | db field (case_data) |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| **Código do caso (identificação)** | Classe + número + sufixos e UF/origem (ex.: `ADPF 1159 MC-Ref / SC - SANTA CATARINA`)                          | **BeautifulSoup**: localizar o **primeiro** `div.jud-text` que contém `Relator(a):`. Dentro dele, obter o **primeiro `h4`** (`h4s[0].get_text(" ", strip=True)`). | `caseCode`           |
| Classe processual                  | Sigla da classe (ex.: `ADPF`, `ADI`, `ADC`)                                                                    | A partir de `caseCode`: regex `^([A-Z]+)\s+`.                                                                                                                     | `caseClassDetail`    |
| Número do processo                 | Número base do processo (ex.: `1159`)                                                                          | A partir de `caseCode`: regex `^[A-Z]+\s+(\d+)` (ou `(\d[\d\.\-]*)` se houver hífen/ponto).                                                                       | `caseNumberDetail`   |
| UF / origem                        | UF e nome do estado (ex.: `SC - SANTA CATARINA`)                                                               | A partir de `caseCode`: se existir `"/"`, pegar o trecho após `/` e aplicar `strip()`.                                                                            | `caseUfDetail`       |
| Tipo/Natureza da decisão           | Texto descritivo do tipo (ex.: “REFERENDO NA MEDIDA CAUTELAR...”)                                              | No mesmo `div.jud-text` do cabeçalho: **segundo `h4`** (`h4s[1].get_text(" ", strip=True)`).                                                                      | `caseDecisionType`   |
| Relator(a)                         | Ministro(a) relator(a)                                                                                         | No bloco de cabeçalho (`div.jud-text`): localizar `h4` que inicia com `Relator(a):` e extrair texto após `:`.                                                     | `rapporteur`         |
| Julgamento                         | Data do julgamento                                                                                             | No bloco de cabeçalho: `h4` que inicia com `Julgamento:`; extrair valor após `:` (ou regex `\d{2}/\d{2}/\d{4}`).                                                  | `judgmentDate`       |
| Publicação (data simples)          | Data de publicação exibida no cabeçalho                                                                        | No bloco de cabeçalho: `h4` que inicia com `Publicação:`; extrair valor após `:`.                                                                                 | `publicationDate`    |
| Órgão julgador                     | Órgão colegiado (ex.: `Tribunal Pleno`)                                                                        | No bloco de cabeçalho: `h4` que inicia com `Órgão julgador:`; extrair valor após `:`.                                                                             | `judgingBody`        |
| Ações/atalhos de interface         | Ações disponíveis (ex.: `Inteiro teor`, `DJ/DJe`, `Imprimir`, `Copiar resultado`, `Acompanhamento processual`) | Coletar elementos com atributo `mattooltip`: `soup.find_all(attrs={"mattooltip": True})` e extrair valores únicos.                                                | `uiTooltips`         |
| ODS (Agenda 2030)                  | Objetivos de Desenvolvimento Sustentável associados                                                            | `soup.select('a[mattooltip="Conheça a Agenda 2030 da ONU"] img')`; extrair `alt` (ou código pelo `src`).                                                          | `odsTags`            |
| Publicação (detalhada / DJe)       | Bloco textual com metadados do DJe                                                                             | Seção `h4 == "Publicação"`; conteúdo em `div.text-pre-wrap` → `get_text("\n", strip=True)`.                                                                       | `publicationBlock`   |
| Partes                             | Partes e representantes (REQTE, INTDO, ADV etc.)                                                               | Seção `h4 == "Partes"`; conteúdo em `div.text-pre-wrap`.                                                                                                          | `partiesBlock`       |
| Ementa                             | Texto integral da ementa                                                                                       | Seção `h4 == "Ementa"`; conteúdo no `div` imediatamente após o `h4`.                                                                                              | `ementaText`         |
| Decisão                            | Texto do resultado do julgamento                                                                               | Seção `h4 == "Decisão"`; conteúdo no `div` imediatamente após o `h4`.                                                                                             | `decisionText`       |
| Indexação                          | Palavras-chave / assuntos indexados                                                                            | Seção `h4 == "Indexação"`; conteúdo em `div.text-pre-wrap`.                                                                                                       | `indexingText`       |
| Legislação                         | Normas e dispositivos citados                                                                                  | Seção `h4 == "Legislação"`; conteúdo em `div.text-pre-wrap`.                                                                                                      | `legislationText`    |
| Observação                         | Notas adicionais / referências                                                                                 | Seção `h4 == "Observação"`; conteúdo em `div.text-pre-wrap`.                                                                                                      | `observationText`    |
| Acórdãos no mesmo sentido          | Precedentes relacionados                                                                                       | Seção `h4 == "Acórdãos no mesmo sentido"`; conteúdo em `div.text-pre-wrap` (opcional estruturar por linhas).                                                      | `similarCasesBlock`  |
| Doutrina                           | Referências doutrinárias                                                                                       | Seção `h4 == "Doutrina"`; conteúdo em `div.text-pre-wrap`.                                                                                                        | `doctrineBlock`      |


**GRAVAR DADOS NA COLLECTION:**

Após o processamento do html sanitizado, identificação e extração dos dados, o script deve:

- Gravar as informações extraídas no mesmo documento na collection 'case_data', criando novos campos conforme necessário para armazenar os dados extraídos.
- Alterar o campo "status" para 'caseHtmlProcessed' após a conclusão do processamento e gravação dos dados extraídos.
- Exiba no terminal apenas as seguintes informações:
    - Ao iniciar o processamento de um novo documento: 
        - "DD-MM-YYY HH:MM:SS - Iniciando processamento do documento '_id': 'caseTitle'"
    - Ao concluir o processamento de um documento:
        - "DD-MM-YYY HH:MM:SS - Extração concluída para o documento '_id': 'caseTitle'"
        - "DD-MM-YYY HH:MM:SS - Dados obtidos: (listar o nome de todos os db fields extraídos, sem os valores)
            - nome do dado 1
            - nome do dado 2
            - nome do dado 3
            - ..."
        - "DD-MM-YYY HH:MM:SS - Tempo total de processamento: 'XX segundos/minutos'"
        - "DD-MM-YYY HH:MM:SS - Status final: 'caseHtmlProcessed'
- Repetir o processo para os próximos documentos com "status" = 'caseSanitized'.
