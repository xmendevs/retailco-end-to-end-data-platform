"""
RetailCo ERP Extractor
======================
Pulls data from the ERP API and writes it to the Lake PostgreSQL database.

How it works:
1. For each entity (customers, orders, etc.), check if we ran before (watermark)
2. If we ran before, only fetch records updated since last run (incremental)
3. If first time, fetch everything (full extract)
4. Upsert (insert-or-update) each row — running twice produces the same result
5. Save the highest updated_at timestamp as the new watermark
"""

import os
import time
import json
import logging
import requests
import psycopg2  # type: ignore[import]
import psycopg2.extras  # type: ignore[import]
from datetime import datetime, timezone
from typing import Any, Dict, Optional
try:
    # python-dotenv provides load_dotenv; some environments / linters may
    # report it as unresolved. Fall back to a no-op if not installed.
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without python-dotenv
    def load_dotenv(*args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.warning("python-dotenv not available; continuing without loading .env file")
        return False

# Load variables from the .env file
load_dotenv()

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Configuration ────────────────────────────────────────────────────────────
API_KEY  = os.environ.get("ERP_API_KEY", "")
BASE_URL = os.environ.get("ERP_BASE_URL", "https://hngstage8da-55c7f5f769c8.herokuapp.com")

print("=" * 50)
print("ERP_API_KEY =", repr(API_KEY))
print("=" * 50)

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}
MAX_RETRIES = 5      # Maximum number of retry attempts per request
PAGE_SIZE   = 100    # How many records to fetch per API page

# Database connection settings
DB_CONFIG = {
    "host":     os.environ.get("LAKE_DB_HOST", "localhost"),
    "port":     int(os.environ.get("LAKE_DB_PORT", 5433)),
    "dbname":   os.environ.get("LAKE_DB_NAME", "lake"),
    "user":     os.environ.get("LAKE_DB_USER", "postgres"),
    "password": os.environ.get("LAKE_DB_PASSWORD", "postgres123"),
}

print("=" * 50)
print("DB CONFIG")
print(DB_CONFIG)
print("=" * 50)

# ── IMPORTANT: Update these entity names after checking the Swagger UI ────────
# These are the API endpoint paths (after the base URL)
ENTITIES = [
    "stores",
    "employees",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "inventory_movements",
    "payment_methods",
]


