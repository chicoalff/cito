Analise o arquivo py em anexo e utilize ele como base para criar um novo script completamente novo e funcional. Ele deve atender às seguintes especificações e requisitos:


## FUNCIONALIDADES E FLUXO DO SCRIPT PY

- Consultar a collection  stf_html no mongo db, filtrando pelos registros que possuírem o campo status = "new"
- Obter os dados do registro mais antigo com da collection (Cluster0, db: cito-v-a33-240125) "raw_html" que possua o cmapo "status" = "new"
- Analisar INTEGRALMENTE TODO O CONTEÚDO do campo "raw_html", e identificar e extraír os seguintes campos:

    * **vatiável no código atual** - **nome coluna output** 
    * id_unico – localIndex
    * id_decisao_stf – stfDecisionId
    * decisao – caseTitle
    * url – caseUrl
    * orgao_colegiado – judgingBody
    * relator – rapporteur
    * redator_acordao – opinionWriter
    * julgamento – judgmentDate
    * publicacao – publicationDate
    * processo_classe – caseClass
    * processo_numero – caseNumber
    * inteiro_teor_ocorrencias – fullTextOccurrences
    * indexacao_ocorrencias – indexingOccurrences
    * result_container_dom_id – domResultContainerId
    * clipboard_dom_id – domClipboardId 
   
---

## DETALHAMENTO E ESPECÍFICAÇÃO DOS DADOS PARA EXTRAÇÃO

---

**DADO: id_unico**

* **DB COLUMN:** localIndex
* **DESCRIÇÃO:** Identificador sequencial local do item, representando a ordem do resultado no HTML processado. Não corresponde a um identificador oficial do STF.
* **TIPO:** integer
* **COMO EXTRAIR:** Não é extraído do HTML. É gerado programaticamente no loop de iteração usando `enumerate(containers, start=1)`.
* **EXEMPLO:** `1`

---

**DADO: id_decisao_stf**

* **DB COLUMN:** stfDecisionId
* **DESCRIÇÃO:** Código interno da decisão no sistema de jurisprudência do STF, normalmente no formato `sjurNNNNNN`.
* **TIPO:** string
* **COMO EXTRAIR:** Localizar, dentro de `div.result-container`, o link `<a>` com classe `mat-tooltip-trigger` e `mattooltip="Dados completos"`. Ler o atributo `href` e extrair o penúltimo segmento da URL (`href.split("/")[-2]`).
* **EXEMPLO:** `sjur513420`

---

**DADO: decisao**

* **DB COLUMN:** caseTitle
* **DESCRIÇÃO:** Título do resultado exibido no card de jurisprudência, geralmente composto pela classe processual e número do processo.
* **TIPO:** string
* **COMO EXTRAIR:** CSS/BS4: `div.result-container a[mattooltip="Dados completos"] h4.ng-star-inserted` → `text.strip()`
* **EXEMPLO:** `ADI 7518`

---

**DADO: url**

* **DB COLUMN:** caseUrl
* **DESCRIÇÃO:** URL completa da página de detalhes (“Dados completos”) da decisão no portal do STF.
* **TIPO:** string
* **COMO EXTRAIR:** Ler o `href` do link “Dados completos” e prefixar com `https://jurisprudencia.stf.jus.br`.
* **EXEMPLO:** `https://jurisprudencia.stf.jus.br/pages/search/sjur513420/false`

---

**DADO: orgao_colegiado**

* **DB COLUMN:** judgingBody
* **DESCRIÇÃO:** Órgão julgador responsável pela decisão.
* **TIPO:** string
* **COMO EXTRAIR:** Dentro de `div#result-principal-header`, localizar o `h4.ng-star-inserted` cujo texto contém “Órgão julgador:” e extrair o texto do `span` interno.
* **EXEMPLO:** `Tribunal Pleno`

---

**DADO: relator**

