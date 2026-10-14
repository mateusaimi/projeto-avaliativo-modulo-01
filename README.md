# Pipeline de Dados e Análise de Vendas — Supermarket Sales

Projeto de engenharia e análise exploratória de dados aplicado a registros transacionais de varejo (1.000 vendas realizadas no 1º trimestre de 2019). A solução estrutura o fluxo desde a carga bruta no PostgreSQL até a limpeza, tipagem relacional e geração de indicadores com Python e Pandas, seguindo a separação entre camadas **Raw (Bronze)**, **Tratada (Silver)** e **Analítica (Gold)**.

---

## Arquitetura da Solução

1. **Camada Raw (Bronze)**: Ingestão fiel do arquivo `SuperMarket Analysis.csv` na tabela `public.raw_vendas` do PostgreSQL. Todos os campos originais são armazenados como `TEXT` para preservar a rastreabilidade da fonte e permitir auditoria de *round-trip* (`data/raw/vendas_exportadas.csv`).
2. **Camada Tratada (Silver)**: Higienização, validação de domínio e tipagem com Pandas (`src/02_etl_vendas.py`), persistindo o resultado em `data/processed/vendas_tratadas.csv` e na tabela `public.vendas_tratadas`. Aplica nomenclatura padronizada em *snake_case*, conversão de datas (`DATE`), horários (`TIME`) e valores monetários (`NUMERIC(10,2)` / `NUMERIC(12,2)`), derivação do `dia_semana` e proteção por constraints relacionais (`PRIMARY KEY`, `NOT NULL` e `CHECK`).
3. **Camada Analítica (Gold)**: Extração de estatísticas descritivas, consolidação das respostas de negócio e geração dos gráficos comparativos no diretório `resultados/` (`src/03_estatistica.py` e `sql/03_consultas.sql`).

---

## Estrutura do Diretório

```text
projeto-avaliativo-modulo-01/
├── sql/
│   ├── 01_criar_banco.sql          # Criação do banco de dados supermarket_sales_db
│   ├── 02_criar_tabelas.sql        # DDL das tabelas raw_vendas e vendas_tratadas
│   └── 03_consultas.sql            # Consultas SQL exploratórias (Raw) e analíticas (Tratada)
├── src/
│   ├── 01_leitura_dados.py         # Ingestão Raw, EDA inicial e conferência de integridade
│   ├── 02_etl_vendas.py            # Pipeline ETL, validação de regras e carga na tabela Tratada
│   └── 03_estatistica.py           # Estatística descritiva, respostas de negócio e gráficos
├── data/
│   ├── raw/                        # CSV original do Kaggle e exportação SQL da camada Raw
│   └── processed/                  # Base tratada (vendas_tratadas.csv) e dicionário de dados
├── resultados/                     # Relatórios analíticos, auditoria de qualidade e gráficos PNG
├── .env.example                    # Modelo de configuração das variáveis de ambiente
├── .gitignore                      # Exclusão de credenciais (.env) e ambiente virtual (.venv)
├── requirements.txt                # Dependências do projeto
└── README.md                       # Documentação técnica e analítica da solução
```

---

## Tecnologias Utilizadas

* **Linguagem**: Python 3.14
* **Banco de Dados Relacional**: PostgreSQL 18
* **Processamento e Análise de Dados**: Pandas 3.0.6
* **Visualização de Dados**: Matplotlib 3.11.2
* **Conectividade SQL**: SQLAlchemy 2.1.1 + driver `pg8000` 1.31.5 (driver em Python puro, evitando dependências de compilação C/DLLs nativas no Windows)
* **Variáveis de Ambiente**: python-dotenv 1.2.3

---

## Fonte de Dados e Critérios Contábeis

* **Fonte**: Conjunto público [Supermarket Sales (Kaggle)](https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales), localizado em `data/raw/SuperMarket Analysis.csv` (1.000 registros e 17 colunas, cobrindo o período de `01/01/2019` a `30/03/2019`).
* **Composição do Faturamento (`valor_total`) vs. Margem Bruta (`receita_bruta`)**:
  * `custo_mercadoria` (`cogs`): corresponde a `preco_unitario × quantidade`.
  * `imposto` (`Tax 5%`): alíquota de 5% calculada sobre `custo_mercadoria`.
  * `valor_total` (`Sales`): representa o valor total da nota fiscal pago pelo cliente (`preco_unitario × quantidade + imposto`). É a métrica utilizada para apuração de **faturamento** e **ticket médio**.
  * `receita_bruta` (`gross income`): representa o ganho bruto da loja na operação (numericamente igual aos 5% de `imposto`, ou `4,76%` do total da nota).