# ── HTTP Request with Retry + Backoff ────────────────────────────────────────
def fetch_with_retry(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Makes a GET request to the API.
    
    Automatically handles:
    - 429 (Rate Limited): waits for however long the API says, then retries
    - 500/502/503/504 (Server Error): waits with exponential backoff, then retries
    - Timeout: retries with exponential backoff
    
    Raises an exception if all retries fail.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"GET {url} params={params} (attempt {attempt})")

           # logger.info(f"API_KEY loaded: {repr(API_KEY)}")
            #logger.info(f"HEADERS being sent: {HEADERS}")

            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30,
            )

            # ── Success ──────────────────────────────────────────────────────
            if response.status_code == 200:
                return response.json()

            # ── Rate Limited (429) ───────────────────────────────────────────
            elif response.status_code == 429:
                # The API tells us how long to wait in the Retry-After header
                wait_seconds = int(response.headers.get("Retry-After", 60))
                logger.warning(
                    f"Rate limited by API. Waiting {wait_seconds} seconds before retry..."
                )
                time.sleep(wait_seconds)
                # Don't count this as an "attempt" failure — keep trying

            # ── Server Error (500s) ──────────────────────────────────────────
            elif response.status_code in (500, 502, 503, 504):
                # Wait: 2^1=2s, 2^2=4s, 2^3=8s, 2^4=16s seconds
                wait_seconds = (2 ** attempt)
                logger.warning(
                    f"Server error {response.status_code}. "
                    f"Attempt {attempt}/{MAX_RETRIES}. "
                    f"Waiting {wait_seconds}s..."
                )
                time.sleep(wait_seconds)

            # ── Other errors (401, 404, etc.) ────────────────────────────────
            else:
                # These won't get better with retries
                logger.error(f"API error {response.status_code}: {response.text}")
                response.raise_for_status()

        except requests.exceptions.Timeout:
            wait_seconds = (2 ** attempt)
            logger.warning(
                f"Request timed out. Attempt {attempt}/{MAX_RETRIES}. "
                f"Waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)

        except requests.exceptions.ConnectionError as e:
            wait_seconds = (2 ** attempt)
            logger.warning(f"Connection error: {e}. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds)

    # If we reach here, all attempts failed
    raise Exception(
        f"Failed to fetch {url} after {MAX_RETRIES} attempts. "
        "Check your internet connection and API key."
    )


# ── Pagination ────────────────────────────────────────────────────────────────
def paginate_entity(entity: str, updated_after: Optional[str] = None):
    """
    Fetches all pages of data for one entity.
    
    The API uses cursor-based pagination:
    - First request: fetch first page
    - If has_more=True: use the cursor from the response to fetch the next page
    - Repeat until has_more=False
    
    Yields: list of rows for each page
    
    NOTE: The cursor field name might differ. Check the Swagger UI.
    Common names: "next_cursor", "cursor", "next_page"
    """
    url = f"{BASE_URL}/{entity}/"
    params: dict[str, Any] = {"limit": PAGE_SIZE}

    # For incremental loads, only fetch records updated after this timestamp
    if updated_after:
        params["updated_after"] = updated_after
    page_num = 0
    total_rows = 0

    while True:
        data = fetch_with_retry(url, params)
        page_num += 1

        # ── Extract rows from response ────────────────────────────────────────
        # APIs often wrap data in a key. Check the Swagger UI.
        # Common patterns: {"data": [...], "has_more": true}
        #                  {"items": [...], "cursor": "abc123"}
        #                  {"results": [...]}
        rows = (
            data.get("data")
            or data.get("items")
            or data.get("results")
            or (data if isinstance(data, list) else [])
        )

        total_rows += len(rows)
        logger.info(f"  Page {page_num}: {len(rows)} rows (total so far: {total_rows})")

        yield rows

        # ── Check if there are more pages ────────────────────────────────────
        meta = data.get("meta", {})
        has_more = meta.get("has_more", False)
        if not has_more:
            break

        # ── Get the cursor for the next page ─────────────────────────────────
        # Check the Swagger UI for the exact field name
        cursor = meta.get("cursor")

        if not cursor:
            # No cursor found even though has_more=True
            logger.warning(f"has_more=True but no cursor found in response. Stopping.")
            break

        # Set cursor for next request; remove updated_after (cursor encodes it)
        params = {"limit": PAGE_SIZE, "cursor": cursor}

    logger.info(f"  Finished: {total_rows} total rows from /{entity}")


# ── Database Setup ────────────────────────────────────────────────────────────
def get_db_connection():
    """Opens a connection to the lake PostgreSQL database."""
    return psycopg2.connect(**DB_CONFIG)


def ensure_raw_schema_and_watermarks(conn):
    """
    Creates the raw schema (if it doesn't exist) and the watermarks table.
    
    The watermarks table stores the last successful extract timestamp per entity.
    This is how we know where to start the next incremental load.
    """
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw._watermarks (
                entity          TEXT        PRIMARY KEY,
                last_updated_at TIMESTAMPTZ,
                last_run_at     TIMESTAMPTZ DEFAULT now(),
                rows_extracted  BIGINT      DEFAULT 0
            );
        """)
    conn.commit()
    logger.info("Schema 'raw' and watermarks table verified.")


def get_watermark(conn, entity: str) -> str | None:
    """
    Returns the last watermark (timestamp) for an entity.
    Returns None if this entity has never been extracted before.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_updated_at FROM raw._watermarks WHERE entity = %s",
            (entity,)
        )
        row = cur.fetchone()

    if row and row[0]:
        ts = row[0].isoformat()
        logger.info(f"  Found watermark: {ts}")
        return ts

    logger.info(f"  No watermark found — will do full extract")
    return None


def save_watermark(conn, entity: str, timestamp: str, row_count: int):
    """
    Saves the new watermark after a successful extract.
    Uses UPSERT so it works for both first run and subsequent runs.
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO raw._watermarks (entity, last_updated_at, last_run_at, rows_extracted)
            VALUES (%s, %s, now(), %s)
            ON CONFLICT (entity) DO UPDATE SET
                last_updated_at = EXCLUDED.last_updated_at,
                last_run_at     = now(),
                rows_extracted  = EXCLUDED.rows_extracted;
        """, (entity, timestamp, row_count))
    conn.commit()


