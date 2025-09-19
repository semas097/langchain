"""Email Agent implementation."""

from __future__ import annotations

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, Dict, List, Optional
import ssl

from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool, tool

from langchain_community.agent_toolkits.ai_mega_agents_factory.base import (
    AgentCategory,
    BaseMegaAgent,
    MegaAgentConfig,
    MegaAgentManifest,
    MonetizationTier,
)


class EmailMetrics:
    """Email operation metrics."""
    
    def __init__(self):
        """Initialize metrics."""
        self.reset()
    
    def reset(self) -> None:
        """Reset metrics."""
        self.emails_sent = 0
        self.emails_failed = 0
        self.total_recipients = 0
        self.execution_time = 0.0
        self.success_rate = 0.0


@tool
def send_email(
    smtp_config: Dict[str, Any],
    recipients: List[str],
    subject: str,
    body: str,
    sender: str,
    body_type: str = "plain",
    attachments: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Send email to recipients.
    
    Args:
        smtp_config: SMTP server configuration
        recipients: List of recipient email addresses
        subject: Email subject
        body: Email body content
        sender: Sender email address
        body_type: Email body type (plain or html)
        attachments: Optional list of attachment file paths
        
    Returns:
        Email sending results
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, body_type))
        
        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {file_path.split('/')[-1]}",
                    )
                    msg.attach(part)
                except Exception as e:
                    return {
                        "status": "error",
                        "error": f"Failed to attach file {file_path}: {str(e)}",
                    }
        
        # Connect to SMTP server and send
        server_host = smtp_config.get("host", "smtp.gmail.com")
        server_port = smtp_config.get("port", 587)
        use_tls = smtp_config.get("use_tls", True)
        username = smtp_config.get("username")
        password = smtp_config.get("password")
        
        with smtplib.SMTP(server_host, server_port) as server:
            if use_tls:
                server.starttls(context=ssl.create_default_context())
            
            if username and password:
                server.login(username, password)
            
            server.send_message(msg)
        
        return {
            "status": "success",
            "recipients_count": len(recipients),
            "message_id": msg.get("Message-ID"),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def send_bulk_email(
    smtp_config: Dict[str, Any],
    email_list: List[Dict[str, Any]],
    sender: str,
) -> Dict[str, Any]:
    """Send bulk emails with personalization.
    
    Args:
        smtp_config: SMTP server configuration
        email_list: List of email configurations
        sender: Sender email address
        
    Returns:
        Bulk email results
    """
    try:
        results = []
        successful_sends = 0
        failed_sends = 0
        
        for email_config in email_list:
            result = send_email.invoke({
                "smtp_config": smtp_config,
                "recipients": email_config.get("recipients", []),
                "subject": email_config.get("subject", ""),
                "body": email_config.get("body", ""),
                "sender": sender,
                "body_type": email_config.get("body_type", "plain"),
                "attachments": email_config.get("attachments"),
            })
            
            results.append(result)
            
            if result.get("status") == "success":
                successful_sends += 1
            else:
                failed_sends += 1
        
        return {
            "status": "success",
            "total_emails": len(email_list),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "success_rate": successful_sends / len(email_list) if email_list else 0,
            "detailed_results": results,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def generate_email_template(
    template_type: str,
    variables: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate email from template.
    
    Args:
        template_type: Type of email template
        variables: Variables to substitute in template
        
    Returns:
        Generated email content
    """
    try:
        templates = {
            "welcome": {
                "subject": "Welcome to {company_name}!",
                "body": """
Dear {customer_name},

Welcome to {company_name}! We're excited to have you on board.

Your account has been successfully created with the following details:
- Email: {email}
- Account Type: {account_type}

To get started, please visit: {login_url}

If you have any questions, please contact our support team at {support_email}.

Best regards,
The {company_name} Team
                """,
            },
            "notification": {
                "subject": "{notification_type}: {title}",
                "body": """
Hello {recipient_name},

This is a notification regarding: {title}

Details:
{message}

Time: {timestamp}
Priority: {priority}

Please take appropriate action if required.

Best regards,
{sender_name}
                """,
            },
            "marketing": {
                "subject": "{campaign_name} - Special Offer Inside!",
                "body": """
Dear Valued Customer,

We have an exciting offer just for you!

{offer_description}

Offer Details:
- Discount: {discount_percentage}%
- Valid Until: {expiry_date}
- Promo Code: {promo_code}

Don't miss out - this offer expires soon!

Shop now: {shop_url}

Best regards,
{company_name} Marketing Team
                """,
            },
        }
        
        if template_type not in templates:
            return {
                "status": "error",
                "error": f"Unknown template type: {template_type}",
                "available_templates": list(templates.keys()),
            }
        
        template = templates[template_type]
        
        # Substitute variables
        subject = template["subject"].format(**variables)
        body = template["body"].format(**variables)
        
        return {
            "status": "success",
            "template_type": template_type,
            "subject": subject,
            "body": body.strip(),
        }
        
    except KeyError as e:
        return {
            "status": "error",
            "error": f"Missing template variable: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def validate_email_addresses(email_addresses: List[str]) -> Dict[str, Any]:
    """Validate email addresses format.
    
    Args:
        email_addresses: List of email addresses to validate
        
    Returns:
        Validation results
    """
    import re
    
    try:
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        valid_emails = []
        invalid_emails = []
        
        for email in email_addresses:
            if email_regex.match(email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
        
        return {
            "status": "success",
            "total_count": len(email_addresses),
            "valid_count": len(valid_emails),
            "invalid_count": len(invalid_emails),
            "valid_emails": valid_emails,
            "invalid_emails": invalid_emails,
            "validation_rate": len(valid_emails) / len(email_addresses) if email_addresses else 0,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


class EmailAgent(BaseMegaAgent):
    """Email Agent for enterprise email communications."""
    
    def __init__(
        self,
        config: Optional[MegaAgentConfig] = None,
        llm: Optional[BaseLanguageModel] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ):
        """Initialize Email Agent.
        
        Args:
            config: Agent configuration
            llm: Language model
            callback_manager: Callback manager
            **kwargs: Additional arguments
        """
        if config is None:
            manifest = MegaAgentManifest(
                name="Email Agent",
                version="1.0.0",
                category=AgentCategory.COMMUNICATION,
                description="Enterprise email agent for automated communications",
                author="AI Mega Agents Factory",
                tags=["email", "communication", "automation", "marketing"],
                min_langchain_version="0.1.0",
                supported_llm_types=["openai", "anthropic", "huggingface"],
                required_tools=["smtp", "email"],
                monetization_tier=MonetizationTier.BASIC,
                pricing_model="usage_based",
            )
            config = MegaAgentConfig(manifest=manifest)
        
        super().__init__(config, llm, callback_manager, **kwargs)
        self.metrics = EmailMetrics()
        
    def initialize(self) -> None:
        """Initialize the email agent."""
        if self._initialized:
            return
            
        self._tools = self.get_tools()
        self._initialized = True
    
    def get_tools(self) -> List[BaseTool]:
        """Get email tools.
        
        Returns:
            List of email tools
        """
        return [
            send_email,
            send_bulk_email,
            generate_email_template,
            validate_email_addresses,
        ]
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute email operation.
        
        Args:
            input_data: Email operation configuration
            **kwargs: Additional execution parameters
            
        Returns:
            Email operation results
        """
        start_time = time.time()
        self.metrics.reset()
        
        try:
            if not self.validate_input(input_data):
                return {
                    "status": "error",
                    "error": "Invalid input data",
                    "required_fields": ["operation", "smtp_config"],
                }
            
            operation = input_data.get("operation")
            smtp_config = input_data.get("smtp_config", {})
            
            if operation == "send_single":
                result = await self._send_single_email(input_data, smtp_config)
            elif operation == "send_bulk":
                result = await self._send_bulk_emails(input_data, smtp_config)
            elif operation == "generate_template":
                result = await self._generate_template(input_data)
            elif operation == "validate_addresses":
                result = await self._validate_addresses(input_data)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "supported_operations": ["send_single", "send_bulk", "generate_template", "validate_addresses"],
                }
            
            self.metrics.execution_time = time.time() - start_time
            
            # Update metrics based on result
            if result.get("status") == "success":
                if operation in ["send_single", "send_bulk"]:
                    self.metrics.emails_sent = result.get("recipients_count", result.get("successful_sends", 0))
                    self.metrics.emails_failed = result.get("failed_sends", 0)
                    self.metrics.total_recipients = result.get("recipients_count", result.get("total_emails", 0))
                    
                    if self.metrics.total_recipients > 0:
                        self.metrics.success_rate = self.metrics.emails_sent / self.metrics.total_recipients
            
            result.update({
                "execution_time": self.metrics.execution_time,
                "metrics": self.get_metrics(),
            })
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
            }
    
    async def _send_single_email(self, input_data: Dict[str, Any], smtp_config: Dict[str, Any]) -> Dict[str, Any]:
        """Send single email."""
        return send_email.invoke({
            "smtp_config": smtp_config,
            "recipients": input_data.get("recipients", []),
            "subject": input_data.get("subject", ""),
            "body": input_data.get("body", ""),
            "sender": input_data.get("sender", ""),
            "body_type": input_data.get("body_type", "plain"),
            "attachments": input_data.get("attachments"),
        })
    
    async def _send_bulk_emails(self, input_data: Dict[str, Any], smtp_config: Dict[str, Any]) -> Dict[str, Any]:
        """Send bulk emails."""
        return send_bulk_email.invoke({
            "smtp_config": smtp_config,
            "email_list": input_data.get("email_list", []),
            "sender": input_data.get("sender", ""),
        })
    
    async def _generate_template(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email template."""
        return generate_email_template.invoke({
            "template_type": input_data.get("template_type", ""),
            "variables": input_data.get("variables", {}),
        })
    
    async def _validate_addresses(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email addresses."""
        return validate_email_addresses.invoke({
            "email_addresses": input_data.get("email_addresses", []),
        })
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate email input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["operation"]
        
        for field in required_fields:
            if field not in input_data:
                return False
        
        operation = input_data["operation"]
        
        if operation in ["send_single", "send_bulk"] and "smtp_config" not in input_data:
            return False
        
        if operation == "send_single":
            required_email_fields = ["recipients", "subject", "body", "sender"]
            for field in required_email_fields:
                if field not in input_data:
                    return False
        
        if operation == "send_bulk":
            if "email_list" not in input_data or "sender" not in input_data:
                return False
        
        if operation == "generate_template":
            if "template_type" not in input_data or "variables" not in input_data:
                return False
        
        if operation == "validate_addresses":
            if "email_addresses" not in input_data:
                return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get email metrics.
        
        Returns:
            Current metrics
        """
        return {
            "emails_sent": self.metrics.emails_sent,
            "emails_failed": self.metrics.emails_failed,
            "total_recipients": self.metrics.total_recipients,
            "success_rate": self.metrics.success_rate,
            "execution_time": self.metrics.execution_time,
        }