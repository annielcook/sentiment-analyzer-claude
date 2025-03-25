import logging
import config
from transformers import pipeline

logger = logging.getLogger("sentiment_agent")

class SentimentAnalyzer:
    def __init__(self):
        # Initialize sentiment analysis pipeline
        logger.info("Initializing sentiment analysis pipeline")
        # Use model configuration from config.py
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=config.SENTIMENT_MODEL["name"],
            revision=config.SENTIMENT_MODEL["revision"]
        )
    
    def analyze(self, title, content):
        """
        Analyze the sentiment of a post based on its title and content
        
        Args:
            title (str): The post title
            content (str): The post content
            
        Returns:
            dict: Sentiment analysis result with keys:
                - score: A float representing sentiment (-1 to 1)
                - label: Either 'POSITIVE' or 'NEGATIVE'
                - is_negative: Boolean indicating if the post has negative sentiment
        """
        # Combine title and content for better sentiment analysis
        text = f"{title}. {content}"
        
        # Get sentiment prediction from ML pipeline
        result = self.sentiment_pipeline(text)[0]
        
        # Convert to a standardized format
        # BERT sentiment models return a label ('POSITIVE'/'NEGATIVE') and a score (0-1)
        # Convert to a value between -1 and 1 for easier thresholding
        score = result['score']
        if result['label'] == 'NEGATIVE':
            score = -score
        
        return {
            'score': score,
            'label': result['label'],
            'is_negative': score < config.NEGATIVE_THRESHOLD
        }