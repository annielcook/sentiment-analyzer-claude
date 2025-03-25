import streamlit as st
import time
import os
import threading
import pickle
import json
import requests
import html
from datetime import datetime, timedelta
import logging
import pandas as pd
import config
from rss_parser import RedditRSSParser
from categorizer import PostCategorizer
from sentiment_analyzer import SentimentAnalyzer
from image_analyzer import ImageAnalyzer
from notifier import EmailNotifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentiment_app")

# Create directories if they don't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# File to store posts data
POSTS_FILE = "data/posts_data.pickle"

def load_posts():
    """Load posts from pickle file"""
    try:
        if os.path.exists(POSTS_FILE):
            with open(POSTS_FILE, "rb") as f:
                posts = pickle.load(f)
                logger.info(f"Loaded {len(posts)} posts from storage")
                return posts
        else:
            logger.info("No saved data found, starting with empty post storage")
            return []
    except Exception as e:
        logger.error(f"Error loading post data: {str(e)}")
        return []

def save_posts(posts):
    """Save posts to pickle file"""
    try:
        # Ensure we only keep the 50 most recent posts
        sorted_posts = sorted(posts, key=lambda x: x.get('timestamp', 0), reverse=True)
        posts_to_save = sorted_posts[:50]
        
        with open(POSTS_FILE, "wb") as f:
            pickle.dump(posts_to_save, f)
        logger.info(f"Saved {len(posts_to_save)} posts to storage")
    except Exception as e:
        logger.error(f"Error saving post data: {str(e)}")

def check_for_bursts(posts):
    """
    Check if there are any bursts of negative sentiment in any category
    
    Returns:
        list: List of (category, posts) tuples where a burst was detected
    """
    bursts = []
    burst_timeframe_seconds = config.BURST_TIMEFRAME * 60
    cutoff_time = time.time() - burst_timeframe_seconds
    
    # Convert all post timestamps to ensure consistency
    for post in posts:
        # If the post has a published field as ISO timestamp string, convert to Unix timestamp
        if 'published' in post and isinstance(post['published'], str):
            try:
                post['published_timestamp'] = datetime.fromisoformat(post['published']).timestamp()
            except ValueError:
                # Handle the case where the timestamp string is not in ISO format
                post['published_timestamp'] = post.get('timestamp', 0)
        # If published is already a timestamp, use it directly
        elif 'published' in post and isinstance(post['published'], (int, float)):
            post['published_timestamp'] = post['published']
        # Fallback to the processing timestamp
        else:
            post['published_timestamp'] = post.get('timestamp', 0)
    
    # Only consider recent posts within the burst timeframe based on published timestamps
    recent_posts = [post for post in posts if post.get('published_timestamp', 0) > cutoff_time]
    
    # Group by category
    categories = {}
    for post in recent_posts:
        category = post.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(post)
    
    # Check each category for negative bursts
    for category, category_posts in categories.items():
        negative_posts = [p for p in category_posts if p.get('sentiment', {}).get('is_negative', False)]
        if len(negative_posts) >= config.BURST_THRESHOLD:
            bursts.append((category, negative_posts))
    
    return bursts

