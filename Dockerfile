FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
      fastapi>=0.112.0 \
      uvicorn>=0.30.0 \
      sqlalchemy>=2.0.32 \
      pydantic-settings>=2.4.0 \
      'psycopg[binary]>=3.2.0' \
      alembic>=1.13.2 \
      apscheduler>=3.10.4

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
