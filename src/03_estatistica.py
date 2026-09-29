"""Responde as perguntas de negocio e gera tabelas e graficos descritivos."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

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
    """Formata um valor com separadores usados em textos em portugues."""
    formatted = f"{value:,.2f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def format_ties(values: pd.Index) -> str:
    """Converte um ou mais nomes empatados em uma frase legivel."""
    names = [str(value) for value in values]
    if not names:
        return "Sem dados validos"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " e " + names[-1]


def tied_max(series: pd.Series) -> pd.Index:
    """Retorna todos os indices que compartilham o maior valor."""
    maximum = series.max()
    return series.index[series.eq(maximum)]


def read_processed_data() -> pd.DataFrame:
    """Carrega a camada tratada e verifica as colunas necessarias."""
    if not INPUT_CSV.is_file():
        raise FileNotFoundError(
            "Base tratada nao encontrada. Execute primeiro "
            "src/02_etl_vendas.py."
        )

    data = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    missing = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing:
        raise ValueError(f"Colunas necessarias ausentes na base tratada: {missing}")
    if data.empty:
        raise ValueError("A base tratada nao possui linhas para analisar.")

    data["valor_total"] = pd.to_numeric(data["valor_total"], errors="coerce")
    data["avaliacao"] = pd.to_numeric(data["avaliacao"], errors="coerce")
    data["data_venda"] = pd.to_datetime(data["data_venda"], errors="coerce")
    data = data.dropna(
        subset=["id_venda", "filial", "linha_produto", "valor_total", "forma_pagamento"]
    ).copy()
    if data.empty:
        raise ValueError("Nao ha registros completos para responder as perguntas.")
    if data["data_venda"].isna().all() or data["dia_semana"].isna().all():
        raise ValueError(
            "Nao ha datas validas na camada tratada. "
            "Confira resultados/relatorio_qualidade.csv."
        )
    if data["avaliacao"].isna().all():
        raise ValueError(
            "Nao ha avaliacoes validas na camada tratada. "
            "Confira resultados/relatorio_qualidade.csv."
        )
    if data["id_venda"].duplicated().any():
        raise ValueError(
            "A camada tratada ainda tem IDs de venda repetidos. "
            "Revise o ETL antes da analise."
        )
    return data


def create_aggregates(data: pd.DataFrame) -> dict[str, pd.Series]:
    """Calcula agregacoes reutilizadas nas respostas e nos graficos."""
    return {
        "revenue_by_branch": data.groupby("filial")["valor_total"].sum().sort_index(),
        "sales_by_branch": data.groupby("filial")["id_venda"].nunique().sort_index(),
        "revenue_by_product": (
            data.groupby("linha_produto")["valor_total"].sum().sort_index()
        ),
        "rating_by_product": (
            data.groupby("linha_produto")["avaliacao"].mean().dropna().sort_index()
        ),
        "sales_by_payment": (
            data.groupby("forma_pagamento")["id_venda"].nunique().sort_index()
        ),
        "sales_by_weekday": (
            data.dropna(subset=["dia_semana"])
            .groupby("dia_semana")["id_venda"]
            .nunique()
            .reindex(DAY_ORDER, fill_value=0)
        ),
    }


def build_answers(
    data: pd.DataFrame, aggregates: dict[str, pd.Series]
) -> list[dict[str, str]]:
    """Cria as oito respostas diretas pedidas no enunciado."""
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

    max_sale_value = data["valor_total"].max()
    max_sales = data.loc[
        data["valor_total"].eq(max_sale_value), ["id_venda", "filial"]
    ]
    transaction_count = int(data["id_venda"].nunique())
    average_sale = float(data.groupby("id_venda")["valor_total"].first().mean())
    top_branch_revenue_value = float(branch_revenue.loc[top_branch_revenue].max())
    top_product_revenue_value = float(product_revenue.loc[top_product_revenue].max())
    top_product_rating_value = float(product_rating.loc[top_product_rating].max())

    return [
        {
            "pergunta": "Qual filial teve maior faturamento?",
            "resposta": format_ties(top_branch_revenue),
            "detalhe": (
                f"{format_number(top_branch_revenue_value)} "
                "unidades monetarias (soma de valor_total)"
            ),
        },
        {
            "pergunta": "Qual filial teve mais transacoes?",
            "resposta": format_ties(top_branch_sales),
            "detalhe": (
                f"{int(branch_sales.loc[top_branch_sales].max())} transacoes "
                "(IDs de venda distintos)"
            ),
        },
        {
            "pergunta": "Qual linha de produto gerou maior faturamento?",
            "resposta": format_ties(top_product_revenue),
            "detalhe": (
                f"{format_number(top_product_revenue_value)} "
                "unidades monetarias (soma de valor_total)"
            ),
        },
        {
            "pergunta": "Qual linha de produto teve maior media de avaliacao?",
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
                f"{int(payment_sales.loc[top_payment].max())} transacoes "
                "(IDs de venda distintos)"
            ),
        },
        {
            "pergunta": "Qual foi o valor medio das vendas?",
            "resposta": format_number(average_sale),
            "detalhe": (
                f"Media calculada sobre {transaction_count} transacoes distintas; "
                "unidade monetaria nao informada na fonte"
            ),
        },
        {
            "pergunta": "Qual foi o valor da maior venda?",
            "resposta": format_number(float(max_sale_value)),
            "detalhe": (
                f"IDs: {', '.join(max_sales['id_venda'].astype(str))}; "
                f"filiais: {', '.join(max_sales['filial'].astype(str).unique())}; "
                "unidade monetaria nao informada na fonte"
            ),
        },
        {
            "pergunta": "Em qual dia da semana ocorreram mais transacoes?",
            "resposta": format_ties(top_weekday),
            "detalhe": (
                f"{int(weekday_sales.loc[top_weekday].max())} transacoes "
                "(IDs de venda distintos)"
            ),
        },
    ]


def save_chart(series: pd.Series, title: str, ylabel: str, filename: str) -> None:
    """Salva um grafico de barras legivel a partir de uma agregacao."""
    figure_width = max(8, len(series.index) * 1.15)
    figure, axis = plt.subplots(figsize=(figure_width, 5.2))
    bars = axis.bar(series.index.astype(str), series.values, color="#2878B5")
    axis.set_title(title, fontsize=14, pad=14)
    axis.set_ylabel(ylabel)
    axis.set_xlabel("")
    axis.grid(axis="y", linestyle="--", alpha=0.3)
    axis.set_axisbelow(True)
    label_format = "%.2f" if series.dtype.kind == "f" else "%d"
    axis.bar_label(bars, fmt=label_format, padding=3)
    axis.tick_params(axis="x", labelrotation=20)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / filename, dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_charts(aggregates: dict[str, pd.Series]) -> list[str]:
    """Gera um grafico para cada comparacao categorica da analise."""
    charts = [
        (
            "revenue_by_branch",
            "Faturamento por filial",
            "Soma de valor_total",
            "faturamento_por_filial.png",
        ),
        (
            "sales_by_branch",
            "Transacoes por filial",
            "Transacoes distintas",
            "transacoes_por_filial.png",
        ),
        (
            "revenue_by_product",
            "Faturamento por linha de produto",
            "Soma de valor_total",
            "faturamento_por_linha_produto.png",
        ),
        (
            "rating_by_product",
            "Avaliacao media por linha de produto",
            "Media da avaliacao (0 a 10)",
            "avaliacao_media_por_linha_produto.png",
        ),
        (
            "sales_by_payment",
            "Transacoes por forma de pagamento",
            "Transacoes distintas",
            "transacoes_por_pagamento.png",
        ),
        (
            "sales_by_weekday",
            "Transacoes por dia da semana",
            "Transacoes distintas",
            "transacoes_por_dia_semana.png",
        ),
    ]
    for key, title, ylabel, filename in charts:
        save_chart(aggregates[key], title, ylabel, filename)
    return [filename for _, _, _, filename in charts]


def create_descriptive_statistics(data: pd.DataFrame) -> pd.DataFrame:
    """Resume as colunas numericas com estatisticas descritivas do Pandas."""
    numeric_data = data.select_dtypes(include="number")
    if numeric_data.empty:
        raise ValueError("A camada tratada nao possui colunas numericas analisaveis.")
    return numeric_data.describe().T.round(2)


def save_markdown(
    data: pd.DataFrame,
    answers: list[dict[str, str]],
    aggregates: dict[str, pd.Series],
    descriptive: pd.DataFrame,
    charts: list[str],
) -> None:
    """Documenta respostas, metodologia e tabelas-resumo junto aos graficos."""
    lines = [
        "# Respostas às perguntas de negócio",
        "",
        f"Análise de **{data['id_venda'].nunique()} transações distintas** "
        f"({len(data)} linhas na camada tratada).",
        "",
        "> A fonte não especifica a moeda. Os valores monetários são apresentados "
        "> em unidades monetárias, sem atribuir símbolo de moeda.",
        "",
        "## Respostas",
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
            "## Estatísticas descritivas",
            "",
            "O resumo abaixo foi calculado com `DataFrame.describe()` do Pandas. "
            "A tabela completa também está em `estatisticas_descritivas.csv`.",
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
        ("Transações por filial", "sales_by_branch", "Transações distintas"),
        (
            "Faturamento por linha de produto",
            "revenue_by_product",
            "Unidades monetarias",
        ),
        (
            "Media de avaliacao por linha de produto",
            "rating_by_product",
            "Pontos (0 a 10)",
        ),
        (
            "Transacoes por forma de pagamento",
            "sales_by_payment",
            "Transacoes distintas",
        ),
        ("Transações por dia da semana", "sales_by_weekday", "Transações distintas"),
    ]
    lines.extend(["", "## Tabelas-resumo", ""])
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
    for chart in charts:
        title = chart.removesuffix(".png").replace("_", " ").capitalize()
        lines.extend([f"### {title}", "", f"![{title}](./{chart})", ""])

    lines.extend(
        [
            "## Critérios de cálculo",
            "",
            (
                "- Faturamento: soma de `valor_total` (coluna `Sales` da fonte, "
                "equivalente a Total no enunciado)."
            ),
            "- Quantidade de transações: contagem de IDs de venda distintos.",
            "- Avaliação média: média de `avaliacao`, ignorando valores ausentes.",
            "- Venda média: média de um `valor_total` por ID de venda distinto.",
            (
                "- Dia da semana: derivado de `data_venda`; dias sem transações "
                "aparecem com zero no gráfico."
            ),
            "- Empates na maior categoria são apresentados em conjunto.",
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

    print(f"Transacoes analisadas: {data['id_venda'].nunique()}")
    print(f"Respostas salvas em: {ANSWERS_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Estatisticas salvas em: {DESCRIPTIVE_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Relatorio salvo em: {ANSWERS_MD.relative_to(PROJECT_ROOT)}")
    print(f"Graficos gerados: {len(charts)}")


if __name__ == "__main__":
    main()
