import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Reddit configuration
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
# Reddit JSON URL - if None, uses sample data
REDDIT_JSON_URL = os.getenv("REDDIT_JSON_URL")

# Demo mode (if True, always use sample data regardless of REDDIT_JSON_URL)
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Sentiment thresholds
NEGATIVE_THRESHOLD = -0.1  # Below this is considered negative sentiment
BURST_THRESHOLD = 3  # Number of negative posts to trigger a burst alert
BURST_TIMEFRAME = 60  # Timeframe in minutes to check for bursts

# Email configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER") 
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Categories for posts
CATEGORIES = [
    "Events",
    "News",
    "Question",
    "Photo",
    "Food",
    "Housing",
    "Transportation",
    "Crime",
    "Politics",
    "Weather",
    "Sports",
    "Other"
]

# Check interval (minutes)
CHECK_INTERVAL = 10

# Number of initial posts to retrieve on startup
INITIAL_POSTS_COUNT = 10

# Model configurations
ZERO_SHOT_MODEL = {
    "name": "facebook/bart-large-mnli",
    "revision": "d7645e1"
}

SENTIMENT_MODEL = {
    "name": "distilbert-base-uncased-finetuned-sst-2-english",
    "revision": "af0f99b"
}

IMAGE_MODEL = {
    "name": "google/vit-base-patch16-224",
    "revision": "5dca96d"
}