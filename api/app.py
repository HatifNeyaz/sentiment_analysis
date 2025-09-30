from flask import Flask, Response
from pymongo import MongoClient
from bson import json_util
import logging

MONGO_URI = "mongodb://root:password@mongo:27017/"
MONGO_DB = "sentiment_db"
MONGO_COLLECTION = "tweets"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    logging.info("MongoDB connection successful for API.")
except Exception as e:
    logging.error(f"Could not connect to MongoDB: {e}")
    client = None

@app.route('/sentiments', methods=['GET'])
def get_sentiments():
    if client is None:
        return Response(json_util.dumps({"error": "Database connection failed"}), status=500, mimetype='application/json')
    try:
        documents = list(collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))
        return Response(json_util.dumps(documents), mimetype='application/json')
    except Exception as e:
        logging.error(f"Error querying sentiments: {e}")
        return Response(json_util.dumps({"error": "Failed to retrieve data"}), status=500, mimetype='application/json')

@app.route('/sentiment-counts', methods=['GET'])
def get_sentiment_counts():
    if client is None:
        return Response(json_util.dumps({"error": "Database connection failed"}), status=500, mimetype='application/json')
    pipeline = [{"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}]
    try:
        counts = list(collection.aggregate(pipeline))
        result = {
            "positive": next((item['count'] for item in counts if item['_id'] == 1), 0),
            "negative": next((item['count'] for item in counts if item['_id'] == 0), 0)
        }
        return Response(json_util.dumps(result), mimetype='application/json')
    except Exception as e:
        logging.error(f"Error querying sentiment counts: {e}")
        return Response(json_util.dumps({"error": "Failed to retrieve data"}), status=500, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)