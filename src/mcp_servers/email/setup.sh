#!/bin/bash
# Setup script for Email MCP Server

echo "Setting up Email MCP Server..."

# Install dependencies
echo "Installing dependencies..."
pip install pydantic python-dotenv --break-system-packages

# Create necessary directories
echo "Creating directories..."
mkdir -p /mnt/d/FTE_Employee/hackathon_zero/attachments
mkdir -p /mnt/d/FTE_Employee/hackathon_zero/src/mcp_servers/email

# Create the .env file if it doesn't exist
ENV_FILE="/mnt/d/FTE_Employee/hackathon_zero/src/mcp_servers/email/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    cat > "$ENV_FILE" << 'EOL'
# Email MCP Server Configuration
# Replace with your actual email and app password
SENDER=your_email@gmail.com
PASSWORD=your_app_password
EOL
fi

echo "Configuration file created at: $ENV_FILE"
echo ""
echo "To configure the Email MCP Server:"
echo "1. Edit the .env file to add your email credentials"
echo "2. For Gmail, you need to use an App Password (not your regular password)"
echo "3. Visit: https://myaccount.google.com/apppasswords"
echo "4. Generate an app password for 'Mail' and use that as the PASSWORD"
echo ""
echo "To update Claude Code configuration:"
echo "Edit ~/.config/claude-code/mcp.json and add the email server configuration"
echo ""
echo "Email MCP Server setup complete!"