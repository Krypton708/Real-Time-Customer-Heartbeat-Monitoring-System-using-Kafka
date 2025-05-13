FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt .
COPY ./data_generator.py .

# Set PIP timeout and retry
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_NO_CACHE_DIR=1 \
    PIP_RETRIES=10

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Setting environment variables
ENV POSTGRES_HOST=postgres
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV KAFKA_TOPIC=heartbeat-topic

# Running the consumer script
CMD ["python", "spark_streaming.py"]