"""Inspeciona o CSV original, carrega a camada Raw e exporta uma consulta."""

from pathlib import Path
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
SOURCE_CSV = RAW_DIR / "supermarket_sales.csv"
EXPORTED_CSV = RAW_DIR / "vendas_exportadas.csv"
DOTENV_PATH = PROJECT_ROOT / ".env"

RAW_COLUMNS = [
    "Invoice ID",
    "Branch",
    "City",
    "Customer type",
    "Gender",
    "Product line",
    "Unit price",
    "Quantity",
    "Tax 5%",
    "Total",
    "Date",
    "Time",
    "Payment",
    "cogs",
    "gross margin percentage",
    "gross income",
    "Rating",
]

EXPORT_QUERY = '''
SELECT
    "Invoice ID",
    "Branch",
    "City",
    "Customer type",
    "Gender",
    "Product line",
    "Unit price",
    "Quantity",
    "Tax 5%",
    "Total",
    "Date",
    "Time",
    "Payment",
    "cogs",
    "gross margin percentage",
    "gross income",
    "Rating"
FROM public.raw_vendas
ORDER BY raw_id
'''


def read_source_csv() -> pd.DataFrame:
    """Lê os campos do CSV como texto para preservar a camada Raw."""
    if not SOURCE_CSV.is_file():
        raise FileNotFoundError(
            "CSV nao encontrado. Salve o arquivo original com o nome "
            f"supermarket_sales.csv em: {RAW_DIR}"
        )

    data = pd.read_csv(
        SOURCE_CSV,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    missing_columns = [column for column in RAW_COLUMNS if column not in data.columns]
    unexpected_columns = [
        column for column in data.columns if column not in RAW_COLUMNS
    ]
    if missing_columns or unexpected_columns:
        raise ValueError(
            "As colunas do CSV nao correspondem ao arquivo esperado. "
            f"Ausentes: {missing_columns or 'nenhuma'}. "
            f"Inesperadas: {unexpected_columns or 'nenhuma'}. "
            f"Encontradas: {list(data.columns)}"
        )

    return data[RAW_COLUMNS]


def print_initial_inspection(data: pd.DataFrame) -> None:
    """Exibe estrutura, valores vazios, duplicidades e amostra do CSV."""
    inferred = pd.read_csv(SOURCE_CSV, encoding="utf-8-sig")
    print(f"Arquivo: {SOURCE_CSV.name}")
    print(f"Linhas: {len(data):,}")
    print(f"Colunas: {len(data.columns)}")
    print("\nTipos inferidos pelo Pandas na leitura exploratoria:")
    print(inferred.dtypes.to_string())

    blank_counts = data.eq("").sum()
    blanks_found = blank_counts[blank_counts > 0]
    print("\nCampos vazios por coluna:")
    if blanks_found.empty:
        print("Nenhum campo vazio encontrado.")
    else:
        print(blanks_found.to_string())

    missing_counts = inferred.isna().sum()
    missing_found = missing_counts[missing_counts > 0]
    print("\nValores ausentes detectados na leitura exploratoria:")
    if missing_found.empty:
        print("Nenhum valor ausente encontrado.")
    else:
        print(missing_found.to_string())

    numeric_summary = inferred.describe().T
    print("\nEstatisticas descritivas basicas das colunas numericas:")
    if numeric_summary.empty:
        print("Nenhuma coluna numerica foi inferida automaticamente.")
    else:
        print(numeric_summary.to_string())

    exact_duplicates = int(data.duplicated().sum())
    duplicate_ids = int(data["Invoice ID"].duplicated().sum())
    print(f"Linhas totalmente duplicadas: {exact_duplicates}")
    print(f"IDs de venda repetidos: {duplicate_ids}")
    print("\nPrimeiras cinco linhas conforme o CSV original:")
    print(data.head().to_string(index=False))


def make_engine() -> Engine:
    """Cria a conexao local com credenciais carregadas de .env."""
    load_dotenv(DOTENV_PATH)
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(
            f"Configure estas variaveis no arquivo .env: {', '.join(missing)}"
        )

    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url, pool_pre_ping=True)


def load_raw_table(data: pd.DataFrame, engine: Engine) -> int:
    """Substitui a carga anterior e insere os valores originais como texto."""
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE public.raw_vendas RESTART IDENTITY"))
        data.to_sql(
            name="raw_vendas",
            schema="public",
            con=connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )

        loaded_count = connection.execute(
            text("SELECT COUNT(*) FROM public.raw_vendas")
        ).scalar_one()

    return int(loaded_count)


def export_raw_query(engine: Engine) -> int:
    """Exporta o resultado de um SELECT do PostgreSQL para CSV."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    exported = pd.read_sql_query(text(EXPORT_QUERY), con=engine)
    exported.to_csv(EXPORTED_CSV, index=False, encoding="utf-8-sig")
    return len(exported)


def main() -> None:
    data = read_source_csv()
    print_initial_inspection(data)

    engine = make_engine()
    try:
        loaded_count = load_raw_table(data, engine)
        exported_count = export_raw_query(engine)
    except SQLAlchemyError as error:
        print(
            "Falha ao acessar o PostgreSQL. Confira se o servico esta ativo, "
            "se o banco e as tabelas foram criados e se o arquivo .env esta correto."
        )
        print(f"Detalhe: {error.__class__.__name__}")
        sys.exit(1)
    finally:
        engine.dispose()

    print(f"\nRegistros carregados em raw_vendas: {loaded_count}")
    print(
        "Registros exportados para "
        f"{EXPORTED_CSV.relative_to(PROJECT_ROOT)}: {exported_count}"
    )

    if loaded_count != len(data) or exported_count != loaded_count:
        raise RuntimeError(
            "A quantidade de linhas mudou entre CSV, Raw e exportacao. "
            "Interrompa a etapa e investigue antes de transformar os dados."
        )


if __name__ == "__main__":
    main()
