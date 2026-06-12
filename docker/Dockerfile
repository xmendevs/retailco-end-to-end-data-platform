# We start FROM the official Airflow image
# This gives us Airflow pre-installed on Python 3.11
FROM apache/airflow:2.9.1-python3.11

# Switch to airflow user (for security — don't run as root)
USER airflow

# Install all the Python packages our pipeline needs
# Every tool in the pipeline is listed here:
# - requests: makes HTTP calls to the ERP API
# - psycopg2-binary: connects to PostgreSQL databases
# - python-dotenv: reads our .env file
# - dlt[postgres,sql_database]: the dlt load tool
# - dbt-core + dbt-postgres: the dbt transformation tool
RUN pip install --no-cache-dir \
    requests==2.31.0 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0 \
    "dlt[postgres,sql_database]==1.27.2" \
    dbt-core==1.8.2 \
    dbt-postgres==1.8.2

    