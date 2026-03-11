FROM python:3.10-slim

WORKDIR /app

# Install system dependencies: git and build tools
RUN apt-get update && apt-get install -y git build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "ai_negotiator_api_cors.py"]
