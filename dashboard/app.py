# dashboard/app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit.components.v1 import html

# --- Configuration ---
API_URL_SENTIMENTS = "http://api:5000/sentiments"
API_URL_COUNTS = "http://api:5000/sentiment-counts"
REFRESH_SECONDS = 5

# --- Page Setup ---
st.set_page_config(
    page_title="Real-Time Sentiment Analysis",
    page_icon="📊",
    layout="wide"
)

# --- Auto-Refresh Component ---
def auto_refresh(interval_seconds):
    """Embeds JavaScript to auto-refresh the page."""
    # The JavaScript code will reload the page every `interval_seconds` milliseconds
    js_code = f"""
        <script>
            setTimeout(function() {{
                window.location.reload();
            }}, {interval_seconds * 1000});
        </script>
    """
    # Use st.components.v1.html to execute the script
    html(js_code, height=0, width=0)

# --- Data Fetching Function ---
@st.cache_data(ttl=REFRESH_SECONDS)
def fetch_data(api_url):
    """Fetches data from the API and returns it as a JSON object."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# --- Main Dashboard UI ---
st.title("📊 Real-Time Social Media Sentiment Analysis")

# Fetch data at the start of the script's run
counts = fetch_data(API_URL_COUNTS)
recent_sentiments = fetch_data(API_URL_SENTIMENTS)

# Check for errors and display the dashboard or a warning
if (counts and "error" in counts) or (recent_sentiments and "error" in recent_sentiments):
    st.error("Could not connect to the API. Waiting for services to start...")
elif not counts or not recent_sentiments:
    st.warning("Waiting for data... The pipeline is warming up.")
else:
    # --- Key Metrics ---
    col1, col2 = st.columns(2)
    col1.metric(label="Positive Sentiments", value=counts.get('positive', 0))
    col2.metric(label="Negative Sentiments", value=counts.get('negative', 0))

    # --- Charts and DataFrames ---
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Sentiment Distribution")
        df_counts = pd.DataFrame([
            {'sentiment': 'Positive', 'count': counts.get('positive', 0)},
            {'sentiment': 'Negative', 'count': counts.get('negative', 0)}
        ])
        fig = px.pie(df_counts, names='sentiment', values='count', color='sentiment',
                     color_discrete_map={'Positive':'green', 'Negative':'red'}, hole=.3)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Most Recent Posts")
        df_recent = pd.DataFrame(recent_sentiments)
        st.dataframe(df_recent, use_container_width=True)

# Call the auto-refresh function at the end of your script
auto_refresh(interval_seconds=REFRESH_SECONDS)