"""Etapa 2 do pipeline: limpeza, conversão de tipos, criação de colunas derivadas e carga na tabela vendas_tratadas."""

from pathlib import Path
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTED_CSV = PROJECT_ROOT / "data" / "raw" / "vendas_exportadas.csv"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "vendas_tratadas.csv"
QUALITY_REPORT = PROJECT_ROOT / "resultados" / "relatorio_qualidade.csv"
DOTENV_PATH = PROJECT_ROOT / ".env"

SOURCE_TO_TARGET = {
    "Invoice ID": "id_venda",
    "Branch": "filial",
    "City": "cidade",
    "Customer type": "tipo_cliente",
    "Gender": "genero",
    "Product line": "linha_produto",
    "Unit price": "preco_unitario",
    "Quantity": "quantidade",
    "Tax 5%": "imposto",
    "Sales": "valor_total",
    "Date": "data_venda",
    "Time": "hora_venda",
    "Payment": "forma_pagamento",
    "cogs": "custo_mercadoria",
    "gross margin percentage": "margem_percentual",
    "gross income": "receita_bruta",
    "Rating": "avaliacao",
}

TEXT_COLUMNS = [
    "id_venda",
    "filial",
    "cidade",
    "tipo_cliente",
    "genero",
    "linha_produto",
    "forma_pagamento",
]
NUMERIC_COLUMNS = [
    "preco_unitario",
    "quantidade",
    "imposto",
    "valor_total",
    "custo_mercadoria",
    "margem_percentual",
    "receita_bruta",
    "avaliacao",
]
NONNEGATIVE_COLUMNS = [
    "preco_unitario",
    "imposto",
    "valor_total",
    "custo_mercadoria",
    "receita_bruta",
]
REQUIRED_COLUMNS = ["id_venda", "filial", "cidade", "linha_produto", "forma_pagamento"]
DAY_NAMES_PT = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def read_exported_csv() -> pd.DataFrame:
    """Lê o CSV exportado da camada Raw e aplica o mapeamento de colunas para snake_case."""
    if not EXPORTED_CSV.is_file():
        raise FileNotFoundError(
            "Arquivo exportado não encontrado. Execute primeiro "
            "src/01_leitura_dados.py."
        )

    data = pd.read_csv(
        EXPORTED_CSV,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    expected = list(SOURCE_TO_TARGET)
    missing = [column for column in expected if column not in data.columns]
    extra = [column for column in data.columns if column not in expected]
    if missing or extra:
        raise ValueError(
            "As colunas exportadas não correspondem ao esquema esperado. "
            f"Ausentes: {missing or 'nenhuma'}. "
            f"Inesperadas: {extra or 'nenhuma'}."
        )

    data = data[expected].rename(columns=SOURCE_TO_TARGET)
    for column in data.columns:
        data[column] = data[column].replace("", pd.NA)
    return data


def remove_duplicate_sales(data: pd.DataFrame, audit: dict) -> pd.DataFrame:
    """Garante unicidade da chave primária (id_venda) antes da carga no banco."""
    missing_id = data["id_venda"].isna()
    audit["linhas_sem_id_removidas"] = int(missing_id.sum())
    data = data.loc[~missing_id].copy()

    duplicate_rows = data.loc[data["id_venda"].duplicated(keep=False)]
    if not duplicate_rows.empty:
        distinct_values = duplicate_rows.groupby("id_venda").nunique(dropna=False)
        conflict_ids = distinct_values.index[distinct_values.gt(1).any(axis=1)]
        if len(conflict_ids):
            examples = list(conflict_ids[:5])
            raise ValueError(
                "Foram encontrados IDs de venda repetidos com dados divergentes entre si. "
                f"Verifique na camada Raw: {examples}"
            )

    duplicate_mask = data["id_venda"].duplicated(keep="first")
    audit["duplicidades_por_id_removidas"] = int(duplicate_mask.sum())
    return data.loc[~duplicate_mask].copy()


def convert_numeric_columns(data: pd.DataFrame, audit: dict) -> pd.DataFrame:
    """Converte colunas numéricas e aplica as regras de domínio (CHECK constraints)."""
    for column in NUMERIC_COLUMNS:
        original = data[column]
        converted = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & converted.isna()
        audit[f"valores_numericos_invalidos_{column}"] = int(invalid.sum())
        data[column] = converted

    quantity = data["quantidade"]
    fractional_quantity = quantity.notna() & (quantity % 1 != 0)
    audit["quantidades_nao_inteiras"] = int(fractional_quantity.sum())

    # Vendas sem quantidade/valores financeiros válidos ou com valores negativos são descartadas
    invalid_domain = fractional_quantity.copy()
    invalid_domain |= quantity.isna() | (quantity <= 0)
    for column in NONNEGATIVE_COLUMNS:
        invalid_domain |= data[column].isna() | (data[column] < 0)

    audit["linhas_fora_das_regras_numericas_removidas"] = int(invalid_domain.sum())
    data = data.loc[~invalid_domain].copy()

    # Se apenas a nota de avaliação estiver fora da escala [0, 10], preserva-se a venda anulando a nota
    invalid_rating = data["avaliacao"].notna() & (
        (data["avaliacao"] < 0) | (data["avaliacao"] > 10)
    )
    audit["avaliacoes_fora_da_faixa_convertidas_em_nulo"] = int(invalid_rating.sum())
    data.loc[invalid_rating, "avaliacao"] = pd.NA

    data["quantidade"] = data["quantidade"].astype("Int64")
    return data


def convert_dates_and_times(data: pd.DataFrame, audit: dict) -> pd.DataFrame:
    """Converte datas (M/D/YYYY) e horários (12h AM/PM) e deriva o dia da semana."""
    date_source = data["data_venda"]
    parsed_dates = pd.to_datetime(
        date_source,
        format="%m/%d/%Y",
        errors="coerce",
    )
    invalid_dates = date_source.notna() & parsed_dates.isna()
    audit["datas_nao_convertidas"] = int(invalid_dates.sum())

    time_source = data["hora_venda"]
    parsed_times = pd.to_datetime(
        time_source,
        format="%I:%M:%S %p",
        errors="coerce",
    )
    invalid_times = time_source.notna() & parsed_times.isna()
    audit["horarios_nao_convertidos"] = int(invalid_times.sum())

    data["data_venda"] = parsed_dates.dt.date
    data["hora_venda"] = parsed_times.dt.time
    data["dia_semana"] = parsed_dates.dt.dayofweek.map(DAY_NAMES_PT).astype("string")
    return data


def check_total_calculation(data: pd.DataFrame, audit: dict) -> None:
    """Confere a fórmula valor_total = preco_unitario * quantidade + imposto na precisão original."""
    needed = ["preco_unitario", "quantidade", "imposto", "valor_total"]
    comparable = data[needed].notna().all(axis=1)
    expected_total = (
        data.loc[comparable, "preco_unitario"] * data.loc[comparable, "quantidade"]
        + data.loc[comparable, "imposto"]
    )
    difference = (data.loc[comparable, "valor_total"] - expected_total).abs()
    audit["totais_com_diferenca_maior_que_0_01"] = int((difference > 0.01).sum())


def save_outputs(data: pd.DataFrame, audit: dict) -> None:
    """Padroniza precisão de 2 casas decimais e salva o CSV tratado e o relatório de auditoria."""
    for column in NUMERIC_COLUMNS:
        rounded = data[column].round(2)
        changed = data[column].notna() & data[column].ne(rounded)
        audit[f"valores_arredondados_2_casas_{column}"] = int(changed.sum())
        data[column] = rounded

    PROCESSED_CSV.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(
        PROCESSED_CSV,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )

    audit["linhas_apos_tratamento"] = len(data)
    audit_frame = pd.DataFrame(
        [{"verificacao": key, "quantidade": value} for key, value in audit.items()]
    )
    audit_frame.to_csv(QUALITY_REPORT, index=False, encoding="utf-8-sig")


def make_engine() -> Engine:
    """Cria a conexão com o PostgreSQL a partir das variáveis do arquivo .env."""
    load_dotenv(DOTENV_PATH)
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(
            f"Configure as seguintes variáveis no arquivo .env: {', '.join(missing)}"
        )

    url = URL.create(
        drivername="postgresql+pg8000",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url, pool_pre_ping=True)


def load_treated_table(data: pd.DataFrame, engine: Engine) -> int:
    """Recarrega public.vendas_tratadas com TRUNCATE para preservar as constraints DDL da tabela."""
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE public.vendas_tratadas"))
        data.to_sql(
            name="vendas_tratadas",
            schema="public",
            con=connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )
        loaded_count = connection.execute(
            text("SELECT COUNT(*) FROM public.vendas_tratadas")
        ).scalar_one()
    return int(loaded_count)


def main() -> None:
    data = read_exported_csv()
    audit = {"linhas_na_exportacao_sql": len(data)}
    for column in data.columns:
        audit[f"valores_ausentes_antes_do_tratamento_{column}"] = int(
            data[column].isna().sum()
        )
    data = remove_duplicate_sales(data, audit)

    missing_required = data[REQUIRED_COLUMNS].isna().any(axis=1)
    audit["linhas_sem_campos_obrigatorios_removidas"] = int(missing_required.sum())
    data = data.loc[~missing_required].copy()

    data = convert_numeric_columns(data, audit)
    check_total_calculation(data, audit)
    data = convert_dates_and_times(data, audit)
    save_outputs(data, audit)

    print(f"Linhas lidas da exportação SQL: {audit['linhas_na_exportacao_sql']}")
    print(f"Linhas válidas na camada Tratada: {len(data)}")
    removed_row_count = sum(
        audit[key]
        for key in (
            "linhas_sem_id_removidas",
            "duplicidades_por_id_removidas",
            "linhas_sem_campos_obrigatorios_removidas",
            "linhas_fora_das_regras_numericas_removidas",
        )
    )
    print(f"Registros descartados por violação de regras: {removed_row_count}")
    print(f"Registros com ajuste de precisão para 2 casas decimais (valor_total): {audit['valores_arredondados_2_casas_valor_total']}")
    print(f"Base tratada salva em: {PROCESSED_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Relatório de qualidade salvo em: {QUALITY_REPORT.relative_to(PROJECT_ROOT)}")

    engine = make_engine()
    try:
        loaded_count = load_treated_table(data, engine)
    except SQLAlchemyError as error:
        print(
            "A base tratada foi salva em CSV, mas houve falha ao carregar no PostgreSQL. "
            "Verifique a tabela vendas_tratadas, suas constraints e o arquivo .env."
        )
        print(f"Detalhe técnico: {error.__class__.__name__}")
        sys.exit(1)
    finally:
        engine.dispose()

    print(f"Registros carregados em public.vendas_tratadas: {loaded_count}")
    if loaded_count != len(data):
        raise RuntimeError(
            "A quantidade de linhas gravadas no banco difere do CSV tratado."
        )


if __name__ == "__main__":
    main()
    