-- =============================================================================
-- PROJETO AVALIATIVO MÓDULO 01 - ANÁLISE DE DADOS COM PYTHON
-- Arquivo: sql/03_consultas.sql
-- Banco: supermarket_sales_db
-- =============================================================================

-- =============================================================================
-- PARTE 1: CONSULTAS FUNDAMENTAIS NA CAMADA RAW
-- Objetivo: Inspecionar e validar a integridade dos dados brutos recém-carregados.
-- Na camada Raw os valores são preservados como texto; conversões pontuais
-- utilizam NULLIF e BTRIM para evitar erros em campos vazios.
-- =============================================================================

-- 1.1. Conferência do volume total de linhas importadas
SELECT COUNT(*) AS total_linhas_raw
FROM raw_vendas;

-- 1.2. Amostragem inicial dos primeiros registros da carga
SELECT *
FROM raw_vendas
ORDER BY raw_id
LIMIT 5;

-- 1.3. Filtro condicional com WHERE (inspeção de vendas de uma filial específica)
SELECT
    "Invoice ID" AS id_venda,
    "Branch"     AS filial,
    "City"       AS cidade,
    "Sales"      AS valor_venda_raw
FROM raw_vendas
WHERE "Branch" = 'Alex'
ORDER BY NULLIF(BTRIM("Sales"), '')::NUMERIC DESC
LIMIT 10;

-- 1.4. Agregação exploratória: faturamento e contagem de transações por filial
SELECT
    "Branch"                                         AS filial,
    COUNT(DISTINCT "Invoice ID")                     AS transacoes_distintas,
    ROUND(SUM(NULLIF(BTRIM("Sales"), '')::NUMERIC), 2) AS faturamento_raw
FROM raw_vendas
GROUP BY "Branch"
ORDER BY faturamento_raw DESC;


-- =============================================================================
-- PARTE 2: VALIDAÇÃO ANALÍTICA NA CAMADA TRATADA (VENDAS_TRATADAS)
-- Objetivo: Responder às perguntas de negócio utilizando a base limpa,
-- tipada nativamente (NUMERIC, DATE, TIME) e com restrições ativas.
-- =============================================================================

-- 2.1. Faturamento total por filial
SELECT
    filial,
    ROUND(SUM(valor_total), 2) AS faturamento_total
FROM vendas_tratadas
GROUP BY filial
ORDER BY faturamento_total DESC;

-- 2.2. Quantidade de vendas distintas por filial
SELECT
    filial,
    COUNT(DISTINCT id_venda) AS quantidade_vendas
FROM vendas_tratadas
GROUP BY filial
ORDER BY quantidade_vendas DESC;

-- 2.3. Faturamento por linha de produto
SELECT
    linha_produto,
    ROUND(SUM(valor_total), 2) AS faturamento_total
FROM vendas_tratadas
GROUP BY linha_produto
ORDER BY faturamento_total DESC;

-- 2.4. Avaliação média dos clientes por linha de produto
SELECT
    linha_produto,
    ROUND(AVG(avaliacao), 2) AS avaliacao_media
FROM vendas_tratadas
GROUP BY linha_produto
ORDER BY avaliacao_media DESC;

-- 2.5. Forma de pagamento mais utilizada
SELECT
    forma_pagamento,
    COUNT(DISTINCT id_venda) AS total_transacoes
FROM vendas_tratadas
GROUP BY forma_pagamento
ORDER BY total_transacoes DESC;

-- 2.6. Valor médio das vendas (ticket médio) e maior venda registrada
SELECT
    ROUND(AVG(valor_total), 2) AS valor_medio_venda,
    ROUND(MAX(valor_total), 2) AS maior_venda_registrada
FROM vendas_tratadas;

-- 2.7. Quantidade de vendas por dia da semana (utilizando a coluna derivada dia_semana)
SELECT
    dia_semana,
    COUNT(DISTINCT id_venda) AS quantidade_vendas
FROM vendas_tratadas
GROUP BY dia_semana
ORDER BY quantidade_vendas DESC;