FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Restock orders live in SQLite here; mount a volume on /data to keep them across deploys
RUN mkdir /data && chown nobody /data
ENV RESTOCK_DB_PATH=/data/restock.db
USER nobody
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
