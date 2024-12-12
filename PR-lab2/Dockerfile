FROM python:3.9-slim

# Install the required packages for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080 8090
CMD ["python", "main.py"]