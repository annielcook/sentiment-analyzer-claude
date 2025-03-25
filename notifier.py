import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config
import logging

logger = logging.getLogger("sentiment_agent")

class EmailNotifier:
    def __init__(self):
        self.sender = config.EMAIL_SENDER
        self.password = config.EMAIL_PASSWORD
        self.recipient = config.EMAIL_RECIPIENT
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
    
    def send_burst_alert(self, category, posts):
        """
        Send an email notification about a burst of negative posts
        In demo mode: logs the email content instead of actually sending
        
        Args:
            category (str): The category with negative posts
            posts (list): List of post dictionaries with negative sentiment
        """
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = f"Alert: Negative Sentiment Burst in r/boston - {category}"
        
        # Create email body
        body = f"<h2>Negative Sentiment Burst Detected in Category: {category}</h2>"
        body += f"<p>There have been {len(posts)} negative posts in the last {config.BURST_TIMEFRAME} minutes.</p>"
        body += "<h3>Posts:</h3>"
        body += "<ul>"
        
        for post in posts:
            body += f"<li><strong><a href='{post['link']}'>{post['title']}</a></strong>"
            
            # Add sentiment information
            sentiment_info = f" (Sentiment Score: {post['sentiment']['score']:.2f})"
            
            # Add image information if available
            if 'image_tags' in post['sentiment'] and post['sentiment']['image_tags']:
                sentiment_info += f" - Contains images of: {', '.join(post['sentiment']['image_tags'][:3])}"
            
            body += sentiment_info + "</li>"
            
            # Add post content preview
            if post['content']:
                # Truncate content for preview
                content_preview = post['content'][:200] + "..." if len(post['content']) > 200 else post['content']
                body += f"<p><em>{content_preview}</em></p>"
        
        body += "</ul>"
        
        # Attach HTML content
        msg.attach(MIMEText(body, 'html'))
        
        # Demo mode: Just log the email instead of sending
        logger.info(f"DEMO MODE - Would send email with subject: {msg['Subject']}")
        logger.info(f"Email content preview: Negative burst in {category} with {len(posts)} posts")
        
        # Comment out actual email sending - uncomment for production use
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
        """
        return True