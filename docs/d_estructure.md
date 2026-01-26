
## Estrutura de Pastas do Projeto CITO 

projeto-cito/
├── 📁 .venv/                      # Ambiente virtual Python (ignorado)
├── 📁 docs/                       # Documentação geral
│   ├── a_requirements.md          # Requisitos funcionais e técnicos
│   ├── b_copilot.md               # Guias de uso do GitHub Copilot
│   └── c_kndowledge.md            # Base de conhecimento do domínio
├── 📁 poc/v-a33-240125/           # Prova de Conceito específica
    ├── 📁 config/                 # Configurações do projeto                
    │   └── service_account.json   # Credenciais de serviço (Google)
    ├── 📋 a_load_configs.py       # Módulo 1: Carregamento de configurações
    ├── 📋 b_search_save_html.py   # Módulo 2: Busca e coleta HTML
    ├── 📋 c_extract_data.py       # Módulo 3: Extração de dados básicos
    ├── 📋 e_fetch_case_html.py    # Módulo 4: Coleta HTML individual
    ├── 📋 f_sanitize_case_html.py # Módulo 5: Sanitização de HTML
    ├── 📋 g_process_case_html_sa... # Módulo 6: Processamento final
    ├── 📋 .gitignore              # Padrões ignorados pelo Git
    └── 📋 readme.md               # Documentação principal do projeto

## Descrição das Pastas e Arquivos

### `poc/`
- Diretório de **Provas de Conceito (PoC)**.
- Centraliza experimentações técnicas e versões controladas.

#### `poc/v-a33-240125/`
Versão específica da PoC, identificada por código interno e data.  
Representa um **snapshot funcional completo do pipeline ETL**.

##### `config/`
- Arquivos de configuração externa.
- Ex.: credenciais, parâmetros operacionais e integração com Google Sheets.

##### `a_load_configs.py`
- Carrega e normaliza configurações externas.
- Centraliza parâmetros do pipeline.
- Permite ajustes sem alteração de código.

##### `b_search_save_html.py`
- Executa buscas no portal do STF.
- Coleta e persiste o HTML bruto das páginas de resultado.

##### `c_extract_data.py`
- Processa HTML bruto.
- Extrai a lista de decisões encontradas.
- Cria registros iniciais na base de dados.

##### `e_fetch_case_html.py`
- Acessa a página individual de cada decisão.
- Coleta o HTML completo (inteiro teor).

##### `f_sanitize_case_html.py`
- Remove ruídos do HTML (menus, navegação, elementos visuais).
- Mantém apenas o conteúdo juridicamente relevante.

##### `g_process_case_html_sanitized.py`
- Extrai metadados jurídicos detalhados.
- Processa blocos textuais como ementa, decisão, partes e publicações.
