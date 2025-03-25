# Reddit Sentiment Analyzer

A lightweight Streamlit application that monitors a Reddit subreddit for new posts, analyzes their sentiment using AI, categorizes them, and sends alerts when bursts of negative sentiment are detected.

## Features

- **Reddit Post Monitoring**: Automatically fetches new posts from Reddit
- **AI-Powered Analysis**: Uses Hugging Face Transformers for sentiment analysis and categorization
- **Image Analysis**: Extracts content and sentiment from images in posts
- **Burst Detection**: Alerts when multiple negative posts appear in a category within a short timeframe
- **Email Notifications**: Sends email alerts when bursts are detected
- **Interactive Dashboard**: Streamlit UI with filtering and visualization options
- **Simple Storage**: Stores up to 50 posts with simple pickle file (no database needed)

## Quick Start

### Local Development

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file:
   ```
   REDDIT_JSON_URL=https://www.reddit.com/r/boston.json
   EMAIL_SENDER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   EMAIL_RECIPIENT=alert-recipient@example.com
   ```
4. Run the application:
   ```
   ./run_app.sh
   ```
5. Open http://localhost:8501 in your browser

### Docker

1. Build and run with Docker Compose:
   ```
   docker-compose up -d
   ```
2. Open http://localhost:8501 in your browser

## Deployment

### Render

1. Fork this repository
2. Update the `render.yaml` file with your GitHub repository URL
3. Create a new Render Blueprint instance from your repository
4. Set up the required environment variables in Render

### HuggingFace Spaces

This project is compatible with HuggingFace Spaces using the Docker SDK:

```yaml
title: Reddit Sentiment Analyzer
emoji: 📊
colorFrom: pink
colorTo: yellow
sdk: docker
app_port: 8501
pinned: false
license: mit
```

## Configuration

Edit `config.py` to configure:

- `CATEGORIES`: Post categories to track
- `BURST_THRESHOLD`: Number of negative posts to trigger a burst alert
- `BURST_TIMEFRAME`: Time window (in minutes) for burst detection
- `CHECK_INTERVAL`: Default interval for checking new posts
- AI model parameters

## Architecture

This application is built as a single Streamlit app that provides both UI and background processing capabilities. It:

1. Fetches posts from Reddit via RSS/JSON
2. Analyzes text sentiment using transformers
3. Categorizes posts with zero-shot classification
4. Analyzes images when present
5. Stores processed posts (max 50) in a pickle file
6. Detects bursts of negative sentiment
7. Sends email notifications
8. Displays results in an interactive dashboard

## How It Works

1. **Post Processing Pipeline**:
   - Fetches JSON data from Reddit and extracts posts
   - Analyzes text sentiment with transformer models
   - Downloads and analyzes images with Vision Transformer
   - Categorizes content with zero-shot classification
   - Combines text and image sentiment for a holistic score

2. **Burst Detection**:
   - Tracks posts by category and sentiment over time
   - Triggers alerts when negative posts exceed threshold in timeframe

3. **User Interface**:
   - Interactive dashboard with filtering capabilities
   - Visual indicators for sentiment bursts
   - Post details with sentiment scores and image analysis results

## File Structure

- `streamlit_app.py`: Main application with UI and processing logic
- `rss_parser.py`: Fetches posts from Reddit
- `sentiment_analyzer.py`: Analyzes post sentiment
- `categorizer.py`: Categorizes posts
- `image_analyzer.py`: Analyzes images in posts
- `notifier.py`: Sends email notifications
- `config.py`: Application configuration
- `Dockerfile`: Container definition
- `docker-compose.yml`: Docker Compose configuration
- `render.yaml`: Render deployment configuration

## License

MIT License