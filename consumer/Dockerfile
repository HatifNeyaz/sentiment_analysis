# consumer/Dockerfile

FROM bitnami/spark:3.4.1
USER root
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY spark_consumer.py .
USER 1001

# FIX: Changed the script name to match the copied file
CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0", "spark_consumer.py"]