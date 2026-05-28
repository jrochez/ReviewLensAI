FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -r -u 1001 -s /bin/false appuser

COPY . .

RUN mkdir -p data/chromadb config && chown -R appuser:appuser /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
