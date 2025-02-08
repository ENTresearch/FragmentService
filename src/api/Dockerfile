FROM python:3.11-alpine

ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

WORKDIR /app

# Install dependencies
COPY ./gateway /app/gateway
COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

# Create a directory for uploaded files
RUN mkdir -p /uploaded_files

# Start the server with live reload
CMD ["sh", "-c", "uvicorn gateway.main:app --host $API_HOST --port $API_PORT --reload"]