def get_new_posts(last_fetch_time=None):
    """
    Background function to fetch and process new posts
    Uses AI-powered categorization and sentiment analysis
    """
    # Get posts from storage to check for already processed IDs
    posts = load_posts()
    seen_ids = {post.get('id', '') for post in posts}
    
    # Initialize components
    parser = RedditRSSParser()
    categorizer = PostCategorizer()
    text_analyzer = SentimentAnalyzer()
    image_analyzer = ImageAnalyzer()
    notifier = EmailNotifier()
    
    # Show status in the app
    st.session_state.status = "Fetching posts..."
    
    # Get new posts (limit to None to get all new posts)
    try:
        new_posts = parser.get_new_posts(seen_ids, limit=None)
        logger.info(f"Found {len(new_posts)} new posts")
        
        if not new_posts:
            st.session_state.status = "No new posts found"
            return
        
        st.session_state.status = f"Processing {len(new_posts)} new posts..."
        
        # Process each post
        for i, post in enumerate(new_posts):
            st.session_state.status = f"Processing post {i+1}/{len(new_posts)}: {post.get('title', '')[:30]}..."
            
            try:
                # Analyze images if present
                image_analysis = None
                if 'image_urls' in post and post['image_urls']:
                    logger.info(f"Analyzing {len(post['image_urls'])} images for post {post['id']}")
                    image_analysis = image_analyzer.analyze_images(post['image_urls'])
                    
                    # Add image captions to post content for better categorization and sentiment analysis
                    if image_analysis.get('captions'):
                        post['content'] = post.get('content', '') + " " + " ".join(image_analysis['captions'])
                
                # Categorize post
                category = categorizer.categorize(post['title'], post.get('content', ''))
                post['category'] = category
                logger.info(f"Categorized post {post['id']} as {category}")
                
                # Analyze text sentiment
                text_sentiment = text_analyzer.analyze(post['title'], post.get('content', ''))
                
                # Add image tags to sentiment result if available
                sentiment = text_sentiment.copy()
                
                # Add image tags if available
                if image_analysis and 'content_tags' in image_analysis:
                    sentiment['image_tags'] = image_analysis.get('content_tags', [])
                
                post['sentiment'] = sentiment
                
                # Add timestamp
                post['timestamp'] = time.time()
                
                # Add to posts list
                posts.append(post)
                
            except Exception as e:
                logger.error(f"Error processing post {post.get('id', 'unknown')}: {str(e)}")
        
        # Save updated posts
        save_posts(posts)
        
        # Check for bursts and send notifications
        bursts = check_for_bursts(posts)
        if bursts:
            st.session_state.status = f"Found {len(bursts)} bursts of negative sentiment"
            logger.info(f"Found {len(bursts)} bursts of negative sentiment")
            
            # Send notifications
            for category, category_posts in bursts:
                logger.info(f"Sending notification for burst in category {category}")
                notifier.send_burst_alert(category, category_posts)
        
        # Update status
        st.session_state.status = f"Finished processing. Found {len(new_posts)} new posts."
        st.session_state.last_fetch_time = time.time()
        st.session_state.posts = posts  # Update posts in session
        
    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}")
        st.session_state.status = f"Error: {str(e)}"

