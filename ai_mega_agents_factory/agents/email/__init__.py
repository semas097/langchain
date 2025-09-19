"""
Email Agent - AI Mega Agents Factory

Specialized agent for email processing, automation, and intelligent email management.
Supports multiple email providers and advanced filtering capabilities.
"""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional
import asyncio
import time
import re
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

from ai_mega_agents_factory import (
    BaseAgentFactory, AgentConfig, AgentResult, AgentTier, monetization_service
)


class EmailConfig(AgentConfig):
    """Configuration for Email Agent"""
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    imap_server: Optional[str] = None
    imap_port: int = 993
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    max_emails_per_request: int = 50
    
    class Config:
        extra = "allow"


class EmailSenderTool(BaseTool):
    """Tool for sending emails"""
    name = "email_sender"
    description = "Send emails with attachments and formatting"
    
    def __init__(self, config: EmailConfig):
        super().__init__()
        self.config = config
    
    def _run(self, to_address: str, subject: str, body: str, 
             cc: str = "", bcc: str = "", html: bool = False) -> str:
        """Send an email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.username
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # For demo purposes, return success without actually sending
            # In production, use actual SMTP connection
            return f"Email sent successfully to {to_address}"
            
        except Exception as e:
            return f"Failed to send email: {str(e)}"
    
    async def _arun(self, to_address: str, subject: str, body: str, 
                   cc: str = "", bcc: str = "", html: bool = False) -> str:
        """Async version of email sending"""
        return self._run(to_address, subject, body, cc, bcc, html)


class EmailReaderTool(BaseTool):
    """Tool for reading and filtering emails"""
    name = "email_reader"
    description = "Read and filter emails from inbox"
    
    def __init__(self, config: EmailConfig):
        super().__init__()
        self.config = config
    
    def _run(self, folder: str = "INBOX", limit: int = 10, 
             filter_subject: str = "", unread_only: bool = True) -> str:
        """Read emails from specified folder"""
        try:
            # For demo purposes, return mock email data
            # In production, use actual IMAP connection
            mock_emails = [
                {
                    "subject": f"Test Email {i}",
                    "from": f"sender{i}@example.com",
                    "date": "2024-01-01",
                    "body": f"This is test email number {i}",
                    "read": i % 2 == 0
                }
                for i in range(1, limit + 1)
            ]
            
            # Apply filters
            if unread_only:
                mock_emails = [e for e in mock_emails if not e["read"]]
            
            if filter_subject:
                mock_emails = [e for e in mock_emails if filter_subject.lower() in e["subject"].lower()]
            
            return str({
                "folder": folder,
                "total_emails": len(mock_emails),
                "emails": mock_emails[:self.config.max_emails_per_request]
            })
            
        except Exception as e:
            return f"Failed to read emails: {str(e)}"
    
    async def _arun(self, folder: str = "INBOX", limit: int = 10, 
                   filter_subject: str = "", unread_only: bool = True) -> str:
        """Async version of email reading"""
        return self._run(folder, limit, filter_subject, unread_only)


class EmailClassifierTool(BaseTool):
    """Tool for classifying emails"""
    name = "email_classifier"
    description = "Classify emails by type, priority, and sentiment"
    
    def _run(self, email_content: str) -> str:
        """Classify email content"""
        try:
            # Simple rule-based classification for demo
            content_lower = email_content.lower()
            
            # Priority classification
            priority = "low"
            if any(word in content_lower for word in ["urgent", "asap", "emergency", "critical"]):
                priority = "high"
            elif any(word in content_lower for word in ["important", "priority", "deadline"]):
                priority = "medium"
            
            # Type classification
            email_type = "general"
            if any(word in content_lower for word in ["meeting", "calendar", "schedule"]):
                email_type = "meeting"
            elif any(word in content_lower for word in ["invoice", "payment", "bill"]):
                email_type = "financial"
            elif any(word in content_lower for word in ["support", "help", "issue", "problem"]):
                email_type = "support"
            
            # Sentiment analysis (basic)
            sentiment = "neutral"
            if any(word in content_lower for word in ["angry", "frustrated", "terrible", "awful"]):
                sentiment = "negative"
            elif any(word in content_lower for word in ["great", "excellent", "wonderful", "amazing"]):
                sentiment = "positive"
            
            return str({
                "priority": priority,
                "type": email_type,
                "sentiment": sentiment,
                "confidence": 0.8  # Mock confidence score
            })
            
        except Exception as e:
            return f"Classification failed: {str(e)}"
    
    async def _arun(self, email_content: str) -> str:
        """Async version of email classification"""
        return self._run(email_content)


class EmailAgent(BaseAgentFactory):
    """Intelligent Email Processing Agent"""
    
    def __init__(self, config: EmailConfig):
        super().__init__(config)
        self.config = config
        self._sender_tool = EmailSenderTool(config)
        self._reader_tool = EmailReaderTool(config)
        self._classifier_tool = EmailClassifierTool()
    
    async def initialize(self) -> bool:
        """Initialize the email agent"""
        try:
            # Initialize tools
            self._tools = [self._sender_tool, self._reader_tool, self._classifier_tool]
            return True
        except Exception as e:
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """Execute email task"""
        start_time = time.time()
        
        try:
            action = task.get("action", "read")
            
            # Check tier limits
            if self.config.tier == AgentTier.FREE and action in ["send"] and task.get("bulk", False):
                return AgentResult(
                    success=False,
                    error="Bulk email sending requires premium tier",
                    execution_time=time.time() - start_time
                )
            
            if action == "send":
                result = await self._sender_tool._arun(
                    to_address=task.get("to", ""),
                    subject=task.get("subject", ""),
                    body=task.get("body", ""),
                    cc=task.get("cc", ""),
                    bcc=task.get("bcc", ""),
                    html=task.get("html", False)
                )
                operation = "email_send"
                
            elif action == "read":
                result = await self._reader_tool._arun(
                    folder=task.get("folder", "INBOX"),
                    limit=task.get("limit", 10),
                    filter_subject=task.get("filter_subject", ""),
                    unread_only=task.get("unread_only", True)
                )
                operation = "email_read"
                
            elif action == "classify":
                result = await self._classifier_tool._arun(
                    email_content=task.get("content", "")
                )
                operation = "email_classify"
                
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown action: {action}",
                    execution_time=time.time() - start_time
                )
            
            # Track usage
            monetization_service.track_usage(self.config.agent_id, operation)
            
            return AgentResult(
                success=True,
                data={
                    "action": action,
                    "result": result,
                    "agent_version": self.config.version
                },
                metadata={
                    "tier": self.config.tier.value,
                    "operation": operation
                },
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def cleanup(self) -> bool:
        """Cleanup resources"""
        try:
            # Close any open connections
            return True
        except Exception:
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Get agent tools"""
        return self._tools


# Register the agent
from ai_mega_agents_factory import agent_registry
agent_registry.register_agent_type("email", EmailAgent)