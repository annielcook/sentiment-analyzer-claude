import re
import html
import json
import config
import requests
import logging
from datetime import datetime

logger = logging.getLogger("sentiment_agent")

class RedditRSSParser:
    def __init__(self):
        self.user_agent = config.USER_AGENT
        self.api_url = config.REDDIT_JSON_URL if hasattr(config, 'REDDIT_JSON_URL') else None
        self.headers = {'User-Agent': self.user_agent}
    
    def get_new_posts(self, seen_ids=None, limit=None):
        """
        Get new posts from Reddit using JSON API or return sample data
        
        Args:
            seen_ids (set, optional): Set of already seen post IDs
            limit (int, optional): Maximum number of posts to return
            
        Returns:
            list: List of post dictionaries
        """
        if seen_ids is None:
            seen_ids = set()
        
        # Always use sample data in demo mode
        if config.DEMO_MODE:
            logger.info("Running in DEMO MODE - using sample data instead of real API")
            return self._get_sample_posts(seen_ids, limit)
        
        # Try to fetch from JSON API if configured
        if self.api_url:
            try:
                logger.info(f"Fetching posts from {self.api_url}")
                return self._fetch_json_posts(seen_ids, limit)
            except Exception as e:
                logger.error(f"Error fetching JSON from Reddit: {str(e)}")
                logger.info("Falling back to sample data")
        else:
            logger.info("No Reddit JSON URL configured, using sample data")
        
        # Use the sample posts function
        return self._get_sample_posts(seen_ids, limit)
    
    def _get_sample_posts(self, seen_ids=None, limit=None):
        """
        Generate sample posts for demo or fallback mode
        
        Args:
            seen_ids (set, optional): Set of already seen post IDs
            limit (int, optional): Maximum number of posts to return
            
        Returns:
            list: List of sample post dictionaries
        """
        if seen_ids is None:
            seen_ids = set()
            
        # Generate sample posts
        sample_posts = [
            {
                'id': 'sample1',
                'title': 'Boston Public Garden looking beautiful today',
                'content': 'I took this photo at the Public Garden this morning. The flowers are in full bloom!',
                'image_urls': [],
                'link': 'https://example.com/sample1',
                'published': '2025-03-20T10:00:00'
            },
            {
                'id': 'sample2',
                'title': 'Traffic problems on I-93 this morning',
                'content': 'Terrible accident on I-93 northbound. Avoid if possible, major delays expected.',
                'image_urls': [],
                'link': 'https://example.com/sample2',
                'published': '2025-03-20T09:30:00'
            },
            {
                'id': 'sample3',
                'title': 'New restaurant opening in Back Bay',
                'content': 'Has anyone tried the new Italian place on Newbury Street? The pasta looks amazing!',
                'image_urls': [],
                'link': 'https://example.com/sample3',
                'published': '2025-03-20T11:15:00'
            },
            {
                'id': 'sample4',
                'title': 'MBTA delays on the Red Line',
                'content': 'Signal problems at Harvard Square. Expect 15-20 minute delays on the Red Line.',
                'image_urls': [],
                'link': 'https://example.com/sample4',
                'published': '2025-03-20T08:45:00'
            },
            {
                'id': 'sample5',
                'title': 'Best coffee shops for working remotely?',
                'content': 'Looking for recommendations for coffee shops with good wifi and plenty of outlets. Preferably in Cambridge or Somerville area.',
                'image_urls': [],
                'link': 'https://example.com/sample5',
                'published': '2025-03-20T12:30:00'
            }
        ]
        
        # Filter out seen posts
        new_posts = [post for post in sample_posts if post['id'] not in seen_ids]
        
        # Apply limit if provided
        if limit and len(new_posts) > limit:
            new_posts = new_posts[:limit]
            
        logger.info(f"Returning {len(new_posts)} sample posts")
        return new_posts
    
    def _fetch_json_posts(self, seen_ids, limit=None):
        """
        Fetch posts using Reddit JSON API
        
        Args:
            seen_ids (set): Set of already seen post IDs
            limit (int, optional): Maximum number of posts to return
            
        Returns:
            list: List of processed posts
        """
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, dict) or 'data' not in data or 'children' not in data.get('data', {}):
                logger.error(f"Unexpected JSON structure: {str(data)[:100]}...")
                return []
            
            posts = []
            for child in data.get('data', {}).get('children', []):
                try:
                    if not isinstance(child, dict) or 'data' not in child:
                        continue
                        
                    post_data = child.get('data', {})
                    
                    # Skip if we've seen this post already
                    post_id = post_data.get('id')
                    if not post_id or post_id in seen_ids:
                        continue
                    
                    # Extract key information
                    title = html.unescape(post_data.get('title', ''))
                    selftext = html.unescape(post_data.get('selftext', ''))
                    created_utc = post_data.get('created_utc', 0)
                    permalink = post_data.get('permalink', '')
                    url = post_data.get('url', '')
                    
                    # Format the datetime 
                    date_str = datetime.fromtimestamp(created_utc).isoformat()
                    
                    # Extract image URLs if any
                    image_urls = []
                    
                    # Check for gallery
                    if post_data.get('is_gallery', False) and 'gallery_data' in post_data:
                        media_metadata = post_data.get('media_metadata', {})
                        for item in post_data['gallery_data'].get('items', []):
                            media_id = item.get('media_id')
                            if media_id and media_id in media_metadata:
                                # 's' is a dictionary, not a list
                                s_data = media_metadata[media_id].get('s', {})
                                if 'u' in s_data:
                                    image_urls.append(s_data['u'])
                    
                    # Check for preview images
                    elif 'preview' in post_data and 'images' in post_data['preview']:
                        for image in post_data['preview']['images']:
                            if 'source' in image and 'url' in image['source']:
                                # Make sure to unescape HTML entities in URLs
                                image_url = html.unescape(image['source']['url'])
                                # Reddit preview URLs sometimes need special handling
                                if "preview.redd.it" in image_url:
                                    logger.info(f"Found Reddit preview image: {image_url}")
                                image_urls.append(image_url)
                    
                    # Check if the URL itself is an image
                    elif self.is_image_url(url):
                        image_urls.append(url)
                    
                    # Create post dictionary
                    post = {
                        'id': post_id,
                        'title': title,
                        'content': selftext,
                        'link': f"https://www.reddit.com{permalink}",
                        'published': date_str,
                        'image_urls': image_urls
                    }
                    
                    posts.append(post)
                    
                except Exception as e:
                    logger.error(f"Error processing post: {str(e)}")
            
            # Apply limit if provided
            if limit and len(posts) > limit:
                posts = posts[:limit]
                
            logger.info(f"Fetched {len(posts)} new posts from Reddit JSON API")
            return posts
            
        except Exception as e:
            logger.error(f"Error in JSON fetching: {str(e)}")
            return []
    
    def is_image_url(self, url):
        """Check if a URL is likely an image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)