def format_datetime(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return "Unknown"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

def get_post_time(post):
    """Get the best available timestamp from a post"""
    # Try published_timestamp first (calculated during burst detection)
    if 'published_timestamp' in post:
        return post['published_timestamp']
    
    # Try converting published if it's a string
    if 'published' in post and isinstance(post['published'], str):
        try:
            return datetime.fromisoformat(post['published']).timestamp()
        except ValueError:
            pass
    
    # Try published if it's already a timestamp
    if 'published' in post and isinstance(post['published'], (int, float)):
        return post['published']
    
    # Fall back to processing timestamp
    return post.get('timestamp', 0)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'posts' not in st.session_state:
        st.session_state.posts = load_posts()
    
    if 'last_fetch_time' not in st.session_state:
        st.session_state.last_fetch_time = None
    
    if 'status' not in st.session_state:
        st.session_state.status = "Ready"
    
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
        
    if 'need_refresh' not in st.session_state:
        st.session_state.need_refresh = False

# Main Streamlit app
def main():
    # Initialize session state
    initialize_session_state()
    
    # Check if we need to refresh data (from auto-refresh)
    if st.session_state.need_refresh:
        get_new_posts()
        st.session_state.need_refresh = False
    
    # App title and description
    st.title("Reddit Sentiment Analyzer")
    st.markdown("Monitors r/boston subreddit for sentiment and categorizes posts")
    
    # Sidebar with controls
    with st.sidebar:
        st.header("Controls")
        
        # Manual refresh button
        if st.button("Fetch New Posts"):
            with st.spinner("Fetching posts..."):
                # Run directly instead of using a thread to avoid Streamlit context warnings
                get_new_posts()
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
        if auto_refresh != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto_refresh
        
        refresh_interval = st.slider("Refresh interval (minutes)", 
                                     min_value=1, max_value=60, value=config.CHECK_INTERVAL)
        
        st.subheader("Categories")
        category_filter = st.multiselect("Filter by category", 
                                        options=["All"] + config.CATEGORIES,
                                        default="All")
        
        st.subheader("Sentiment")
        sentiment_filter = st.radio("Filter by sentiment", 
                                   options=["All", "Positive", "Negative", "Neutral"],
                                   index=0)
    
    # Status information
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        st.write(f"Status: {st.session_state.status}")
    with status_col2:
        if st.session_state.last_fetch_time:
            st.write(f"Last fetch: {format_datetime(st.session_state.last_fetch_time)}")
        else:
            st.write("Last fetch: Never")
    
    # Show bursts if any
    posts = st.session_state.posts
    bursts = check_for_bursts(posts)
    if bursts:
        st.subheader(f"🚨 Bursts Detected: {len(bursts)}")
        for category, neg_posts in bursts:
            with st.expander(f"Burst in {category} category - {len(neg_posts)} negative posts"):
                for post in neg_posts:
                    st.markdown(f"**{post.get('title', 'No title')}** - "
                               f"Score: {post.get('sentiment', {}).get('score', 0):.2f}")
    
    # Display posts with filtering
    st.subheader("Recent Posts")
    
    # Apply filters
    filtered_posts = posts
    
    # Category filter
    if category_filter and "All" not in category_filter:
        filtered_posts = [p for p in filtered_posts if p.get('category') in category_filter]
    
    # Sentiment filter
    if sentiment_filter == "Positive":
        filtered_posts = [p for p in filtered_posts if p.get('sentiment', {}).get('score', 0) > 0.1]
    elif sentiment_filter == "Negative":
        filtered_posts = [p for p in filtered_posts if p.get('sentiment', {}).get('score', 0) < -0.1]
    elif sentiment_filter == "Neutral":
        filtered_posts = [p for p in filtered_posts if abs(p.get('sentiment', {}).get('score', 0)) <= 0.1]
    
    # Sort by published timestamp (newest first)
    filtered_posts = sorted(filtered_posts, key=get_post_time, reverse=True)
    
    # Display posts in cards
    if not filtered_posts:
        st.info("No posts found with the selected filters")
    else:
        # Convert to DataFrame for easier display
        posts_df = pd.DataFrame([
            {
                "title": p.get('title', 'No title'),
                "category": p.get('category', 'Other'),
                "sentiment": p.get('sentiment', {}).get('label', 'NEUTRAL'),
                "score": p.get('sentiment', {}).get('score', 0),
                "timestamp": format_datetime(get_post_time(p)),
                "link": p.get('link', '#'),
                "id": p.get('id', ''),
                "content": p.get('content', '')[:200] + '...' if p.get('content', '') else 'No content'
            } for p in filtered_posts
        ])
        
        # Use Streamlit's built-in dataframe for a cleaner overview
        st.dataframe(
            posts_df[["title", "category", "sentiment", "score", "timestamp"]],
            column_config={
                "title": st.column_config.TextColumn("Title"),
                "category": st.column_config.TextColumn("Category"),
                "sentiment": st.column_config.TextColumn("Sentiment"),
                "score": st.column_config.NumberColumn("Score", format="%.2f"),
                "timestamp": st.column_config.TextColumn("Time")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Show detailed cards for each post
        for i, post in enumerate(filtered_posts[:10]):  # Limit to 10 posts for performance
            sentiment = post.get('sentiment', {})
            sentiment_score = sentiment.get('score', 0)
            sentiment_label = sentiment.get('label', 'NEUTRAL')
            
            # Determine card color based on sentiment
            if sentiment_score > 0.1:
                card_bg = "#d4edda"  # Green for positive
                card_color = "#155724"
            elif sentiment_score < -0.1:
                card_bg = "#f8d7da"  # Red for negative
                card_color = "#721c24"
            else:
                card_bg = "#e2e3e5"  # Gray for neutral
                card_color = "#383d41"
            
            # Create a card-like container
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"### {post.get('title', 'No title')}")
                    st.text(f"Category: {post.get('category', 'Other')}")
                
                with col2:
                    st.markdown(f"**Sentiment: {sentiment_label}**")
                    st.markdown(f"Score: {sentiment_score:.2f}")
                
                st.markdown(post.get('content', '')[:200] + '...' if len(post.get('content', '')) > 200 else post.get('content', ''))
                
                # Show image tags if available
                if 'image_tags' in sentiment and sentiment['image_tags']:
                    st.text(f"Image content: {', '.join(sentiment['image_tags'][:5])}")
                
                st.markdown(f"[View on Reddit]({post.get('link', '#')})")
    
    # Auto-refresh logic
    if st.session_state.auto_refresh:
        # Calculate time since last fetch
        if st.session_state.last_fetch_time:
            time_since_last = time.time() - st.session_state.last_fetch_time
            if time_since_last > refresh_interval * 60:
                st.session_state.status = "Auto-refreshing..."
                # Use a flag to trigger refresh on next rerun instead of threading
                st.session_state.need_refresh = True
        
        # Set up auto-refresh for the page
        st.rerun()

if __name__ == "__main__":
    main()