* **DB COLUMN:** rapporteur
* **DESCRIÇÃO:** Ministro(a) relator(a) da decisão.
* **TIPO:** string
* **COMO EXTRAIR:** Em `div#result-principal-header`, localizar o `h4.ng-star-inserted` com o rótulo “Relator(a):” e extrair o texto do `span`.
* **EXEMPLO:** `Min. GILMAR MENDES`

---

**DADO: julgamento**

* **DB COLUMN:** judgmentDate
* **DESCRIÇÃO:** Data em que ocorreu o julgamento da decisão.
* **TIPO:** string (data no formato exibido pelo site)
* **COMO EXTRAIR:** Em `div#result-principal-header`, localizar o `h4` cujo texto contém “Julgamento:” e extrair o valor do `span`.
* **EXEMPLO:** `16/09/2024`

---

**DADO: publicacao**

* **DB COLUMN:** publicationDate
* **DESCRIÇÃO:** Data de publicação oficial da decisão.
* **TIPO:** string (data no formato exibido pelo site)
* **COMO EXTRAIR:** Em `div#result-principal-header`, localizar o `h4` cujo texto contém “Publicação:” e extrair o valor do `span`.
* **EXEMPLO:** `02/10/2024`

---

**DADO: redator_acordao**

* **DB COLUMN:** opinionWriter
* **DESCRIÇÃO:** Ministro(a) redator(a) do acórdão, quando essa informação estiver presente no card do resultado.
* **TIPO:** string
* **COMO EXTRAIR:** Em `div#result-principal-header`, localizar o `h4.ng-star-inserted` cujo texto contém “Redator(a) do acórdão:” e extrair o `span` interno. Campo opcional.
* **EXEMPLO:** `Min. EDSON FACHIN`

---

**DADO: processo_classe**

* **DB COLUMN:** caseClass
* **DESCRIÇÃO:** Classe processual do processo (ADI, ADC, ADPF, ADO etc.).
* **TIPO:** string
* **COMO EXTRAIR:** A partir do link de “Acompanhamento processual” (`a[mattooltip="Acompanhamento processual"]`), fazer o parse da querystring e ler o parâmetro `classe`.
* **EXEMPLO:** `ADI`

---

**DADO: processo_numero**

* **DB COLUMN:** caseNumber
* **DESCRIÇÃO:** Número do processo no STF.
* **TIPO:** string
* **COMO EXTRAIR:** A partir do mesmo link de “Acompanhamento processual”, extrair da querystring o parâmetro `numeroProcesso`.
* **EXEMPLO:** `7518`

---

**DADO: inteiro_teor_ocorrencias**

* **DB COLUMN:** fullTextOccurrences
* **DESCRIÇÃO:** Quantidade de ocorrências de “Inteiro teor” indicada na seção “Outras ocorrências” do card.
* **TIPO:** integer
* **COMO EXTRAIR:** Em `div.result-container`, localizar a seção “Outras ocorrências”, identificar o link cujo `span.mr-5` é “Inteiro teor” e extrair o número entre parênteses usando regex `\((\d+)\)`.
* **EXEMPLO:** `15`

---

Esse detalhamento define, de forma alinhada ao HTML real analisado, **o significado, a origem técnica e o destino em banco** de cada campo que compõe o modelo de extração do Projeto CITO.



---


### GRAVAR DADOS EXTRÍDO NO MONGO DB

Os dados extraídos do html deverão ser salvos no mesmo database do mongo db, porém na colléction case_data.


Após gravar os dados nessa collection, o script deverá fazer um update no campo "status" da collection raw_html do dado utilizado, alterando o valor da coluna "status" de "new", para "extracted"


## DADOS DE CONEXÃO COM O BANCO DE DADOS

**Credenciais Mongo DB**
    - Usuário mongo: cito
    - Senha mongo: fyu9WxkHakGKHeoq
    - Cluster name: Cluster0
    - Database name: cito-v-a33-240125
    - Collection para obter os dados iniciais: raw_html
    - Collection para salvar os dados extraídos: case_data

**Mongo String**
    - mongodb+srv://<db_username>:<db_password>@cluster0.gb8bzlp.mongodb.net/?appName=Cluster0



