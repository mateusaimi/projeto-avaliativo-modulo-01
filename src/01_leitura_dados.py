"""Realiza a inspeção exploratória do CSV original, carrega a tabela Raw e valida a exportação SQL."""

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
SOURCE_CSV = RAW_DIR / "SuperMarket Analysis.csv"
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
    "Sales",
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
    "Sales",
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
    """Lê todos os campos do CSV como texto para preservar a fidelidade na camada Raw."""
    if not SOURCE_CSV.is_file():
        raise FileNotFoundError(
            "Arquivo CSV não encontrado. O arquivo esperado é "
            f"{SOURCE_CSV.name}, em: {RAW_DIR}"
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
            "As colunas do CSV não correspondem à estrutura esperada. "
            f"Ausentes: {missing_columns or 'nenhuma'}. "
            f"Inesperadas: {unexpected_columns or 'nenhuma'}. "
            f"Encontradas: {list(data.columns)}"
        )

    return data[RAW_COLUMNS]


def print_initial_inspection(data: pd.DataFrame) -> None:
    """Exibe diagnóstico estrutural inicial (tipos inferidos, nulos, duplicatas e estatísticas)."""
    # Leitura secundária com inferência de tipos do Pandas apenas para diagnóstico exploratório (EDA)
    inferred = pd.read_csv(SOURCE_CSV, encoding="utf-8-sig")
    print(f"Arquivo analisado: {SOURCE_CSV.name}")
    print(f"Total de linhas: {len(data):,}")
    print(f"Total de colunas: {len(data.columns)}")
    print("\nTipos inferidos pelo Pandas na leitura exploratória:")
    print(inferred.dtypes.to_string())

    blank_counts = data.eq("").sum()
    blanks_found = blank_counts[blank_counts > 0]
    print("\nStrings vazias por coluna:")
    if blanks_found.empty:
        print("Nenhum campo vazio encontrado.")
    else:
        print(blanks_found.to_string())

    missing_counts = inferred.isna().sum()
    missing_found = missing_counts[missing_counts > 0]
    print("\nValores nulos (NaN) na leitura exploratória:")
    if missing_found.empty:
        print("Nenhum valor ausente encontrado nas 1.000 linhas.")
    else:
        print(missing_found.to_string())

    numeric_summary = inferred.describe().T
    print("\nEstatísticas descritivas iniciais das colunas numéricas:")
    if numeric_summary.empty:
        print("Nenhuma coluna numérica foi inferida automaticamente.")
    else:
        print(numeric_summary.to_string())

    exact_duplicates = int(data.duplicated().sum())
    duplicate_ids = int(data["Invoice ID"].duplicated().sum())
    print(f"\nLinhas inteiramente duplicadas: {exact_duplicates}")
    print(f"IDs de venda (Invoice ID) repetidos: {duplicate_ids}")
    print("\nAmostra das cinco primeiras linhas:")
    print(data.head().to_string(index=False))


def make_engine() -> Engine:
    """Cria a conexão com o PostgreSQL usando variáveis definidas no arquivo .env."""
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


def load_raw_table(data: pd.DataFrame, engine: Engine) -> int:
    """Limpa a carga anterior e insere os registros brutos como texto na tabela raw_vendas."""
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


def export_raw_query(engine: Engine) -> pd.DataFrame:
    """Executa consulta SQL na tabela raw_vendas e exporta o resultado para CSV."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    exported = pd.read_sql_query(text(EXPORT_QUERY), con=engine)
    exported.to_csv(EXPORTED_CSV, index=False, encoding="utf-8-sig")
    return exported


def verify_raw_round_trip(source: pd.DataFrame, exported: pd.DataFrame) -> None:
    """Compara o CSV original com o CSV exportado do banco para atestar integridade da carga Raw."""
    if source.shape != exported.shape or list(source.columns) != list(exported.columns):
        raise RuntimeError(
            "A exportação da tabela Raw diverge das dimensões do CSV original: "
            f"original={source.shape}, exportada={exported.shape}."
        )

    source_values = source.astype("string").fillna("")
    exported_values = exported.astype("string").fillna("")
    matches = source_values.eq(exported_values).all(axis=1)
    if not bool(matches.all()):
        different_rows = matches.index[~matches].tolist()
        examples = []
        for row_index in different_rows[:5]:
            different_columns = source_values.columns[
                source_values.iloc[row_index].ne(exported_values.iloc[row_index])
            ]
            examples.append(
                f"linha CSV {row_index + 2}: {list(different_columns)}"
            )
        raise RuntimeError(
            f"{len(different_rows)} linhas diferem do CSV original após a carga no banco. "
            f"Exemplos: {examples}"
        )


def main() -> None:
    data = read_source_csv()
    print_initial_inspection(data)

    engine = make_engine()
    try:
        loaded_count = load_raw_table(data, engine)
        exported = export_raw_query(engine)
        exported_count = len(exported)
        verify_raw_round_trip(data, exported)
    except SQLAlchemyError as error:
        print(
            "Falha ao conectar ou gravar no PostgreSQL. Verifique se o serviço está ativo, "
            "se os scripts 01 e 02 em sql/ foram executados e se o arquivo .env está correto."
        )
        print(f"Detalhe técnico: {error.__class__.__name__}")
        sys.exit(1)
    finally:
        engine.dispose()

    print(f"\nRegistros carregados em public.raw_vendas: {loaded_count}")
    print(
        "Registros exportados via SQL para "
        f"{EXPORTED_CSV.relative_to(PROJECT_ROOT)}: {exported_count}"
    )
    print("Conferência de integridade Raw: 100% dos campos e a ordem das linhas conferem.")

    if loaded_count != len(data) or exported_count != loaded_count:
        raise RuntimeError(
            "Divergência na contagem de linhas entre CSV original, banco e exportação."
        )


if __name__ == "__main__":
    main()
    