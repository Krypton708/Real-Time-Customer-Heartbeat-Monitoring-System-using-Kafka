import random
import time
import json
import logging
from datetime import datetime
from kafka.errors import KafkaError
from kafka import KafkaProducer

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Function to get Kafka Producer instance
def get_producer(max_retries=5, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            log.info("Kafka Producer connected.")
            return producer
        except KafkaError as e:
            log.warning(f"Kafka not available, retrying in {delay}s... ({retries + 1}/{max_retries})")
            retries += 1
            time.sleep(delay)
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            retries += 1
            time.sleep(delay)
    log.error("Kafka Producer init failed after max retries.")
    raise Exception("Kafka connection failed")


# Function to generate heartbeat data
def generate_data():
    return {
        "patient_id": random.randint(1, 10),
        "timestamp": datetime.now().isoformat(),
        "heart_rate": random.randint(20, 200)
    }

# Main function to run the data generator (producer)
def main():
    producer = get_producer()
    try:
        while True:
            data = generate_data()
            producer.send('heartbeat-topic', data).get(timeout=10)
            log.info(f"Sent: {data}")
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopped by user.")
    except Exception as e:
        log.error(f"Error: {e}")

main()

# General comments:
# The code is modularized and follows the best practices for data generation and Kafka usage.
