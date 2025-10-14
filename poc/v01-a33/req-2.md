

Crie um novo script em python, que será responsável pela obtenção dos dados da página de cada decisão.


## REQUISITOS
### VARIÁVEIS E PARAMETRIZACAO
- Inclua variáveis para definir os paths de entrada, saída.
- Inclua parametros de configuração pertinentes

### IDENTIFICAÇÃO DA DECISÃO E URL PARA SCRAPING
- Ler o arquivo .json contendo o indice de decisões
- Identificar o primeiro registro que contenha o campo "status" = "novo"
- Obter os seguintes dados e grava-los em variáveis para uso durante a execussão do código:
    - id_stf
    - url_decisao
- Alterar o campo "status" para "processando"


### OBTER HTML/CONTEÚDO COMPLETO DA PÁGINA
- criar uma pasta (no diretório "data/decisoes") com o título da decisão, tudo em minúsculo, com hifem no lugar de espçao (exemplo: adpf-526, adi-33, etc...) 
- Obter o código html completo da url_decisão e salvar na pasta criaada anteriormente, com o nome seguindo  o padrão: título-decisao + dia +mês + ano + hora + minuto. Exemplo: adpf-526-13-10-2005-11-48.html

- Após salvar o html, mude o status para "html salvo" no arquivo .json
- Atualize a dt_atualizado no arquivo .json

### EXTRAIR DADOS DO HTML PARA JSON
- Analise o html e identifique os dados detalhados conforme as especificações a seguir.
- Salve o arquivo na pasta da decisão em formato json usando o mesmo padrão de nomeclatura
     
    id_stf (identificador da sentença no site do stf),
    uf (sigla da unidade federativa, em duas letras. ex.: PR, MG, DF, SP, etc.),
    classe (sigla da classe da sentença, ex,> ADI, ADC, ADPF, ADO, etc)
    publicacao (uma ou mais linhas de texto contendo detalhes da publicação, como data, número do diário oficial, página, etc) Ex.:
        ACÓRDÃO ELETRÔNICO
        DJe-080 DIVULG 29-04-2013 PUBLIC 30-04-2013
        RTJ VOL-00226-01 PP-00011
    partes (lista de partes envolvidas, contendo o papel/função abreviada e o nome do envolvidas.) exemplo:
        REQTE.(S)  : PARTIDO SOCIALISTA BRASILEIRO - PSB 
        ADV.(A/S)  : RAFAEL DE ALENCAR ARARIPE CARNEIRO E OUTRO(A/S)
        INTDO.(A/S)  : MINISTRO DE ESTADO DA SAÚDE 
        ADV.(A/S)  : ADVOGADO-GERAL DA UNIÃO 
        INTDO.(A/S)  : AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA - ANVISA 
        PROC.(A/S)(ES) : PROCURADOR-GERAL FEDERAL 
        AM. CURIAE.  : INSTITUTO BRASILEIRO DE DIREITO DE FAMILIA - IBDFAM 
        ADV.(A/S)  : MARIA BERENICE DIAS 
        ADV.(A/S)  : RONNER BOTELHO SOARES 
        AM. CURIAE.  : GRUPO DIGNIDADE - PELA CIDADANIA DE GAYS, LÉSBICAS E TRANSGÊNEROS 
        ADV.(A/S)  : RAFAEL DOS SANTOS KIRCHHOFF 
    ementa (texto da ementa, resumo ou sumário da decisão),
    tese (texto da tese jurídica firmada na decisão, quando houver),
    decisao (texto da decisao como disponível na página da decisão no site do stf)
    indexação (lista de palavras-chave utilizadas para indexação e categorização da decisão) 
    legislação (lista de referências a legislação mencionada na decisão, com detalhes como número, artigo, parágrafo, etc) Exemplo:
        LEG-FED   CF      ANO-1988
            ART-00001 INC-00003 ART-00003 INC-00001 
            INC-00004 ART-00004 INC-00001 INC-00002 
            ART-00005 "CAPUT" INC-00041 INC-00042 
            PAR-00001 PAR-00002 PAR-00003 ART-00006 
            ART-00007 ART-00008 ART-00009 ART-00010 
            ART-00011 ART-00012 ART-00013 ART-00014 
            ART-00015 ART-00016 ART-00017 ART-00059 
            ART-00084 INC-00006 INC-00012 ART-00102 
            INC-00001 LET-A ART-00103 INC-00008 
            ART-00199 PAR-00004 ART-00200
                CF-1988 CONSTITUIÇÃO FEDERAL
        LEG-FED   LEI-007716      ANO-1989
            LEI ORDINÁRIA
    observacoes (campo livre para observações adicionais sobre a decisão)
    doutrina (lista com referências doutrinárias mencionadas na decisão, como livros, artigos, autores, etc)  exemplo:
        ALEXY, Robert. Teoria dos Direitos Fundamentais. São Paulo: Malheiros, 2006. p. 593-594.
        BARROSO, Luís Roberto. A Dignidade da Pessoa Humana no Direito Constitucional Contemporâneo: a construção de um conceito jurídico à luz da jurisprudência mundial. Belo Horizonte: Fórum, 2013.
        BALKIN, Jack. M. Constitutional Redemption: Political Faith in an Unjust World. Cambridge: Harvard University Press, 2011. p. 5-6.
        BORRILLO, Daniel. Homofobia: história e crítica de um preconceito. Belo Horizonte: Autêntica, 2010. p. 38-39.
        CARDINALI, Daniel Carvalho. A escola como instrumento do dever constitucional de enfrentamento da homofobia: potencialidade e tensões. Revista Publicum, Rio de Janeiro, v. 3, n. 1, 2017. p. 158 e p. 166.
        CARVALHO, Menelick de. A hermenêutica constitucional e os desafios postos aos direitos fundamentais. In: SAMPAIO, José Adércio Leite (Org.). Jurisdição constitucional e direitos fundamentais. Belo Horizonte: Del Rey, 2003. p. 154.
        CARVALHO NETO, Menelick de; SCOTTI, Guilherme. Os Direitos Fundamentais e a (In)Certeza do Direito – A produtividade das Tensões Principiológicas e a Superação do Sistema de Regras. Belo Horizonte: Fórum, 2011. p. 19-20.
    url_arquivo (url do arquivo PDF contendo os documentos e o inteiro teor da decisão, quando disponível))
