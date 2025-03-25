import logging
import config
from transformers import pipeline

logger = logging.getLogger("sentiment_agent")

class PostCategorizer:
    def __init__(self):
        # Initialize categories from config
        self.categories = config.CATEGORIES
        
        # Initialize zero-shot classification pipeline
        logger.info("Initializing zero-shot classification pipeline")
        # Use model configuration from config.py
        self.classifier = pipeline(
            "zero-shot-classification",
            model=config.ZERO_SHOT_MODEL["name"],
            revision=config.ZERO_SHOT_MODEL["revision"]
        )
    
    def categorize(self, title, content):
        """
        Categorize a post based on its title and content
        
        Args:
            title (str): The post title
            content (str): The post content
            
        Returns:
            str: The predicted category
        """
        # Combine title and content for categorization
        text = f"{title}. {content}"
        
        # Get prediction using zero-shot classification
        prediction = self.classifier(
            text, 
            candidate_labels=self.categories,
            multi_label=False
        )
        
        # Return the most likely category
        return prediction['labels'][0]