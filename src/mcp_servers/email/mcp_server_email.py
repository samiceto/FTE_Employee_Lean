#!/usr/bin/env python3
"""
Email MCP Server - A Model Context Protocol server that provides email functionality.
Enables LLMs to compose and send emails, as well as search for attachments within specified directories.
"""

import asyncio
import os
import smtplib
import socket
import time
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import argparse
import sys
import logging
from typing import Any
from pathlib import Path
from src.core.errors import NetworkTimeout, ServiceUnavailable
from src.logging.audit_logger import audit_logger

logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    print("Error: mcp is required. Please install it using 'pip install mcp'", file=sys.stderr)
    sys.exit(1)


class EmailConfig:
    """Email SMTP configuration for different providers."""

    def __init__(self):
        self.email_configs = [
            {"domain": "gmail.com", "smtp_server": "smtp.gmail.com", "smtp_port": 587},
            {"domain": "outlook.com", "smtp_server": "smtp.office365.com", "smtp_port": 587},
            {"domain": "yahoo.com", "smtp_server": "smtp.mail.yahoo.com", "smtp_port": 587},
            {"domain": "qq.com", "smtp_server": "smtp.qq.com", "smtp_port": 587},
            {"domain": "126.com", "smtp_server": "smtp.126.com", "smtp_port": 25},
        ]

    def get_smtp_config(self, email_address: str):
        """Get SMTP configuration based on email domain."""
        domain = email_address.split('@')[-1]
        for config in self.email_configs:
            if config['domain'] == domain:
                return config
        # Default to Gmail if domain not found
        return self.email_configs[0]


def get_attachment_content_type(filepath: str) -> str:
    """Get the content type of an attachment."""
    content_type, _ = mimetypes.guess_type(filepath)
    if content_type is None:
        content_type = 'application/octet-stream'
    return content_type


def is_supported_attachment(filepath: str) -> bool:
    """Check if the file type is supported for attachment."""
    _, ext = os.path.splitext(filepath.lower())
    supported_extensions = {
        # Documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # Text files
        '.txt', '.log', '.csv', '.json', '.xml', '.md',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp'
    }
    return ext in supported_extensions


def _send_email_with_smtp(sender_email: str, sender_password: str, msg: MIMEMultipart,
                          smtp_config: dict, max_attempts: int = 3) -> str:
    """
    Send email with SMTP timeout and retry.

    Args:
        sender_email: Sender email address
        sender_password: Sender password
        msg: Prepared email message
        smtp_config: SMTP configuration dict
        max_attempts: Maximum retry attempts

    Returns:
        Success message

    Raises:
        NetworkTimeout: If SMTP connection times out
        ServiceUnavailable: If SMTP service is unavailable
    """
    base_delay = 2
    max_delay = 30

    for attempt in range(max_attempts):
        try:
            # Create SMTP connection with 15 second timeout
            with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'], timeout=15) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            receiver_list = msg['To']
            return f"Email sent successfully to {receiver_list}"

        except socket.timeout:
            if attempt == max_attempts - 1:
                raise NetworkTimeout("SMTP timeout after all retries")
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"SMTP timeout, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)

        except smtplib.SMTPException as e:
            if attempt == max_attempts - 1:
                raise ServiceUnavailable(f"SMTP error: {e}")
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"SMTP error: {e}, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)

    raise ServiceUnavailable("Failed to send email after all retries")