* **Filiais e Cidades**: Os códigos de filial presentes no arquivo de origem (`Alex` em Yangon, `Cairo` em Mandalay e `Giza` em Naypyitaw) foram mantidos sem alterações arbitrárias.
* **Unidade Monetária**: Como a fonte não especifica divisa oficial, os resultados financeiros são reportados em unidades monetárias padronizadas.

O detalhamento de todas as colunas, tipos e regras de domínio encontra-se em [`data/processed/dicionario_dados.md`](data/processed/dicionario_dados.md).

---

## Guia de Instalação e Execução

### 1. Preparação do Ambiente Virtual

```powershell
# Criação do ambiente virtual
python -m venv .venv

# Instalação das dependências
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Criação do arquivo de variáveis de ambiente
Copy-Item .env.example .env
```

Edite o arquivo `.env` informando a senha local do seu PostgreSQL (`DB_PASSWORD`). O arquivo `.env` é ignorado pelo Git (`.gitignore`).

### 2. Criação do Banco e das Tabelas no PostgreSQL

1. Conectado ao banco padrão `postgres`, execute `sql/01_criar_banco.sql` para criar o banco `supermarket_sales_db`.
2. Conectado ao banco `supermarket_sales_db`, execute `sql/02_criar_tabelas.sql` para criar as tabelas `public.raw_vendas` e `public.vendas_tratadas`.

### 3. Execução Sequencial do Pipeline Python

A partir da raiz do projeto, execute:

```powershell
# Etapa 1: Inspeção inicial, carga na tabela raw_vendas e exportação de conferência
.\.venv\Scripts\python.exe src/01_leitura_dados.py

# Etapa 2: Transformação ETL, padronização de tipos e carga em vendas_tratadas
.\.venv\Scripts\python.exe src/02_etl_vendas.py

# Etapa 3: Estatística descritiva, respostas de negócio e geração dos gráficos
.\.venv\Scripts\python.exe src/03_estatistica.py
```

### 4. Execução das Consultas SQL

O arquivo `sql/03_consultas.sql` está dividido em duas partes para execução no cliente SQL:
* **Parte 1 (`raw_vendas`)**: conferência de carga, amostragem e agregação sobre os dados brutos em texto.
* **Parte 2 (`vendas_tratadas`)**: consultas analíticas que respondem diretamente às 8 perguntas de negócio sobre os dados já tipados.

---

## Resultados das Perguntas de Negócio

| Nº | Pergunta de Negócio | Resposta Obtida | Métrica e Referência |
|:---:|---|---|---|
| 1 | Qual filial apresentou o maior faturamento? | **Giza** (`110.568,71` un.) | Soma de `valor_total` por filial |
| 2 | Qual filial realizou a maior quantidade de vendas? | **Alex** (`340` vendas) | Contagem de vendas (`id_venda`) por filial |
| 3 | Qual linha de produto apresentou o maior faturamento? | **Food and beverages** (`56.144,86` un.) | Soma de `valor_total` por linha de produto |
| 4 | Qual linha de produto recebeu a melhor avaliação média? | **Food and beverages** (`7,11` / 10) | Média de `avaliacao` por linha de produto |
| 5 | Qual foi a forma de pagamento mais utilizada? | **Ewallet** (`345` transações) | Contagem de vendas por `forma_pagamento` |
| 6 | Qual foi o valor médio das vendas (ticket médio)? | **`322,97` un.** | Média de `valor_total` nas 1.000 vendas (mediana: `253,85`) |
| 7 | Qual foi a maior venda registrada? | **`1.042,65` un.** | Valor máximo (`id_venda = 860-79-0874`, filial **Giza**) |
| 8 | Em qual dia da semana ocorreu a maior quantidade de vendas? | **Sábado** (`164` vendas) | Contagem de vendas por `dia_semana` |

---

## Leitura Analítica e Direcionamento de Negócio

A análise conjunta das métricas e das estatísticas descritivas ([`resultados/respostas_perguntas_negocio.md`](resultados/respostas_perguntas_negocio.md)) evidencia quatro pontos práticos para a gestão da rede:

