# Email MCP Server

A Model Context Protocol server that provides email functionality for the Silver Tier AI Employee project. This server enables LLMs to compose and send emails, as well as search for attachments within specified directories.

## Features

- Send emails with multiple recipients
- Support for email attachments
- Search for files in directories based on pattern matching
- Secure email transmission using SMTP
- Support for Gmail, Outlook, Yahoo, QQ, and 126 email services

## Installation

1. Install the required dependencies:
```bash
pip install pydantic python-dotenv --break-system-packages
```

2. Run the setup script:
```bash
./setup.sh
```

## Configuration

1. Create a `.env` file in the `src/mcp_servers/email/` directory with your email credentials:
```env
SENDER=your_email@gmail.com
PASSWORD=your_app_password
```

> **Note**: For Gmail, you need to use an App Password instead of your regular password. Generate one at: https://myaccount.google.com/apppasswords

2. The server supports the following email providers:
   - Gmail (@gmail.com) - smtp.gmail.com:587
   - Outlook (@outlook.com) - smtp.office365.com:587
   - Yahoo (@yahoo.com) - smtp.mail.yahoo.com:587
   - QQ (@qq.com) - smtp.qq.com:587
   - 126 (@126.com) - smtp.126.com:25

## Claude Code Configuration

Add the following configuration to `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "email": {
      "command": "/usr/bin/python3",
      "args": [
        "/mnt/d/FTE_Employee/hackathon_zero/src/mcp_servers/email/mcp_server_email.py",
        "--dir",
        "/mnt/d/FTE_Employee/hackathon_zero/attachments"
      ],
      "env": {
        "SENDER": "your_email@gmail.com",
        "PASSWORD": "your_app_password"
      }
    }
  }
}
```

## Available Tools

### send_email
Sends emails with the provided subject, body, and receiver(s).

Parameters:
- `receiver` (array of strings, required): List of recipient email addresses
- `body` (string, required): The main content of the email
- `subject` (string, required): The subject line of the email
- `attachments` (array of strings, optional): Email attachments (filenames)

### search_attachments
Searches for files in a specified directory that match a given pattern.

Parameters:
- `pattern` (string, required): The text pattern to search for in file names

## Usage Examples

### Sending an Email
```json
{
  "receiver": ["recipient@example.com"],
  "subject": "Test Email from MCP Server",
  "body": "This is a test email sent via the MCP Email Server.",
  "attachments": ["document.pdf", "image.jpg"]
}
```

### Searching for Attachments
```json
{
  "pattern": "report"
}
```

## Security Notes

- For Gmail and other services, you may need to use an app-specific password
- The server supports a limited set of attachment file types for security reasons:
  - Documents: doc, docx, xls, xlsx, ppt, pptx, pdf
  - Archives: zip, rar, 7z, tar, gz
  - Text files: txt, log, csv, json, xml, md
  - Images: jpg, jpeg, png, gif, bmp

## Supported Attachment Types

The server supports the following attachment file types:
- Documents: .doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf
- Archives: .zip, .rar, .7z, .tar, .gz
- Text files: .txt, .log, .csv, .json, .xml, .md
- Images: .jpg, .jpeg, .png, .gif, .bmp