async def send_email(receiver: list[str], body: str, subject: str, attachments: list[str], attachment_dir: str | None) -> str:
    """
    Send an email with optional attachments, timeout, and retry.

    Args:
        receiver: List of recipient email addresses
        body: Email body text
        subject: Email subject
        attachments: List of attachment filenames
        attachment_dir: Directory containing attachments

    Returns:
        Success message

    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If attachment not found
        NetworkTimeout: If SMTP times out
        ServiceUnavailable: If email service unavailable
    """
    # Log MCP call
    audit_logger.log_mcp_call(
        server='email',
        tool='send_email',
        arguments={
            'receiver': receiver,
            'subject': subject,
            'has_attachments': bool(attachments)
        }
    )

    start_time = time.time()

    try:
        sender_email = os.getenv('SENDER')
        sender_password = os.getenv('PASSWORD')

        if not sender_email or not sender_password:
            raise ValueError("SENDER and PASSWORD environment variables must be set")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver)
        msg['Subject'] = subject

        # Add body to email
        msg.attach(MIMEText(body, 'plain'))

        # Add attachments if provided
        if attachments:
            for filename in attachments:
                filepath = os.path.join(attachment_dir, filename) if attachment_dir else filename

                if not os.path.isfile(filepath):
                    raise FileNotFoundError(f"Attachment file not found: {filepath}")

                if not is_supported_attachment(filepath):
                    raise ValueError(f"Unsupported file type for attachment: {filepath}")

                with open(filepath, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(filepath)}',
                )
                msg.attach(part)

        # Get SMTP configuration
        email_config = EmailConfig()
        smtp_config = email_config.get_smtp_config(sender_email)

        # Send email with timeout and retry (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _send_email_with_smtp,
            sender_email,
            sender_password,
            msg,
            smtp_config
        )

        # Log success
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_mcp_success(
            server='email',
            tool='send_email',
            duration_ms=duration_ms
        )

        return result

    except (NetworkTimeout, ServiceUnavailable) as e:
        # Log failure
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_mcp_failure(
            server='email',
            tool='send_email',
            error=str(e),
            duration_ms=duration_ms
        )
        # Log error and re-raise for graceful degradation (queue fallback in Phase 4)
        logger.error(f"Failed to send email: {e}")
        raise
    except Exception as e:
        # Log failure
        duration_ms = (time.time() - start_time) * 1000
        audit_logger.log_mcp_failure(
            server='email',
            tool='send_email',
            error=str(e),
            duration_ms=duration_ms
        )
        logger.error(f"Unexpected error sending email: {e}")
        raise Exception(f"Failed to send email: {str(e)}")


async def search_attachments(pattern: str, attachment_dir: str | None) -> dict:
    """Search for files matching pattern in attachment directory."""
    if not attachment_dir or not os.path.isdir(attachment_dir):
        return {
            'pattern': pattern,
            'directory': attachment_dir or 'None',
            'total_found': 0,
            'files': []
        }

    matching_files = []
    pattern_lower = pattern.lower()

    for root, dirs, files in os.walk(attachment_dir):
        for filename in files:
            if pattern_lower in filename.lower():
                filepath = os.path.join(root, filename)
                file_size = os.path.getsize(filepath)
                matching_files.append({
                    'filename': filename,
                    'path': filepath,
                    'size_bytes': file_size
                })

    return {
        'pattern': pattern,
        'directory': attachment_dir,
        'total_found': len(matching_files),
        'files': matching_files
    }


# Create server instance
server = Server("email-server")
ATTACHMENT_DIR = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="send_email",
            description="Send an email with optional attachments",
            inputSchema={
                "type": "object",
                "properties": {
                    "receiver": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recipient email addresses"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attachment filenames (optional)"
                    }
                },
                "required": ["receiver", "subject", "body"]
            }
        ),
        Tool(
            name="search_attachments",
            description="Search for files in the attachment directory matching a pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern to search for in filenames"
                    }
                },
                "required": ["pattern"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "send_email":
        receiver = arguments.get("receiver", [])
        subject = arguments.get("subject", "")
        body = arguments.get("body", "")
        attachments = arguments.get("attachments", [])

        try:
            result = await send_email(receiver, body, subject, attachments, ATTACHMENT_DIR)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "search_attachments":
        pattern = arguments.get("pattern", "")

        try:
            result = await search_attachments(pattern, ATTACHMENT_DIR)
            # Format the results nicely
            output = f"Found {result['total_found']} file(s) matching pattern '{result['pattern']}':\n"
            if result['files']:
                for file_info in result['files']:
                    output += f"\n- {file_info['filename']}"
                    output += f"\n  Path: {file_info['path']}"
                    output += f"\n  Size: {file_info['size_bytes']} bytes\n"
            else:
                output += "(no matches found)"

            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the MCP server."""
    global ATTACHMENT_DIR

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Email MCP Server")
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Directory to search for attachments"
    )
    args = parser.parse_args()

    ATTACHMENT_DIR = args.dir

    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == '__main__':
    asyncio.run(main())
