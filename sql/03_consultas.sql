-- Consultas exploratórias (Camada Raw) e analíticas (Camada Tratada).
-- Executar conectado ao banco supermarket_sales_db.

-- Parte 1: Inspeção da camada Raw (tabela raw_vendas)
-- Os campos brutos estão armazenados como TEXT; conversões numéricas pontuais
-- usam BTRIM e NULLIF apenas para ordenação e conferência exploratória.

-- 1.1. Total de linhas carregadas na tabela bruta
SELECT COUNT(*) AS total_linhas_raw
FROM raw_vendas;

-- 1.2. Amostra das 5 primeiras linhas na ordem original do CSV
SELECT *
FROM raw_vendas
ORDER BY raw_id
LIMIT 5;

-- 1.3. Filtro condicional: 10 maiores vendas brutas da filial Alex
SELECT
    "Invoice ID" AS id_venda,
    "Branch"     AS filial,
    "City"       AS cidade,
    "Sales"      AS valor_venda_raw
FROM raw_vendas
WHERE "Branch" = 'Alex'
ORDER BY NULLIF(BTRIM("Sales"), '')::NUMERIC DESC
LIMIT 10;

-- 1.4. Conferência de volume e faturamento bruto por filial
-- Observação: como "Sales" possui até 4 casas decimais no CSV original, a soma
-- direta na Raw resulta em 106.197,67 para Cairo (diferença de 0,07 frente à
-- camada Tratada, onde cada venda é padronizada em NUMERIC(12,2)).
SELECT
    "Branch"                                           AS filial,
    COUNT(DISTINCT "Invoice ID")                       AS transacoes_distintas,
    ROUND(SUM(NULLIF(BTRIM("Sales"), '')::NUMERIC), 2) AS faturamento_raw
FROM raw_vendas
GROUP BY "Branch"
ORDER BY faturamento_raw DESC;

-- 1.5. Consulta base para exportação da camada Raw para CSV (vendas_exportadas.csv)
SELECT *
FROM raw_vendas
ORDER BY raw_id;


-- Parte 2: Respostas às perguntas de negócio na camada Tratada (vendas_tratadas)
-- Como id_venda é PRIMARY KEY NOT NULL nesta tabela, cada registro corresponde
-- a uma única transação validada.

-- 2.1. Pergunta 1: Qual filial apresentou o maior faturamento?
SELECT
    filial,
    cidade,
    ROUND(SUM(valor_total), 2) AS faturamento_total,
    ROUND(AVG(valor_total), 2) AS ticket_medio
FROM vendas_tratadas
GROUP BY filial, cidade
ORDER BY faturamento_total DESC;

-- 2.2. Pergunta 2: Qual filial realizou a maior quantidade de vendas?
SELECT
    filial,
    cidade,
    COUNT(id_venda) AS quantidade_vendas
FROM vendas_tratadas
GROUP BY filial, cidade
ORDER BY quantidade_vendas DESC;

-- 2.3. Pergunta 3: Qual linha de produto apresentou o maior faturamento?
SELECT
    linha_produto,
    COUNT(id_venda)            AS quantidade_vendas,
    ROUND(SUM(valor_total), 2) AS faturamento_total,
    ROUND(AVG(valor_total), 2) AS ticket_medio
FROM vendas_tratadas
GROUP BY linha_produto
ORDER BY faturamento_total DESC;

-- 2.4. Pergunta 4: Qual linha de produto recebeu a melhor avaliação média?
SELECT
    linha_produto,
    ROUND(AVG(avaliacao), 2) AS avaliacao_media,
    MIN(avaliacao)           AS menor_avaliacao,
    MAX(avaliacao)           AS maior_avaliacao
FROM vendas_tratadas
GROUP BY linha_produto
ORDER BY avaliacao_media DESC;

-- 2.5. Pergunta 5: Qual foi a forma de pagamento mais utilizada?
SELECT
    forma_pagamento,
    COUNT(id_venda)            AS total_transacoes,
    ROUND(SUM(valor_total), 2) AS faturamento_total
FROM vendas_tratadas
GROUP BY forma_pagamento
ORDER BY total_transacoes DESC;

-- 2.6. Perguntas 6 e 7 (resumo): Valor médio das vendas e maior venda registrada
SELECT
    COUNT(id_venda)            AS total_transacoes,
    ROUND(AVG(valor_total), 2) AS valor_medio_venda,
    ROUND(MAX(valor_total), 2) AS maior_venda_registrada
FROM vendas_tratadas;

-- 2.7. Pergunta 7 (detalhe): Identificação da maior venda individual
SELECT
    id_venda,
    filial,
    cidade,
    linha_produto,
    quantidade,
    preco_unitario,
    imposto,
    valor_total,
    data_venda
FROM vendas_tratadas
ORDER BY valor_total DESC, id_venda ASC
LIMIT 1;

-- 2.8. Pergunta 8: Em qual dia da semana ocorreu a maior quantidade de vendas?
SELECT
    dia_semana,
    COUNT(id_venda)            AS quantidade_vendas,
    ROUND(SUM(valor_total), 2) AS faturamento_total,
    ROUND(AVG(valor_total), 2) AS ticket_medio
FROM vendas_tratadas
GROUP BY dia_semana
ORDER BY quantidade_vendas DESC;
