"""
dlt Load Pipeline — moves data from Lake DB to Warehouse DB.
Uses merge write disposition so running twice produces identical results.
"""

import os
import dlt
from dlt.sources.sql_database import sql_database
from dotenv import load_dotenv

load_dotenv()

ENTITIES = [
    "customers",
    "products",
    "stores",
    "employees",
    "orders",
    "order_items",
    "payments",
    "payment_methods",
    "inventory_movements",
]


def run_load_pipeline():
    print("Starting dlt load pipeline...")

    lake_host = os.environ.get("LAKE_DB_HOST", "localhost")
    lake_port = int(os.environ.get("LAKE_DB_PORT", 5433))
    lake_db = os.environ.get("LAKE_DB_NAME", "lake")
    lake_user = os.environ.get("LAKE_DB_USER", "postgres")
    lake_password = os.environ.get("LAKE_DB_PASSWORD", "postgres123")
    lake_connection_string = (
        f"postgresql+psycopg2://{lake_user}:{lake_password}@{lake_host}:{lake_port}/{lake_db}"
    )

    source = sql_database(
        credentials=lake_connection_string,
        schema="raw",
        table_names=ENTITIES,
    )

    pipeline = dlt.pipeline(
        pipeline_name="retailco_lake_to_warehouse",
        destination=dlt.destinations.postgres(
            credentials={
                "host": os.environ.get("WAREHOUSE_DB_HOST", "localhost"),
                "port": int(os.environ.get("WAREHOUSE_DB_PORT", 5434)),
                "database": os.environ.get("WAREHOUSE_DB_NAME", "warehouse"),
                "username": os.environ.get("WAREHOUSE_DB_USER", "postgres"),
                "password": os.environ.get("WAREHOUSE_DB_PASSWORD", "postgres123"),
            }
        ),
        dataset_name="raw",
    )

    info = pipeline.run(
        source,
        write_disposition="merge",
        primary_key="id"
    )

    print(f"Load complete: {info}")

    return {
    "status": "SUCCESS"
}