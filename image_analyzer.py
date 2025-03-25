import requests
from io import BytesIO
from PIL import Image
from transformers import ViTImageProcessor, ViTForImageClassification
import torch
import logging
import config
import numpy as np

logger = logging.getLogger("sentiment_agent")

class ImageAnalyzer:
    def __init__(self):
        logger.info("Initializing Image Analyzer")
        
        # Initialize Vision Transformer for image classification
        # Use model configuration from config.py
        model_name = config.IMAGE_MODEL["name"]
        model_revision = config.IMAGE_MODEL["revision"]
        
        self.processor = ViTImageProcessor.from_pretrained(model_name, revision=model_revision)
        self.model = ViTForImageClassification.from_pretrained(model_name, revision=model_revision)
        logger.info("Image classification model loaded successfully")
            
        # Initialize image captioning model
        # This could be modified to use a larger model like BLIP or CoCa depending on needs
        
    def download_image(self, url):
        """
        Download image from URL
        
        Args:
            url (str): Image URL
            
        Returns:
            PIL.Image: Downloaded image
        """
        # Set proper headers to avoid 403 Forbidden errors from Reddit
        headers = {
            'User-Agent': config.USER_AGENT,
            'Referer': 'https://www.reddit.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        }
        
        try:
            # First try with headers
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                # Try using the Reddit URL with "amp;" stripped out (common Reddit URL issue)
                cleaned_url = url.replace("&amp;", "&")
                if cleaned_url != url:
                    logger.info(f"Retrying with cleaned URL: {cleaned_url}")
                    try:
                        response = requests.get(cleaned_url, headers=headers, timeout=10)
                        response.raise_for_status()
                        return Image.open(BytesIO(response.content))
                    except Exception as e2:
                        logger.error(f"Error downloading image with cleaned URL {cleaned_url}: {str(e2)}")
                        return None
            logger.error(f"HTTP error downloading image {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error downloading image {url}: {str(e)}")
            return None
    
    def analyze_images(self, image_urls):
        """
        Analyze images from a list of URLs
        
        Args:
            image_urls (list): List of image URLs
            
        Returns:
            dict: Analysis results with keys:
                - content_tags: List of content tags from images
                - captions: List of image captions
        """
        if not image_urls:
            return {
                'content_tags': [],
                'captions': []
            }
        
        content_tags = []
        captions = []
        successful_analyses = 0
        
        for url in image_urls:
            try:
                # Skip empty or invalid URLs
                if not url or not isinstance(url, str) or len(url) < 5:
                    logger.warning(f"Skipping invalid image URL: {url}")
                    continue
                
                # Download image
                logger.info(f"Downloading image from: {url}")
                image = self.download_image(url)
                if image is None:
                    logger.warning(f"Could not download image from: {url}")
                    continue
                
                # Classify image
                tags = self.classify_image(image)
                if tags:
                    content_tags.extend(tags)
                    logger.info(f"Image tags: {', '.join(tags[:5])}")
                
                # Generate caption for image
                caption = self.simple_image_description(tags)
                if caption:
                    captions.append(caption)
                    logger.info(f"Image caption: {caption}")
                
                successful_analyses += 1
                
            except Exception as e:
                logger.error(f"Error analyzing image {url}: {str(e)}")
        
        return {
            'content_tags': list(set(content_tags)),  # Remove duplicates
            'captions': captions
        }
    
    def classify_image(self, image):
        """
        Classify image content
        
        Args:
            image (PIL.Image): Image to classify
            
        Returns:
            list: List of content tags
        """
        # Ensure the image is in RGB format (handle PNG with alpha channel, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Resize to expected size for most vision models
        image = image.resize((224, 224))
        
        # Preprocess image with padding to ensure consistent tensor sizes
        inputs = self.processor(images=image, return_tensors="pt")
        
        # Get model predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = outputs.logits.softmax(dim=-1)
        
        # Get top 5 predictions
        top_indices = predictions[0].topk(5).indices
        
        # Convert indices to labels
        labels = [self.model.config.id2label[idx.item()] for idx in top_indices]
        
        return labels
    
    def simple_image_description(self, tags):
        """
        Create a simple image description from content tags
        
        Args:
            tags (list): List of content tags
            
        Returns:
            str: Simple image description
        """
        if not tags:
            return ""
        
        # This is a simplistic approach - a dedicated image captioning model would be better
        return f"Image showing {', '.join(tags[:3])}"
    
