# Dicionário de dados — camada tratada

Este dicionário segue os tipos e as restrições publicados no enunciado. Os nomes da coluna tratada usam letras minúsculas e snake_case para evitar acentos e espaços nos identificadores SQL.

| Coluna tratada | Coluna de origem no CSV | Tipo PostgreSQL esperado | Regra / interpretação |
|---|---|---|---|
| id_venda | Invoice ID | VARCHAR(50) | Chave primária, NOT NULL. Manter como texto: é um identificador, não uma medida. |
| filial | Branch | VARCHAR(10) | NOT NULL. |
| cidade | City | VARCHAR(100) | NOT NULL. |
| tipo_cliente | Customer type | VARCHAR(50) | Pode ser nulo conforme o dicionário do enunciado. |
| genero | Gender | VARCHAR(20) | Pode ser nulo conforme o dicionário do enunciado. |
| linha_produto | Product line | VARCHAR(150) | NOT NULL. |
| preco_unitario | Unit price | NUMERIC(10,2) | CHECK >= 0. |
| quantidade | Quantity | INTEGER | CHECK > 0. |
| imposto | Tax 5% | NUMERIC(10,2) | CHECK >= 0. |
| valor_total | Total | NUMERIC(12,2) | CHECK >= 0. Valor da transação usado nas métricas de faturamento. Conferir contra o valor original antes de qualquer arredondamento. |
| data_venda | Date | DATE | Converter o texto do CSV para data; confirmar o formato ao inspecionar o arquivo. |
| hora_venda | Time | TIME | Converter o texto do CSV para horário. |
| forma_pagamento | Payment | VARCHAR(50) | NOT NULL. |
| custo_mercadoria | cogs | NUMERIC(12,2) | CHECK >= 0. |
| margem_percentual | gross margin percentage | NUMERIC(10,2) | Preservar o valor de origem com a precisão exigida no enunciado. |
| receita_bruta | gross income | NUMERIC(12,2) | CHECK >= 0. Segue o mapeamento indicado no enunciado; não confundir com Total ao responder faturamento. |
| avaliacao | Rating | NUMERIC(4,2) | CHECK entre 0 e 10. |
| dia_semana | Derivada de data_venda | VARCHAR(15) | Dia da semana em português, derivado de data_venda para responder à pergunta de negócio. |

## Observações de tratamento

- Preservar o CSV original sem alterações na camada Raw; conversões e padronizações pertencem à camada tratada.
- Registrar quantos valores nulos e duplicados foram encontrados antes de decidir como tratá-los.
- A coluna id_venda deve permanecer texto. Não calcular métricas somando identificadores.
- Usar valor_total (origem Total) para faturamento, média e maior venda. A coluna receita_bruta mapeia gross income conforme o dicionário do enunciado e deve ser analisada separadamente.
- O enunciado pede duas casas decimais para vários campos numéricos. Conferir a precisão existente no CSV e documentar qualquer arredondamento aplicado.
