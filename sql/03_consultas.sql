-- Fase 2: consultas de exploracao e agregacao sobre a camada Raw.
-- Os campos numericos ainda sao texto; NULLIF evita erro em campos vazios.

-- Conferir a carga Raw.
SELECT COUNT(*) AS quantidade_linhas
FROM raw_vendas;

SELECT *
FROM raw_vendas
ORDER BY raw_id
LIMIT 10;

-- Exemplo de filtro com WHERE.
SELECT
    "Invoice ID",
    "Branch",
    "Total"
FROM raw_vendas
WHERE "Branch" = 'A'
ORDER BY "Total" DESC
LIMIT 10;

-- Faturamento por filial.
SELECT
    "Branch" AS filial,
    SUM(NULLIF(BTRIM("Total"), '')::NUMERIC) AS faturamento
FROM raw_vendas
GROUP BY "Branch"
ORDER BY faturamento DESC;

-- Quantidade de transacoes por filial.
SELECT
    "Branch" AS filial,
    COUNT(DISTINCT "Invoice ID") AS quantidade_vendas
FROM raw_vendas
GROUP BY "Branch"
ORDER BY quantidade_vendas DESC;

-- Faturamento por linha de produto.
SELECT
    "Product line" AS linha_produto,
    SUM(NULLIF(BTRIM("Total"), '')::NUMERIC) AS faturamento
FROM raw_vendas
GROUP BY "Product line"
ORDER BY faturamento DESC;

-- Avaliacao media por linha de produto.
SELECT
    "Product line" AS linha_produto,
    AVG(NULLIF(BTRIM("Rating"), '')::NUMERIC) AS avaliacao_media
FROM raw_vendas
GROUP BY "Product line"
ORDER BY avaliacao_media DESC;

-- Forma de pagamento mais usada.
SELECT
    "Payment" AS forma_pagamento,
    COUNT(DISTINCT "Invoice ID") AS quantidade_vendas
FROM raw_vendas
GROUP BY "Payment"
ORDER BY quantidade_vendas DESC;

-- Valor medio e maior venda.
WITH vendas AS (
    SELECT DISTINCT ON ("Invoice ID")
        "Invoice ID",
        NULLIF(BTRIM("Total"), '')::NUMERIC AS valor_total
    FROM raw_vendas
    ORDER BY "Invoice ID", raw_id
)
SELECT
    AVG(valor_total) AS valor_medio_venda,
    MAX(valor_total) AS maior_venda
FROM vendas;

-- Quantidade de vendas por dia da semana (ISO: segunda=1, domingo=7).
WITH vendas AS (
    SELECT DISTINCT ON ("Invoice ID")
        "Invoice ID",
        TO_DATE(NULLIF(BTRIM("Date"), ''), 'MM/DD/YYYY') AS data_venda
    FROM raw_vendas
    WHERE "Invoice ID" IS NOT NULL
    ORDER BY "Invoice ID", raw_id
)
SELECT
    CASE EXTRACT(ISODOW FROM data_venda)::INTEGER
        WHEN 1 THEN 'Segunda-feira'
        WHEN 2 THEN 'Terca-feira'
        WHEN 3 THEN 'Quarta-feira'
        WHEN 4 THEN 'Quinta-feira'
        WHEN 5 THEN 'Sexta-feira'
        WHEN 6 THEN 'Sabado'
        WHEN 7 THEN 'Domingo'
    END AS dia_semana,
    COUNT(*) AS quantidade_vendas
FROM vendas
WHERE data_venda IS NOT NULL
GROUP BY EXTRACT(ISODOW FROM data_venda)
ORDER BY quantidade_vendas DESC;

-- A exportacao do SELECT da tabela Raw para
-- data/raw/vendas_exportadas.csv sera feita no script Python 01_leitura_dados.py.
