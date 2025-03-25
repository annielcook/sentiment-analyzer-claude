#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Run the Streamlit app
echo "Starting Reddit Sentiment Analyzer..."
echo "Navigate to http://localhost:8501 in your browser"

# Run with appropriate options
streamlit run streamlit_app.py --server.port=8501