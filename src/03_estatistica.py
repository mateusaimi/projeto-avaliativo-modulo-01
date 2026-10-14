"""Calcula estatísticas descritivas, responde às perguntas de negócio e gera visualizações."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "vendas_tratadas.csv"
OUTPUT_DIR = PROJECT_ROOT / "resultados"
ANSWERS_CSV = OUTPUT_DIR / "respostas_perguntas_negocio.csv"
ANSWERS_MD = OUTPUT_DIR / "respostas_perguntas_negocio.md"
DESCRIPTIVE_CSV = OUTPUT_DIR / "estatisticas_descritivas.csv"

REQUIRED_COLUMNS = {
    "id_venda",
    "filial",
    "linha_produto",
    "valor_total",
    "avaliacao",
    "forma_pagamento",
    "data_venda",
    "dia_semana",
}
DAY_ORDER = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]


def format_number(value: float) -> str:
    """Formata números decimais no padrão brasileiro (ponto para milhar e vírgula para decimal)."""
    formatted = f"{value:,.2f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def format_ties(values: pd.Index) -> str:
    """Formata um ou mais rótulos vencedores caso haja empate técnico."""
    names = [str(value) for value in values]
    if not names:
        return "Sem dados válidos"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " e " + names[-1]


def tied_max(series: pd.Series) -> pd.Index:
    """Retorna os índices que alcançaram o valor máximo da série."""
    maximum = series.max()
    return series.index[series.eq(maximum)]


def read_processed_data() -> pd.DataFrame:
    """Lê a base já higienizada pela etapa de ETL (vendas_tratadas.csv)."""
    if not INPUT_CSV.is_file():
        raise FileNotFoundError(
            "Base tratada não encontrada. Execute primeiro "
            "src/02_etl_vendas.py."
        )

    data = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    missing = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes na base tratada: {missing}")
    if data.empty:
        raise ValueError("A base tratada está vazia.")

    data["data_venda"] = pd.to_datetime(data["data_venda"], errors="coerce")
    return data


def create_aggregates(data: pd.DataFrame) -> dict[str, pd.Series]:
    """Calcula as séries agregadas utilizadas nas respostas de negócio e nos gráficos."""
    return {
        "revenue_by_branch": data.groupby("filial")["valor_total"].sum().sort_index(),
        "sales_by_branch": data.groupby("filial")["id_venda"].count().sort_index(),
        "revenue_by_product": (
            data.groupby("linha_produto")["valor_total"].sum().sort_index()
        ),
        "rating_by_product": (
            data.groupby("linha_produto")["avaliacao"].mean().dropna().sort_index()
        ),
        "sales_by_payment": (
            data.groupby("forma_pagamento")["id_venda"].count().sort_index()
        ),
        "sales_by_weekday": (
            data.groupby("dia_semana")["id_venda"]
            .count()
            .reindex(DAY_ORDER, fill_value=0)
        ),
    }


def build_answers(
    data: pd.DataFrame, aggregates: dict[str, pd.Series]
) -> list[dict[str, str]]:
    """ Consolida as respostas das oito perguntas de negócio."""
    branch_revenue = aggregates["revenue_by_branch"]
    branch_sales = aggregates["sales_by_branch"]
    product_revenue = aggregates["revenue_by_product"]
    product_rating = aggregates["rating_by_product"]
    payment_sales = aggregates["sales_by_payment"]
    weekday_sales = aggregates["sales_by_weekday"]

    top_branch_revenue = tied_max(branch_revenue)
    top_branch_sales = tied_max(branch_sales)
    top_product_revenue = tied_max(product_revenue)
    top_product_rating = tied_max(product_rating)
    top_payment = tied_max(payment_sales)
    top_weekday = tied_max(weekday_sales[weekday_sales > 0])

    max_sale_value = float(data["valor_total"].max())
    max_sales = data.loc[
        data["valor_total"].eq(max_sale_value), ["id_venda", "filial"]
    ]
    transaction_count = len(data)
    average_sale = float(data["valor_total"].mean())
    top_branch_revenue_value = float(branch_revenue.loc[top_branch_revenue].max())
    top_product_revenue_value = float(product_revenue.loc[top_product_revenue].max())
    top_product_rating_value = float(product_rating.loc[top_product_rating].max())

    return [
        {
            "pergunta": "Qual filial teve maior faturamento?",
            "resposta": format_ties(top_branch_revenue),
            "detalhe": (
                f"{format_number(top_branch_revenue_value)} "
                "unidades monetárias (soma de valor_total)"
            ),
        },
        {
            "pergunta": "Qual filial teve mais transações?",
            "resposta": format_ties(top_branch_sales),
            "detalhe": (
                f"{int(branch_sales.loc[top_branch_sales].max())} vendas registradas"
            ),
        },
        {
            "pergunta": "Qual linha de produto gerou maior faturamento?",
            "resposta": format_ties(top_product_revenue),
            "detalhe": (
                f"{format_number(top_product_revenue_value)} "
                "unidades monetárias (soma de valor_total)"
            ),
        },
        {
            "pergunta": "Qual linha de produto teve maior média de avaliação?",
            "resposta": format_ties(top_product_rating),
            "detalhe": (
                f"{format_number(top_product_rating_value)} "
                "pontos em uma escala de 0 a 10"
            ),
        },
        {
            "pergunta": "Qual forma de pagamento foi mais usada?",
            "resposta": format_ties(top_payment),
            "detalhe": (
                f"{int(payment_sales.loc[top_payment].max())} transações"
            ),
        },
        {
            "pergunta": "Qual foi o valor médio das vendas?",
            "resposta": format_number(average_sale),
            "detalhe": (
                f"Ticket médio calculado sobre {transaction_count} vendas "
                f"(mediana de {format_number(float(data['valor_total'].median()))})"
            ),
        },
        {
            "pergunta": "Qual foi o valor da maior venda?",
            "resposta": format_number(max_sale_value),
            "detalhe": (
                f"ID: {', '.join(max_sales['id_venda'].astype(str))} | "
                f"Filial: {', '.join(max_sales['filial'].astype(str).unique())}"
            ),
        },
        {
            "pergunta": "Em qual dia da semana ocorreram mais transações?",
            "resposta": format_ties(top_weekday),
            "detalhe": (
                f"{int(weekday_sales.loc[top_weekday].max())} transações"
            ),
        },
    ]


def save_chart(series: pd.Series, title: str, ylabel: str, filename: str) -> None:
    """Gera e exporta um gráfico de barras padronizado com rótulos de dados."""
    figure_width = max(8, len(series.index) * 1.15)
    figure, axis = plt.subplots(figsize=(figure_width, 5.2))
    bars = axis.bar(series.index.astype(str), series.values, color="#2878B5")
    axis.set_title(title, fontsize=14, pad=14)
    axis.set_ylabel(ylabel)
    axis.set_xlabel("")
    axis.grid(axis="y", linestyle="--", alpha=0.3)
    axis.set_axisbelow(True)
    labels = (
        [format_number(float(value)) for value in series.values]
        if series.dtype.kind == "f"
        else [f"{int(value):,}".replace(",", ".") for value in series.values]
    )
    axis.bar_label(bars, labels=labels, padding=3)
    axis.tick_params(axis="x", labelrotation=20)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / filename, dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_charts(aggregates: dict[str, pd.Series]) -> list[str]:
    """Gera os seis gráficos comparativos na pasta resultados/."""
    charts = [
        (
            "revenue_by_branch",
            "Faturamento por filial",
            "Faturamento (unidades monetárias)",
            "faturamento_por_filial.png",
        ),
        (
            "sales_by_branch",
            "Transações por filial",
            "Quantidade de vendas",
            "transacoes_por_filial.png",
        ),
        (
            "revenue_by_product",
            "Faturamento por linha de produto",
            "Faturamento (unidades monetárias)",
            "faturamento_por_linha_produto.png",
        ),
        (
            "rating_by_product",
            "Avaliação média por linha de produto",
            "Média da avaliação (0 a 10)",
            "avaliacao_media_por_linha_produto.png",
        ),
        (
            "sales_by_payment",
            "Transações por forma de pagamento",
            "Quantidade de vendas",
            "transacoes_por_pagamento.png",
        ),
        (
            "sales_by_weekday",
            "Transações por dia da semana",
            "Quantidade de vendas",
            "transacoes_por_dia_semana.png",
        ),
    ]
    for key, title, ylabel, filename in charts:
        save_chart(aggregates[key], title, ylabel, filename)
    return [filename for _, _, _, filename in charts]


def create_descriptive_statistics(data: pd.DataFrame) -> pd.DataFrame:
    """Calcula estatísticas descritivas (contagem, média, desvio padrão e quartis)."""
    numeric_data = data.select_dtypes(include="number")
    if numeric_data.empty:
        raise ValueError("A camada tratada não possui colunas numéricas analisáveis.")
    return numeric_data.describe().T.round(2)


def save_markdown(
    data: pd.DataFrame,
    answers: list[dict[str, str]],
    aggregates: dict[str, pd.Series],
    descriptive: pd.DataFrame,
    charts: list[str],
) -> None:
    """Consolida respostas, interpretação de negócio, tabelas e gráficos em Markdown."""
    lines = [
        "# Relatório Analítico e Respostas de Negócio",
        "",
        f"Consolidação baseada nas **{len(data)} vendas validadas** na camada Tratada "
        "(período de 01/01/2019 a 30/03/2019).",
        "",
        "## Respostas Diretas",
        "",
        "| Pergunta | Resposta | Detalhe |",
        "|---|---|---|",
    ]
    for answer in answers:
        lines.append(
            f"| {answer['pergunta']} | {answer['resposta']} | {answer['detalhe']} |"
        )

    lines.extend(
        [
            "",
            "## Leitura Analítica para Tomada de Decisão",
            "",
            "- **Volume vs. Ticket Médio entre Filiais**: Embora **Alex** lidere em quantidade de transações (340 vendas contra 328 de Giza), **Giza** alcança o maior faturamento total (110.568,71 contra 106.200,37 de Alex) porque opera com um **ticket médio 7,9% superior** (337,10 em Giza vs. 312,35 em Alex). Já Alex e Cairo estão tecnicamente empatadas em faturamento (diferença de apenas 2,63 unidades monetárias no trimestre).",
            "- **Rentabilidade e Satisfação por Categoria**: **Food and beverages** lidera simultaneamente em faturamento (56.144,86) e satisfação do cliente (7,11/10). Em contrapartida, **Fashion accessories** registra o maior número de vendas individuais (178 transações), mas fica em 4º lugar em faturamento (54.305,88) por ter o menor ticket médio entre as linhas (305,09). Já **Health and beauty** apresenta o menor faturamento (49.193,81) devido ao menor fluxo de vendas (152 transações), apesar de manter bom ticket médio (323,64) e avaliação de 7,00.",
            "- **Assimetria do Ticket Médio**: O ticket médio geral é de **322,97**, mas a mediana é de **253,85** (com desvio padrão elevado de 245,89). Isso mostra uma distribuição assimétrica à direita: metade das compras é de até 253,85, enquanto cestas grandes (até 10 unidades de itens próximos a 100,00, como a maior venda `860-79-0874` de 1.042,65 em Giza) puxam a média para cima.",
            "- **Meios de Pagamento e Fluxo Semanal**: **Ewallet** (345) e **Cash** (344) dividem a preferência dos clientes em empate técnico, somando juntos 68,9% das vendas, enquanto **Credit card** responde por 31,1% (311 vendas). Na distribuição semanal, **Sábado** concentra o maior fluxo (164 vendas e maior ticket médio, de 342,20), seguido por **Terça-feira** (158 vendas), enquanto **Segunda-feira** apresenta o menor movimento (125 vendas, ticket médio de 303,19) — indicando os melhores dias para reforço de escala de caixa e campanhas promocionais de início de semana.",
            "",
            "## Estatísticas Descritivas",
            "",
            "Resumo extraído via `DataFrame.describe()` (exportado também em `estatisticas_descritivas.csv`):",
            "",
            (
                "| Variável | Contagem | Média | Desvio padrão | Mínimo | "
                "25% | Mediana | 75% | Máximo |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for variable, statistics in descriptive.iterrows():
        values = []
        for name in descriptive.columns:
            value = statistics[name]
            if pd.isna(value):
                values.append("—")
            elif name == "count":
                values.append(str(int(value)))
            else:
                values.append(format_number(float(value)))
        lines.append(f"| {variable} | " + " | ".join(values) + " |")

    table_specs = [
        ("Faturamento por filial", "revenue_by_branch", "Unidades monetárias"),
        ("Transações por filial", "sales_by_branch", "Quantidade de vendas"),
        (
            "Faturamento por linha de produto",
            "revenue_by_product",
            "Unidades monetárias",
        ),
        (
            "Média de avaliação por linha de produto",
            "rating_by_product",
            "Pontos (0 a 10)",
        ),
        (
            "Transações por forma de pagamento",
            "sales_by_payment",
            "Quantidade de vendas",
        ),
        ("Transações por dia da semana", "sales_by_weekday", "Quantidade de vendas"),
    ]
    lines.extend(["", "## Tabelas-Resumo", ""])
    for title, key, value_title in table_specs:
        lines.extend(
            [f"### {title}", "", f"| Categoria | {value_title} |", "|---|---:|"]
        )
        for category, value in aggregates[key].items():
            if pd.isna(value):
                formatted_value = "Sem avaliação"
            elif pd.api.types.is_integer_dtype(aggregates[key].dtype):
                formatted_value = str(int(value))
            else:
                formatted_value = format_number(float(value))
            lines.append(f"| {category} | {formatted_value} |")
        lines.append("")

    lines.extend(["## Gráficos", ""])
    chart_titles = {
        "faturamento_por_filial.png": "Faturamento por filial",
        "transacoes_por_filial.png": "Transações por filial",
        "faturamento_por_linha_produto.png": "Faturamento por linha de produto",
        "avaliacao_media_por_linha_produto.png": "Avaliação média por linha de produto",
        "transacoes_por_pagamento.png": "Transações por forma de pagamento",
        "transacoes_por_dia_semana.png": "Transações por dia da semana",
    }
    for chart in charts:
        title = chart_titles[chart]
        lines.extend([f"### {title}", "", f"![{title}](./{chart})", ""])

    lines.extend(
        [
            "## Notas Metodológicas",
            "",
            "- **Faturamento e Ticket Médio**: calculados sobre `valor_total` (`Sales`), que reflete o valor final da nota pago pelo cliente (`preco_unitario * quantidade + imposto`). A coluna `receita_bruta` (`gross income`) corresponde exclusivamente à margem operacional de 5% sobre o custo da mercadoria (`custo_mercadoria`).",
            "- **Precisão Numérica entre Camadas**: Na camada Raw (`raw_vendas`), os valores originais de `Sales` e `Tax 5%` possuem até 4 casas decimais. Na passagem para a camada Tratada (`vendas_tratadas`), cada transação é padronizada para 2 casas decimais (`NUMERIC(12,2)`), motivo pelo qual somatórios agregados diretamente na Raw podem apresentar diferença residual de centavos.",
            "",
        ]
    )
    ANSWERS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = read_processed_data()
    aggregates = create_aggregates(data)
    answers = build_answers(data, aggregates)
    descriptive = create_descriptive_statistics(data)
    descriptive.index.name = "variavel"
    pd.DataFrame(answers).to_csv(ANSWERS_CSV, index=False, encoding="utf-8-sig")
    descriptive.to_csv(
        DESCRIPTIVE_CSV,
        index_label="variavel",
        encoding="utf-8-sig",
    )
    charts = save_charts(aggregates)
    save_markdown(data, answers, aggregates, descriptive, charts)

    print(f"Vendas analisadas: {len(data)}")
    print(f"Respostas salvas em: {ANSWERS_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Estatísticas salvas em: {DESCRIPTIVE_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Relatório analítico salvo em: {ANSWERS_MD.relative_to(PROJECT_ROOT)}")
    print(f"Gráficos gerados: {len(charts)}")


if __name__ == "__main__":
    main()
    