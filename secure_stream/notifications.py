from typing import List, Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from dataclasses import dataclass
import jinja2

@dataclass
class Notification:
    id: str
    type: str
    severity: str
    title: str
    message: str
    timestamp: str
    metadata: Dict[str, Any]
    recipient: str

class NotificationEngine:
    """Handles notification generation and delivery for the SecureStream system."""
    
    def __init__(
        self,
        smtp_config: Dict[str, str],
        webhook_urls: Dict[str, str],
        template_dir: str
    ):
        """
        Initialize notification engine.
        
        Args:
            smtp_config: SMTP server configuration
            webhook_urls: External webhook URLs for notifications
            template_dir: Directory containing notification templates
        """
        self.smtp_config = smtp_config
        self.webhook_urls = webhook_urls
        self.logger = logging.getLogger(__name__)
        
        # Initialize template engine
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )

    async def send_notification(self, notification: Notification) -> bool:
        """
        Send notification through configured channels.
        
        Args:
            notification: Notification object to send
            
        Returns:
            Success status
        """
        try:
            # Send email notification
            if notification.type in ['violation', 'critical']:
                await self._send_email_notification(notification)
            
            # Send webhook notification
            if notification.severity in ['high', 'critical']:
                await self._send_webhook_notification(notification)
            
            # Log notification
            self._log_notification(notification)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")
            return False

    async def _send_email_notification(self, notification: Notification):
        """Send email notification."""
        try:
            # Load email template
            template = self.template_env.get_template(f"{notification.type}.html")
            html_content = template.render(
                title=notification.title,
                message=notification.message,
                metadata=notification.metadata,
                timestamp=notification.timestamp
            )
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"SecureStream Alert: {notification.title}"
            msg['From'] = self.smtp_config['sender']
            msg['To'] = notification.recipient
            
            # Add HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP_SSL(
                self.smtp_config['host'],
                self.smtp_config['port']
            ) as server:
                server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {str(e)}")
            raise

    async def _send_webhook_notification(self, notification: Notification):
        """Send webhook notification."""
        try:
            webhook_url = self.webhook_urls.get(notification.type)
            if not webhook_url:
                return
                
            payload = {
                "type": notification.type,
                "severity": notification.severity,
                "title": notification.title,
                "message": notification.message,
                "timestamp": notification.timestamp,
                "metadata": notification.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status not in (200, 201):
                        raise Exception(
                            f"Webhook request failed: {response.status}"
                        )
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")
            raise

    def _log_notification(self, notification: Notification):
        """Log notification for audit purposes."""
        log_entry = {
            "id": notification.id,
            "type": notification.type,
            "severity": notification.severity,
            "title": notification.title,
            "timestamp": notification.timestamp,
            "recipient": notification.recipient
        }
        self.logger.info(f"Notification sent: {json.dumps(log_entry)}")

class NotificationManager:
    """Manages notification preferences and delivery rules."""
    
    def __init__(self, db_url: str):
        """
        Initialize notification manager.
        
        Args:
            db_url: Database connection URL
        """
        self.db_url = db_url
        self.logger = logging.getLogger(__name__)

    async def get_notification_preferences(
        self, user_id: str
    ) -> Dict[str, Any]:
        """Get user's notification preferences."""
        try:
            # Fetch from database
            # Implementation depends on database schema
            return {
                "email_notifications": True,
                "webhook_notifications": True,
                "notification_types": ["violation", "critical"],
                "minimum_severity": "medium"
            }
        except Exception as e:
            self.logger.error(
                f"Failed to get notification preferences: {str(e)}"
            )
            return {}

    async def update_notification_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """Update user's notification preferences."""
        try:
            # Update in database
            # Implementation depends on database schema
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to update notification preferences: {str(e)}"
            )
            return False

    def create_violation_notification(
        self, content_id: str, violation_data: Dict[str, Any]
    ) -> Notification:
        """Create notification for content violation."""
        return Notification(
            id=f"violation_{content_id}_{datetime.utcnow().timestamp()}",
            type="violation",
            severity="high",
            title=f"Content Violation Detected",
            message=(
                f"Potential violation detected for content {content_id} "
                f"on platform {violation_data.get('platform', 'Unknown')}"
            ),
            timestamp=datetime.utcnow().isoformat(),
            metadata=violation_data,
            recipient=violation_data.get('owner_email')
        )

    def create_system_notification(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Notification:
        """Create system-level notification."""
        return Notification(
            id=f"system_{event_type}_{datetime.utcnow().timestamp()}",
            type="system",
            severity="medium",
            title=f"System Event: {event_type}",
            message=event_data.get('message', ''),
            timestamp=datetime.utcnow().isoformat(),
            metadata=event_data,
            recipient=event_data.get('admin_email')
        )
