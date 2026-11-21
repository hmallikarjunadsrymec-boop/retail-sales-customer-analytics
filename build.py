"""
Build the SQLite analytics database for Vercel deployment.
Uses pyarrow installed into a temporary location outside the deployment package
to avoid bundling pyarrow or pandas into the serverless function.
"""
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "processed" / "retail_analytics.db"
PARQUET_PATH = ROOT / "data" / "processed" / "retail_cleaned.parquet"
CSV_PATH = ROOT / "data" / "processed" / "retail_cleaned.csv"
BUILD_DEPS = Path("/tmp/retail-analytics-build-deps")


def build_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.is_file() and DB_PATH.stat().st_size > 1000000:
        print(f"Database already exists at {DB_PATH} ({DB_PATH.stat().st_size:,} bytes).")
        return

    source = PARQUET_PATH if PARQUET_PATH.is_file() else CSV_PATH
    if not source.is_file():
        raise FileNotFoundError(f"Source data file not found at {PARQUET_PATH} or {CSV_PATH}")

    if source.suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError:
            print("Installing temporary build dependency pyarrow into /tmp...")
            BUILD_DEPS.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                    "--no-cache-dir", "--target", str(BUILD_DEPS), "pyarrow>=12.0.0"
                ],
                check=True,
            )
            sys.path.insert(0, str(BUILD_DEPS))
            import pyarrow.parquet as pq

        print(f"Reading {source} via PyArrow...")
        table = pq.read_table(str(source))
    else:
        table = None

    print(f"Creating SQLite schema at {DB_PATH}...")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA page_size = 4096")

    conn.execute("DROP TABLE IF EXISTS sales_transactions")
    conn.execute("""CREATE TABLE sales_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT NOT NULL,
        stock_code TEXT NOT NULL,
        description TEXT,
        quantity INTEGER NOT NULL,
        invoice_date TEXT NOT NULL,
        unit_price REAL NOT NULL,
        customer_id TEXT,
        country TEXT NOT NULL,
        revenue REAL NOT NULL,
        date TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        month_name TEXT NOT NULL,
        year_month TEXT NOT NULL,
        quarter TEXT NOT NULL,
        day_of_week TEXT NOT NULL,
        hour INTEGER NOT NULL,
        order_value REAL NOT NULL,
        category TEXT NOT NULL
    )""")

    insert_sql = """INSERT INTO sales_transactions (
        invoice_no, stock_code, description, quantity, invoice_date, unit_price,
        customer_id, country, revenue, date, year, month, month_name, year_month,
        quarter, day_of_week, hour, order_value, category
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    if table is not None:
        batches = table.to_batches(max_chunksize=50000)
        total_rows = 0
        for b in batches:
            d = b.to_pydict()
            n = len(d["InvoiceNo"])
            total_rows += n
            rows = list(zip(
                [str(x) for x in d["InvoiceNo"]],
                [str(x) for x in d["StockCode"]],
                [str(x) if x is not None else "" for x in d["Description"]],
                [int(x) for x in d["Quantity"]],
                [str(x) for x in d["InvoiceDate"]],
                [float(x) for x in d["UnitPrice"]],
                [str(x) if x is not None else "" for x in d["CustomerID"]],
                [str(x) for x in d["Country"]],
                [float(x) for x in d["Revenue"]],
                [str(x) for x in d["Date"]],
                [int(x) for x in d["Year"]],
                [int(x) for x in d["Month"]],
                [str(x) for x in d["MonthName"]],
                [str(x) for x in d["YearMonth"]],
                [str(x) for x in d["Quarter"]],
                [str(x) for x in d["DayOfWeek"]],
                [int(x) for x in d["Hour"]],
                [float(x) for x in d["OrderValue"]],
                [str(x) for x in d["Category"]]
            ))
            conn.executemany(insert_sql, rows)
    else:
        import csv
        total_rows = 0
        with open(source, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch = []
            for r in reader:
                batch.append((
                    r["InvoiceNo"], r["StockCode"], r.get("Description", ""),
                    int(r["Quantity"]), r["InvoiceDate"], float(r["UnitPrice"]),
                    r.get("CustomerID", ""), r["Country"], float(r["Revenue"]),
                    r["Date"], int(r["Year"]), int(r["Month"]), r["MonthName"],
                    r["YearMonth"], r["Quarter"], r["DayOfWeek"], int(r["Hour"]),
                    float(r["OrderValue"]), r["Category"]
                ))
                if len(batch) >= 25000:
                    conn.executemany(insert_sql, batch)
                    total_rows += len(batch)
                    batch = []
            if batch:
                conn.executemany(insert_sql, batch)
                total_rows += len(batch)

    conn.commit()
    print(f"Ingested {total_rows:,} records into sales_transactions table.")

    # Create indexes for analytical queries
    print("Creating database indexes...")
    conn.execute("CREATE INDEX idx_sales_country_cat ON sales_transactions (country, category)")
    conn.execute("CREATE INDEX idx_sales_year_month ON sales_transactions (year_month)")
    conn.execute("CREATE INDEX idx_sales_invoice ON sales_transactions (invoice_no)")
    conn.execute("CREATE INDEX idx_sales_customer ON sales_transactions (customer_id)")
    conn.execute("CREATE INDEX idx_sales_stock ON sales_transactions (stock_code)")
    conn.commit()

    conn.execute("VACUUM")
    conn.close()

    db_size = DB_PATH.stat().st_size
    print(f"Vercel build prepared SQLite database: {DB_PATH} ({total_rows:,} rows, {db_size:,} bytes)")

    # Clean up build dependencies in /tmp
    if BUILD_DEPS.exists():
        try:
            shutil.rmtree(BUILD_DEPS)
            print(f"Cleaned up temporary build dependencies: {BUILD_DEPS}")
        except Exception as e:
            print(f"Warning: could not delete {BUILD_DEPS}: {e}")

    # Remove the build-only source file to save function package space
    if source.is_file() and source.resolve() != DB_PATH.resolve():
        source.unlink()
        print(f"Removed build-only source dataset: {source}")


if __name__ == "__main__":
    build_database()
