FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create data directory for dedup cache
RUN mkdir -p /app/data

CMD ["python", "main.py", "--all"]
