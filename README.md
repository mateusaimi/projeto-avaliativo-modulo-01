# Projeto Avaliativo Módulo 01 — Análise de Vendas de Supermercado

> Status: estrutura inicial. O pipeline e os resultados serão completados e conferidos durante o desenvolvimento.

## Objetivo

Organizar os registros de vendas em uma camada bruta e uma camada tratada, usar SQL e Pandas para preparar os dados e responder às perguntas de negócio do Projeto Avaliativo do Módulo 01.

## Fonte dos dados

Dataset Supermarket Sales, indicado no enunciado: https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales

O arquivo original deverá ser mantido em data/raw/ sem edição manual. O formato e as colunas serão conferidos antes da carga.

## Pré-requisitos previstos

- Python 3.14 ou outra versão compatível com as dependências registradas em requirements.txt.
- PostgreSQL e pgAdmin (ou outra ferramenta SQL).
- Git e VS Code.
- Conta GitHub para publicar o repositório e enviar o link no AVA.

As credenciais locais do banco ficarão em um arquivo .env, ignorado pelo Git. Use .env.example como modelo e nunca publique a senha.

## Etapas previstas

1. Baixar o CSV original e preservá-lo em data/raw/.
2. Criar o banco e as tabelas Raw e Tratada no PostgreSQL.
3. Consultar os dados com SQL e exportar o resultado para CSV.
4. Inspecionar e tratar os dados com Pandas.
5. Salvar a base tratada, calcular as métricas e gerar gráficos.

## Estrutura

- sql/: criação do banco, criação de tabelas e consultas.
- src/: leitura e inspeção, ETL e análise estatística.
- data/raw/: arquivo original e exportações SQL.
- data/processed/: base tratada e dicionário de dados.
- resultados/: respostas e gráficos.

## Execução

Os comandos finais serão acrescentados após a implementação do pipeline. A ordem de execução prevista é:

1. Criar o banco com sql/01_criar_banco.sql.
2. Criar as tabelas Raw e Tratada com sql/02_criar_tabelas.sql.
3. Carregar o CSV original na tabela Raw e executar sql/03_consultas.sql.
4. Executar src/01_leitura_dados.py e src/02_etl_vendas.py.
5. Executar src/03_estatistica.py para salvar as métricas e os gráficos.

Consulte data/processed/dicionario_dados.md para o mapeamento entre as colunas do CSV e a camada tratada.

## Resultados

As respostas às perguntas de negócio e as visualizações serão documentadas aqui quando a análise estiver concluída.
