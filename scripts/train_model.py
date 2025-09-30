# scripts/train_model.py

import pandas as pd
import joblib
import logging
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

# --- Configuration ---
# Using Path for cross-platform compatibility (works on Windows, Mac, Linux)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
TRAINING_DATA_FILE = DATA_DIR / "twitter_training.csv"
MODEL_OUTPUT_FILE = MODELS_DIR / "sentiment_pipeline.joblib"

# --- Setup Logging ---
# Logging is better than print() for applications. It gives you timestamps
# and severity levels (INFO, ERROR, etc.).
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(file_path):
    """Loads and preprocesses the training data from a CSV file."""
    logging.info(f"Loading data from {file_path}...")
    try:
        df = pd.read_csv(file_path, header=None, names=['id', 'entity', 'sentiment', 'text'])
        df.dropna(subset=['text'], inplace=True)
        
        # Filter for only relevant sentiments
        df = df[df['sentiment'].isin(['Positive', 'Negative'])]
        
        # Map string labels to binary (0/1) for the model
        df['sentiment_label'] = df['sentiment'].map({'Positive': 1, 'Negative': 0})
        
        logging.info("Data loaded and preprocessed successfully.")
        logging.info(f"Data shape: {df.shape}")
        return df['text'], df['sentiment_label']
        
    except FileNotFoundError:
        logging.error(f"Data file not found at {file_path}. Exiting.")
        raise

def train_sentiment_model(X, y):
    """Creates, trains, and returns a sentiment analysis pipeline."""
    
    # Split data before training
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logging.info("Data split into training and testing sets.")

    # Define the model pipeline
    # This pipeline encapsulates the feature extraction (TF-IDF) and the classifier.
    # It ensures that the same steps are applied consistently during training and prediction.
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=10000, 
            ngram_range=(1, 2), # Using unigrams and bigrams captures more context
            stop_words='english' # Remove common English words that don't add much meaning
        )),
        ('classifier', LogisticRegression(
            solver='liblinear', # Good solver for this type of problem
            max_iter=1000
        ))
    ])
    
    logging.info("Training the sentiment model pipeline...")
    pipeline.fit(X_train, y_train)
    logging.info("Model training complete.")
    
    # Evaluate the model on the unseen test set
    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    logging.info(f"Model accuracy on the test set: {accuracy:.4f}")
    
    return pipeline

def save_model(model, file_path):
    """Saves the trained model to a file."""
    # Ensure the directory to save the model exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Saving model to {file_path}...")
    joblib.dump(model, file_path)
    logging.info("Model saved successfully.")

def main():
    """Main function to run the full training pipeline."""
    try:
        X, y = load_data(TRAINING_DATA_FILE)
        model = train_sentiment_model(X, y)
        save_model(model, MODEL_OUTPUT_FILE)
    except Exception as e:
        logging.error(f"An error occurred during the training process: {e}")

if __name__ == "__main__":
    main()