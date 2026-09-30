# Respostas às perguntas de negócio

Análise de **1000 transações distintas** (1000 linhas na camada tratada).

> A fonte não especifica a moeda. Os valores monetários são apresentados em unidades monetárias, sem atribuir símbolo de moeda.

## Respostas

| Pergunta | Resposta | Detalhe |
|---|---|---|
| Qual filial teve maior faturamento? | Giza | 110.568,71 unidades monetárias (soma de valor_total) |
| Qual filial teve mais transações? | Alex | 340 transações (IDs de venda distintos) |
| Qual linha de produto gerou maior faturamento? | Food and beverages | 56.144,86 unidades monetárias (soma de valor_total) |
| Qual linha de produto teve maior média de avaliação? | Food and beverages | 7,11 pontos em uma escala de 0 a 10 |
| Qual forma de pagamento foi mais usada? | Ewallet | 345 transações (IDs de venda distintos) |
| Qual foi o valor médio das vendas? | 322,97 | Média calculada sobre 1000 transações distintas; unidade monetária não informada na fonte |
| Qual foi o valor da maior venda? | 1.042,65 | IDs: 860-79-0874; filiais: Giza; unidade monetária não informada na fonte |
| Em qual dia da semana ocorreram mais transações? | Sábado | 164 transações (IDs de venda distintos) |

## Estatísticas descritivas

O resumo abaixo foi calculado com `DataFrame.describe()` do Pandas. A tabela completa também está em `estatisticas_descritivas.csv`.

| Variável | Contagem | Média | Desvio padrão | Mínimo | 25% | Mediana | 75% | Máximo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preco_unitario | 1000 | 55,67 | 26,49 | 10,08 | 32,88 | 55,23 | 77,94 | 99,96 |
| quantidade | 1000 | 5,51 | 2,92 | 1,00 | 3,00 | 5,00 | 8,00 | 10,00 |
| imposto | 1000 | 15,38 | 11,71 | 0,51 | 5,93 | 12,09 | 22,44 | 49,65 |
| valor_total | 1000 | 322,97 | 245,89 | 10,68 | 124,42 | 253,85 | 471,35 | 1.042,65 |
| custo_mercadoria | 1000 | 307,59 | 234,18 | 10,17 | 118,50 | 241,76 | 448,90 | 993,00 |
| margem_percentual | 1000 | 4,76 | 0,00 | 4,76 | 4,76 | 4,76 | 4,76 | 4,76 |
| receita_bruta | 1000 | 15,38 | 11,71 | 0,51 | 5,93 | 12,09 | 22,44 | 49,65 |
| avaliacao | 1000 | 6,97 | 1,72 | 4,00 | 5,50 | 7,00 | 8,50 | 10,00 |

## Tabelas-resumo

### Faturamento por filial

| Categoria | Unidades monetárias |
|---|---:|
| Alex | 106.200,37 |
| Cairo | 106.197,74 |
| Giza | 110.568,71 |

### Transações por filial

| Categoria | Transações distintas |
|---|---:|
| Alex | 340 |
| Cairo | 332 |
| Giza | 328 |

### Faturamento por linha de produto

| Categoria | Unidades monetárias |
|---|---:|
| Electronic accessories | 54.337,52 |
| Fashion accessories | 54.305,88 |
| Food and beverages | 56.144,86 |
| Health and beauty | 49.193,81 |
| Home and lifestyle | 53.861,87 |
| Sports and travel | 55.122,88 |

### Média de avaliação por linha de produto

| Categoria | Pontos (0 a 10) |
|---|---:|
| Electronic accessories | 6,92 |
| Fashion accessories | 7,03 |
| Food and beverages | 7,11 |
| Health and beauty | 7,00 |
| Home and lifestyle | 6,84 |
| Sports and travel | 6,92 |

### Transações por forma de pagamento

| Categoria | Transações distintas |
|---|---:|
| Cash | 344 |
| Credit card | 311 |
| Ewallet | 345 |

### Transações por dia da semana

| Categoria | Transações distintas |
|---|---:|
| Segunda-feira | 125 |
| Terça-feira | 158 |
| Quarta-feira | 143 |
| Quinta-feira | 138 |
| Sexta-feira | 139 |
| Sábado | 164 |
| Domingo | 133 |

## Gráficos

### Faturamento por filial

![Faturamento por filial](./faturamento_por_filial.png)

### Transações por filial

![Transações por filial](./transacoes_por_filial.png)

### Faturamento por linha de produto

![Faturamento por linha de produto](./faturamento_por_linha_produto.png)

### Avaliação média por linha de produto

![Avaliação média por linha de produto](./avaliacao_media_por_linha_produto.png)

### Transações por forma de pagamento

![Transações por forma de pagamento](./transacoes_por_pagamento.png)

### Transações por dia da semana

![Transações por dia da semana](./transacoes_por_dia_semana.png)

## Critérios de cálculo

- Faturamento: soma de `valor_total` (coluna `Sales` da fonte, equivalente a Total no enunciado).
- Quantidade de transações: contagem de IDs de venda distintos.
- Avaliação média: média de `avaliacao`, ignorando valores ausentes.
- Venda média: média de um `valor_total` por ID de venda distinto.
- Dia da semana: derivado de `data_venda`; dias sem transações aparecem com zero no gráfico.
- Empates na maior categoria são apresentados em conjunto.
- Valores numéricos foram arredondados para duas casas decimais na camada Tratada; a fórmula de valor_total foi conferida antes desse arredondamento.
- Como a camada Raw mantém a precisão original, totais agrupados diretamente nela podem diferir por centavos dos totais da camada Tratada.