def ensure_entity_table(conn, entity: str, sample_row: dict):
    """
    Creates the table for an entity if it doesn't exist yet.
    Derives column types from the first row of data.
    
    This is a "schema-on-arrival" approach — we don't pre-define schemas.
    The table shape comes from what the API actually returns.
    """
    columns_sql = []

    for col_name, value in sample_row.items():
        # Determine PostgreSQL type from Python type
        if col_name == "id":
            col_type = "TEXT PRIMARY KEY"
        elif isinstance(value, bool):
            col_type = "BOOLEAN"
        elif isinstance(value, int):
            col_type = "BIGINT"
        elif isinstance(value, float):
            col_type = "NUMERIC"
        elif isinstance(value, dict) or isinstance(value, list):
            col_type = "JSONB"  # Store nested objects as JSON
        else:
            col_type = "TEXT"  # Default: store everything as text

        columns_sql.append(f'"{col_name}" {col_type}')

    ddl = f"""
        CREATE TABLE IF NOT EXISTS raw."{entity}" (
            {", ".join(columns_sql)}
        );
    """

    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def upsert_rows(conn, entity: str, rows: list) -> int:
    """
    Inserts rows into the lake database.
    If a row with the same 'id' already exists, updates it (UPSERT).
    
    This is what makes the extractor idempotent:
    - Run it once: 1000 rows inserted
    - Run it again: same 1000 rows, updated with latest values
    - Result is always the same, no duplicates
    """
    if not rows:
        return 0

    # Serialize nested objects to JSON strings for storage
    processed_rows = []
    for row in rows:
        processed_row = {}
        for k, v in row.items():
            if isinstance(v, (dict, list)):
                processed_row[k] = json.dumps(v)
            else:
                processed_row[k] = v
        processed_rows.append(processed_row)

    columns = list(processed_rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))

    # Build the UPDATE clause (for when the id already exists)
    update_clause = ", ".join(
        f'"{c}" = EXCLUDED."{c}"'
        for c in columns if c != "id"
    )

    sql = f"""
        INSERT INTO raw."{entity}" ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE SET {update_clause};
    """

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            sql,
            [tuple(row.get(c) for c in columns) for row in processed_rows],
            page_size=500,
        )
    conn.commit()
    return len(rows)


# ── Main Extract Function ─────────────────────────────────────────────────────
def extract_entity(entity: str, full_refresh: bool = False) -> int:
    """
    Extracts all data for one entity from the ERP API and saves to lake DB.
    
    Called by Airflow once per entity per day.
    
    Args:
        entity: The entity name (e.g., "customers")
        full_refresh: If True, ignore watermark and fetch everything
    
    Returns:
        Total number of rows upserted
    """
    logger.info(f"{'='*50}")
    logger.info(f"Starting extract: {entity}")

    conn = get_db_connection()
    ensure_raw_schema_and_watermarks(conn)

    # ── Get watermark (or None for first run) ─────────────────────────────────
    watermark = None if full_refresh else get_watermark(conn, entity)

    total_upserted = 0
    max_updated_at = watermark  # Track the highest timestamp in this batch
    table_created = False

    # ── Fetch all pages ───────────────────────────────────────────────────────
    for page_rows in paginate_entity(entity, updated_after=watermark):

        if not page_rows:
            continue

        # Create the table on the first page if it doesn't exist
        if not table_created and page_rows:
            sample_row = next((row for row in page_rows if isinstance(row, dict)), None)
            if sample_row:
                ensure_entity_table(conn, entity, sample_row)
                table_created = True

        # Upsert this page's rows
        count = upsert_rows(conn, entity, page_rows)
        total_upserted += count

        # Track the maximum updated_at to use as the new watermark
        for row in page_rows:
            if not isinstance(row, dict):
                continue

            row_ts = row.get("updatedAt")
            if row_ts:
                if max_updated_at is None or row_ts > max_updated_at:
                    max_updated_at = row_ts
                else:
                    max_updated_at = max(max_updated_at, row_ts)

    # ── Save watermark for next incremental run ───────────────────────────────
    if max_updated_at:
        save_watermark(conn, entity, max_updated_at, total_upserted)
        logger.info(f"Watermark saved: {max_updated_at}")

    conn.close()
    logger.info(f"Completed: {entity} | {total_upserted} rows upserted")
    return total_upserted


def run_full_extract():
    """Extracts all entities. Called directly for testing."""
    results = {}
    for entity in ENTITIES:
        try:
            count = extract_entity(entity)
            results[entity] = {"status": "success", "rows": count}
        except Exception as e:
            logger.error(f"Failed to extract {entity}: {e}")
            results[entity] = {"status": "failed", "error": str(e)}

    logger.info("=" * 50)
    logger.info("EXTRACTION SUMMARY:")
    for entity, result in results.items():
        logger.info(f"  {entity}: {result}")

    return results


# ── Entry point (for testing locally) ────────────────────────────────────────
if __name__ == "__main__":
    run_full_extract()