1. **Eficiência de Ticket Médio vs. Volume de Caixa entre Filiais**:
   * **Alex** lidera em fluxo de clientes (`340` vendas), mas fica em 2º lugar em faturamento (`106.200,37`), praticamente empatada com **Cairo** (`106.197,74` em `332` vendas — diferença de apenas `2,63` un. no trimestre).
   * **Giza**, mesmo registrando o menor número de transações (`328` vendas), é a líder isolada de faturamento (`110.568,71`) porque opera com um **ticket médio 7,9% maior que o de Alex** (`337,10` em Giza contra `312,35` em Alex e `319,87` em Cairo), além de possuir a melhor avaliação média entre as unidades (`7,07`). Na prática, Alex tem oportunidade de elevar receita trabalhando venda cruzada (*cross-selling*) para aproximar sua cesta média do patamar de Giza.
2. **Desempenho das Linhas de Produto**:
   * **Food and beverages** é o carro-chefe da operação, liderando tanto em receita (`56.144,86`) quanto em satisfação dos clientes (`7,11 / 10`).
   * **Fashion accessories** atrai o maior volume de compras (`178` vendas), mas gera o menor ticket médio (`305,09`), ficando na 4ª posição em faturamento (`54.305,88`).
   * **Health and beauty** tem o menor faturamento (`49.193,81`) exclusivamente por menor volume de saídas (`152` vendas), pois seu ticket médio (`323,64`) e sua avaliação (`7,00`) estão acima da média da rede — indicando potencial para ações de exposição e atração de fluxo para a categoria.
3. **Distribuição Assimétrica do Valor das Vendas**:
   * Enquanto o ticket médio geral é de **`322,97`**, a mediana (`50%`) é de **`253,85`** (com desvio padrão de `245,89` e amplitude de `10,68` a `1.042,65`). Metade dos clientes gasta até `253,85`, enquanto compras de grande volume (até 10 itens de maior valor unitário, como a venda `860-79-0874` de `1.042,65` em Giza) deslocam a média para cima.
4. **Sazonalidade Semanal e Meios de Pagamento**:
   * **Sábado** é o dia mais forte tanto em volume (`164` transações) quanto em ticket médio (`342,20`), seguido por **Terça-feira** (`158` transações). **Segunda-feira** é o dia mais fraco em fluxo (`125` vendas) e cesta média (`303,19`), sendo o candidato natural para campanhas promocionais de ativação.
   * Nos pagamentos, **Ewallet** (`345` vendas) e **Cash** (`344` vendas) dividem a liderança em empate técnico (somando `68,9%` das transações), com **Credit card** em `31,1%` (`311` vendas).

---

## Visualizações Geradas

### Desempenho por Filial
| Faturamento por Filial | Transações por Filial |
|:---:|:---:|
| ![Faturamento por Filial](resultados/faturamento_por_filial.png) | ![Transações por Filial](resultados/transacoes_por_filial.png) |

### Desempenho por Linha de Produto
| Faturamento por Linha de Produto | Avaliação Média por Linha de Produto |
|:---:|:---:|
| ![Faturamento por Linha](resultados/faturamento_por_linha_produto.png) | ![Avaliação Média por Linha](resultados/avaliacao_media_por_linha_produto.png) |

### Formas de Pagamento e Distribuição Temporal
| Transações por Forma de Pagamento | Transações por Dia da Semana |
|:---:|:---:|
| ![Transações por Pagamento](resultados/transacoes_por_pagamento.png) | ![Transações por Dia](resultados/transacoes_por_dia_semana.png) |

---

## Governança e Qualidade de Dados

* **Verificação de Ida e Volta (*Round-Trip*) na Camada Raw**: O script `src/01_leitura_dados.py` compara célula a célula o CSV original com o arquivo `data/raw/vendas_exportadas.csv` extraído via SQL de `public.raw_vendas`, confirmando preservação integral dos 1.000 registros.
* **Papel do ETL e Auditoria de Precisão (`resultados/relatorio_qualidade.csv`)**: Embora a inspeção inicial comprove que o arquivo original não possui células vazias nem IDs duplicados, o pipeline `src/02_etl_vendas.py` aplica validações defensivas de obrigatoriedade, unicidade e regras de domínio (`CHECK`) antes da carga relacional. Na transformação numérica, o ETL valida a fórmula `preco_unitario × quantidade + imposto = valor_total` na precisão original de 4 casas decimais (0 divergências) e, em seguida, padroniza os campos monetários para 2 casas decimais (`NUMERIC(12,2)`), registrando os 838 registros ajustados no relatório de qualidade.