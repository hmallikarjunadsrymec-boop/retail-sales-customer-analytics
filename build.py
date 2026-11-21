"""Build the SQLite analytics database without bundling PyArrow in the Vercel function."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUILD_DEPS = Path("/tmp/retail-analytics-build-deps")
BUILD_DEPS.mkdir(parents=True, exist_ok=True)

# PyArrow is required only to read the Parquet input during the build. Install
# it outside the repository so Vercel does not package it into the Lambda.
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
     "--target", str(BUILD_DEPS), "pyarrow>=12.0.0"],
    check=True,
)
sys.path.insert(0, str(BUILD_DEPS))
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

# Remove the build-only Parquet file from the deployment output.
source_path = Path(source)
if source_path.exists() and source_path.resolve() != database.resolve():
    source_path.unlink()
    print(f"Removed build-only source dataset: {source_path}")

print(f"Vercel build prepared SQLite database: {database} ({rows:,} rows, {database.stat().st_size:,} bytes)")
