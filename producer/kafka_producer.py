import pandas as pd
import json
import time
import logging
from kafka import KafkaProducer
from pathlib import Path

# --- Configuration ---
DATA_FILE = Path(r"./data/twitter_training.csv")
KAFKA_TOPIC = "twitter-stream"
KAFKA_SERVER = "kafka:9092"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_producer():
    producer = None
    for i in range(10): # Increased retries
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_SERVER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logging.info("Successfully connected to Kafka.")
            return producer
        except Exception as e:
            logging.error(f"Failed to connect to Kafka on attempt {i+1}: {e}")
            time.sleep(10) # Increased wait time
    if not producer:
        logging.critical("Could not connect to Kafka after multiple retries. Exiting.")
        exit(1)

def on_send_success(record_metadata):
    logging.info(f"Message sent to topic '{record_metadata.topic}' partition {record_metadata.partition} at offset {record_metadata.offset}")

def on_send_error(excp):
    logging.error('Error sending message', exc_info=excp)

def stream_data(producer, topic, file_path):
    try:
        chunk_iter = pd.read_csv(
            file_path,
            header=None,
            names=['id', 'entity', 'sentiment', 'text'],
            chunksize=1000
        )
        logging.info(f"Starting to stream data from {file_path} to topic '{topic}'...")
        for chunk in chunk_iter:
            chunk.dropna(subset=['text'], inplace=True)
            for index, row in chunk.iterrows():
                message = {
                    'id': row['id'],
                    'text': str(row['text']),
                    'timestamp': time.time()
                }
                producer.send(topic, value=message).add_callback(on_send_success).add_errback(on_send_error)
                time.sleep(0.01)
        producer.flush()
        logging.info("Finished streaming all data.")
    except FileNotFoundError:
        logging.error(f"Data file not found at {file_path}. Please check the path.")
    except Exception as e:
        logging.error(f"An error occurred during data streaming: {e}")

def main():
    producer = create_producer()
    if producer:
        stream_data(producer, KAFKA_TOPIC, DATA_FILE)
        producer.close()

if __name__ == "__main__":
    main()