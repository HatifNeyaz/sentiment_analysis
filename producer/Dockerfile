FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY kafka_producer.py .
# Correctly copy ONLY the data directory
# COPY ../ data/
CMD ["python", "kafka_producer.py"]