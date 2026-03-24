"""Email service for sending notifications."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
import os


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.enabled = bool(self.sender_email and self.sender_password)
        
        if self.enabled:
            logger.info(f"Email service initialized with {self.smtp_server}:{self.smtp_port}")
        else:
            logger.warning("Email service disabled: SENDER_EMAIL or SENDER_PASSWORD not configured")
    
    async def send_room_created_notification(
        self,
        recipient_email: str,
        room_name: str,
        room_id: str,
        creator_name: str,
        base_url: str = "http://localhost:8000"
    ) -> bool:
        """Send email notification when a new room is created.
        
        Args:
            recipient_email: Email address to send to
            room_name: Name of the created room
            room_id: ID of the created room
            creator_name: Name of the room creator
            base_url: Base URL of the application
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Email service disabled, skipping notification to {recipient_email}")
            return False
        
        try:
            room_url = f"{base_url}/room/{room_id}"
            
            subject = f"New Game Room Created: {room_name}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #4CAF50;">A New Game Room Has Been Created!</h2>
                    
                    <p>Hello,</p>
                    
                    <p>A new 5 Crowns game room has been created. Here are the details:</p>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                        <p><strong>Room Name:</strong> {room_name}</p>
                        <p><strong>Created By:</strong> {creator_name}</p>
                        <p><strong>Room ID:</strong> <code>{room_id}</code></p>
                    </div>
                    
                    <p><a href="{room_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Join the Game</a></p>
                    
                    <p>If the button above doesn't work, you can also visit this link:</p>
                    <p><a href="{room_url}">{room_url}</a></p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        This is an automated notification from the 5 Crowns game server. 
                        If you have any questions, please contact the room creator.
                    </p>
                </body>
            </html>
            """
            
            text_content = f"""
            A New Game Room Has Been Created!
            
            Room Name: {room_name}
            Created By: {creator_name}
            Room ID: {room_id}
            
            Join the game here: {room_url}
            
            This is an automated notification from the 5 Crowns game server.
            """
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # Attach both text and HTML versions
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"Email notification sent to {recipient_email} for room {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification to {recipient_email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
