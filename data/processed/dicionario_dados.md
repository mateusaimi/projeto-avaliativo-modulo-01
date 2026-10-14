# Dicionário de Dados — Camada Tratada (`vendas_tratadas`)

Mapeamento estrutural entre o arquivo original (`SuperMarket Analysis.csv`) e a tabela relacional `public.vendas_tratadas` (e o arquivo `data/processed/vendas_tratadas.csv`). Os identificadores foram padronizados em `snake_case` e sem acentuação para facilitar consultas SQL.

| Coluna tratada | Coluna de origem no CSV | Tipo PostgreSQL | Regra de negócio e restrições de integridade |
|---|---|---|---|
| `id_venda` | `Invoice ID` | `VARCHAR(50)` | `PRIMARY KEY, NOT NULL`. Código identificador único do cupom fiscal; mantido como texto por ser chave nominal. |
| `filial` | `Branch` | `VARCHAR(10)` | `NOT NULL`. Identificação da unidade (`Alex`, `Cairo` e `Giza`). |
| `cidade` | `City` | `VARCHAR(100)` | `NOT NULL`. Cidade de localização da filial (`Yangon`, `Mandalay` e `Naypyitaw`). |
| `tipo_cliente` | `Customer type` | `VARCHAR(50)` | Perfil de fidelidade do comprador (`Member` ou `Normal`). Permite nulo na modelagem. |
| `genero` | `Gender` | `VARCHAR(20)` | Gênero informado no cadastro (`Female` ou `Male`). Permite nulo na modelagem. |
| `linha_produto` | `Product line` | `VARCHAR(150)` | `NOT NULL`. Categoria mercadológica do item vendido. |
| `preco_unitario` | `Unit price` | `NUMERIC(10,2)` | `CHECK >= 0`. Preço unitário do item antes de impostos. |
| `quantidade` | `Quantity` | `INTEGER` | `CHECK > 0`. Quantidade inteira de itens comprados na transação. |
| `imposto` | `Tax 5%` | `NUMERIC(10,2)` | `CHECK >= 0`. Imposto de 5% incidente sobre o custo da mercadoria (`0,05 * custo_mercadoria`). |
| `valor_total` | `Sales` | `NUMERIC(12,2)` | `CHECK >= 0`. Faturamento bruto da transação pago pelo cliente (`preco_unitario * quantidade + imposto`). Métrica base para cálculo de faturamento e ticket médio. |
| `data_venda` | `Date` | `DATE` | Data de emissão da venda, convertida do padrão americano (`M/D/YYYY`) para `YYYY-MM-DD`. |
| `hora_venda` | `Time` | `TIME` | Horário da transação, convertido do formato de 12 horas (`HH:MM:SS AM/PM`) para 24 horas (`HH:MM:SS`). |
| `forma_pagamento` | `Payment` | `VARCHAR(50)` | `NOT NULL`. Meio de pagamento utilizado (`Ewallet`, `Cash` ou `Credit card`). |
| `custo_mercadoria` | `cogs` | `NUMERIC(12,2)` | `CHECK >= 0`. Custo da mercadoria vendida sem impostos (`preco_unitario * quantidade`). |
| `margem_percentual` | `gross margin percentage` | `NUMERIC(10,2)` | Margem bruta percentual constante na operação (`4,76%` sobre o valor total da nota). |
| `receita_bruta` | `gross income` | `NUMERIC(12,2)` | `CHECK >= 0`. Lucro/margem bruta apurada na venda (`valor_total - custo_mercadoria`). Analisada separadamente do faturamento total. |
| `avaliacao` | `Rating` | `NUMERIC(4,2)` | `CHECK BETWEEN 0 AND 10`. Nota de satisfação atribuída pelo cliente na escala de 0 a 10. |
| `dia_semana` | *(Derivada de `data_venda`)* | `VARCHAR(15)` | Dia da semana em português (`Segunda-feira` a `Domingo`), criado no ETL para análise de sazonalidade semanal. |

## Diretrizes de Tratamento e Qualidade

- **Fidelidade da Camada Raw**: O CSV original é carregado sem tipagem destrutiva em `raw_vendas` (`TEXT`); as conversões de tipo, padronização de nomes e regras de arredondamento ocorrem exclusivamente na passagem para a camada Tratada.
- **Preservação dos Dados Geográficos**: Na base original, `Branch` utiliza os códigos `Alex` (associada a `Yangon`), `Cairo` (`Mandalay`) e `Giza` (`Naypyitaw`). Ambos os campos foram preservados integralmente sem substituições arbitrárias.
- **Precisão Decimal (`NUMERIC`)**: No arquivo de origem, `Tax 5%`, `Sales` e `gross income` possuem até 4 casas decimais em 838 dos 1.000 registros (ex.: `548.9715`), e `gross margin percentage` possui 9 casas (`4.761904762`). O pipeline ETL confere primeiro a consistência exata da fórmula `preco_unitario * quantidade + imposto = valor_total` na precisão original e, em seguida, arredonda os valores monetários para 2 casas decimais (`NUMERIC(10,2)` e `NUMERIC(12,2)`).