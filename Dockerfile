FROM python:3.12-slim

WORKDIR /app

# System deps: soccerdata's some scrapers and lxml/pandas benefit from these;
# kept minimal on purpose (no browser/selenium deps — this project doesn't
# require them for the core engine or Flask app to run).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p cache/api_responses cache/soccerdata_cache

ENV EPL_HOST=0.0.0.0
ENV EPL_PORT=8000
ENV EPL_WSGI_SERVER=production
ENV EPL_DEBUG=false

EXPOSE 8000

CMD ["python", "main.py"]
