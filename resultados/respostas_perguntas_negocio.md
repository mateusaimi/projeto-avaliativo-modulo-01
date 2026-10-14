# Relatório Analítico e Respostas de Negócio

Consolidação baseada nas **1000 vendas validadas** na camada Tratada (período de 01/01/2019 a 30/03/2019).

## Respostas Diretas

| Pergunta | Resposta | Detalhe |
|---|---|---|
| Qual filial teve maior faturamento? | Giza | 110.568,71 unidades monetárias (soma de valor_total) |
| Qual filial teve mais transações? | Alex | 340 vendas registradas |
| Qual linha de produto gerou maior faturamento? | Food and beverages | 56.144,86 unidades monetárias (soma de valor_total) |
| Qual linha de produto teve maior média de avaliação? | Food and beverages | 7,11 pontos em uma escala de 0 a 10 |
| Qual forma de pagamento foi mais usada? | Ewallet | 345 transações |
| Qual foi o valor médio das vendas? | 322,97 | Ticket médio calculado sobre 1000 vendas (mediana de 253,85) |
| Qual foi o valor da maior venda? | 1.042,65 | ID: 860-79-0874 | Filial: Giza |
| Em qual dia da semana ocorreram mais transações? | Sábado | 164 transações |

## Leitura Analítica para Tomada de Decisão

- **Volume vs. Ticket Médio entre Filiais**: Embora **Alex** lidere em quantidade de transações (340 vendas contra 328 de Giza), **Giza** alcança o maior faturamento total (110.568,71 contra 106.200,37 de Alex) porque opera com um **ticket médio 7,9% superior** (337,10 em Giza vs. 312,35 em Alex). Já Alex e Cairo estão tecnicamente empatadas em faturamento (diferença de apenas 2,63 unidades monetárias no trimestre).
- **Rentabilidade e Satisfação por Categoria**: **Food and beverages** lidera simultaneamente em faturamento (56.144,86) e satisfação do cliente (7,11/10). Em contrapartida, **Fashion accessories** registra o maior número de vendas individuais (178 transações), mas fica em 4º lugar em faturamento (54.305,88) por ter o menor ticket médio entre as linhas (305,09). Já **Health and beauty** apresenta o menor faturamento (49.193,81) devido ao menor fluxo de vendas (152 transações), apesar de manter bom ticket médio (323,64) e avaliação de 7,00.
- **Assimetria do Ticket Médio**: O ticket médio geral é de **322,97**, mas a mediana é de **253,85** (com desvio padrão elevado de 245,89). Isso mostra uma distribuição assimétrica à direita: metade das compras é de até 253,85, enquanto cestas grandes (até 10 unidades de itens próximos a 100,00, como a maior venda `860-79-0874` de 1.042,65 em Giza) puxam a média para cima.
- **Meios de Pagamento e Fluxo Semanal**: **Ewallet** (345) e **Cash** (344) dividem a preferência dos clientes em empate técnico, somando juntos 68,9% das vendas, enquanto **Credit card** responde por 31,1% (311 vendas). Na distribuição semanal, **Sábado** concentra o maior fluxo (164 vendas e maior ticket médio, de 342,20), seguido por **Terça-feira** (158 vendas), enquanto **Segunda-feira** apresenta o menor movimento (125 vendas, ticket médio de 303,19) — indicando os melhores dias para reforço de escala de caixa e campanhas promocionais de início de semana.

## Estatísticas Descritivas

Resumo extraído via `DataFrame.describe()` (exportado também em `estatisticas_descritivas.csv`):

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

## Tabelas-Resumo

### Faturamento por filial

| Categoria | Unidades monetárias |
|---|---:|
| Alex | 106.200,37 |
| Cairo | 106.197,74 |
| Giza | 110.568,71 |

### Transações por filial

| Categoria | Quantidade de vendas |
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

| Categoria | Quantidade de vendas |
|---|---:|
| Cash | 344 |
| Credit card | 311 |
| Ewallet | 345 |

### Transações por dia da semana

| Categoria | Quantidade de vendas |
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

## Notas Metodológicas

- **Faturamento e Ticket Médio**: calculados sobre `valor_total` (`Sales`), que reflete o valor final da nota pago pelo cliente (`preco_unitario * quantidade + imposto`). A coluna `receita_bruta` (`gross income`) corresponde exclusivamente à margem operacional de 5% sobre o custo da mercadoria (`custo_mercadoria`).
- **Precisão Numérica entre Camadas**: Na camada Raw (`raw_vendas`), os valores originais de `Sales` e `Tax 5%` possuem até 4 casas decimais. Na passagem para a camada Tratada (`vendas_tratadas`), cada transação é padronizada para 2 casas decimais (`NUMERIC(12,2)`), motivo pelo qual somatórios agregados diretamente na Raw podem apresentar diferença residual de centavos.
