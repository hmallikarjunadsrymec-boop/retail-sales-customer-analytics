"""Prepare the read-only SQLite analytics database during the Vercel build."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.sql_engine import DB_PATH, PARQUET_PATH, CSV_PATH, load_cleaned_data_to_sql

source = PARQUET_PATH if Path(PARQUET_PATH).is_file() else CSV_PATH
if not Path(source).is_file():
    raise FileNotFoundError(
        "No processed sales dataset found. Expected "
        "data/processed/retail_cleaned.parquet or retail_cleaned.csv."
    )

rows = load_cleaned_data_to_sql(db_path=DB_PATH, data_path=source)
database = Path(DB_PATH)
if not database.is_file() or database.stat().st_size == 0:
    raise RuntimeError("SQLite database build failed: database file is missing or empty.")

# The Parquet source is needed only during the build. Keeping it in the
# deployed Python function wastes bundle space; the generated SQLite DB is
# the runtime data source.
source_path = Path(source)
if source_path.exists() and source_path.resolve() != database.resolve():
    source_path.unlink()
    print(f"Removed build-only source dataset: {source_path}")

print(f"Vercel build prepared SQLite database: {database} ({rows:,} rows, {database.stat().st_size:,} bytes)")
