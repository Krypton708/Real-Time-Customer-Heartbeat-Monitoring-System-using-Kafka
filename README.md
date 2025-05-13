
# Real-Time Heartbeat Monitoring

Welcome to the Heartbeat Monitoring System! This guide will walk you through setting up a real-time data pipeline using:

- **Kafka** (message broker)
- **Spark Structured Streaming** (data processor)
- **PostgreSQL** (data storage)

---

###  Project Structure

```
project-root/
│
├── kafka_producer.py           # Generates and sends heart rate data
├── spark_kafka_to_postgres.py  # Reads from Kafka and writes to PostgreSQL
├── user_guide.md               # 📖 You are here!
└── requirements.txt            # Python dependencies
```

---

##  Prerequisites

Ensure you have the following installed and running:

- Docker & Docker Compose
- Python 3.8+
- Java 8+
- Apache Spark with PySpark
- Kafka (via Docker or local setup)
- PostgreSQL (via Docker or local setup)

---

## Step 1: Start Kafka and PostgreSQL with Docker

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"

  postgres:
    image: postgres
    environment:
      POSTGRES_DB: heartbeat_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
```

Run it:

```bash
docker-compose up -d
```

---

## Step 2: Run the Kafka Producer

This script simulates heartbeat data:

```python
# kafka_producer.py

import random
import time
from datetime import datetime
from kafka import KafkaProducer
import json
import logging

logging.basicConfig(level=logging.INFO)
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_heartbeat():
    while True:
        data = {
            "patient_id": random.randint(1, 10),
            "timestamp": datetime.now().isoformat(),
            "heart_rate": random.randint(20, 200)
        }
        producer.send('heartbeat-topic', data)
        logging.info(f"Sent: {data}")
        time.sleep(1)

generate_heartbeat()
```

Run it:

```bash
python kafka_producer.py
```

---

## Step 3: Run the Spark Job

This script reads from Kafka and writes valid heartbeats to PostgreSQL:

```python
# spark_kafka_to_postgres.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, IntegerType, TimestampType
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("KafkaToPostgres")

schema = StructType()
          .add("patient_id", IntegerType())
          .add("timestamp", TimestampType())
          .add("heart_rate", IntegerType())

spark = SparkSession.builder.appName("KafkaToPostgres").getOrCreate()

df = spark.readStream.format("kafka")
     .option("kafka.bootstrap.servers", "localhost:9092")
     .option("subscribe", "heartbeat-topic")
     .option("startingOffsets", "latest")
     .load()

parsed_df = df.selectExpr("CAST(value AS STRING)")
        .select(from_json(col("value"), schema).alias("data"))
        .select("data.*")
        .dropna()

def write_batch(batch_df, batch_id):
    try:
        batch_df.write.format("jdbc")
        .option("url", "jdbc:postgresql://localhost:5432/heartbeat_db")
        .option("dbtable", "heartbeats")
        .option("user", "postgres")
        .option("password", "postgres")
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save()
        log.info(f"Batch {batch_id} written to PostgreSQL.")
    except Exception as e:
        log.error(f"Error writing batch {batch_id}: {e}")

parsed_df.writeStream
  .foreachBatch(write_batch)
  .option("checkpointLocation", "/tmp/spark_checkpoint")
  .start()
  .awaitTermination()
```

Run the script:

```bash
spark-submit spark_kafka_to_postgres.py
```

---

## Step 4: Verify Data in PostgreSQL

Connect using a GUI like pgAdmin.

```sql
SELECT * FROM heartbeats;
```

---

## Troubleshooting Tips

| Problem                            | Solution |
|------------------------------------|----------|
| Kafka connection error             | Ensure Kafka is running on port 9092 and topic is correct |
| Spark job crashes on type error    | Ensure schema in `spark_streaming.py` matches the JSON structure |
| PostgreSQL write error             | Check credentials and database existence |
| Invalid rows not written           | They are dropped by `.dropna()` for safety |

---

## Resources

- [Apache Kafka Docs](https://kafka.apache.org/)
- [Apache Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
