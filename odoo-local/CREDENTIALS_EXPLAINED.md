# Odoo Credentials - Explained

## Two Sets of Credentials (DON'T CONFUSE THEM!)

### 1. PostgreSQL Database Credentials
**Where:** `docker-compose.yml`
```yaml
environment:
  POSTGRES_USER: odoo
  POSTGRES_PASSWORD: odoo
```

**What they're for:**
- Internal connection between Odoo container and PostgreSQL container
- You DON'T use these to log into Odoo web interface
- These stay as `odoo/odoo` (no need to change)

---

### 2. Odoo Admin Credentials
**Where:** Set during first Odoo access
**Used in:** MCP server and skills

**What they're for:**
- Logging into Odoo web interface at http://localhost:8069
- API access (what our MCP server uses)
- Default username: `admin`
- Password: **YOU SET THIS** during initial Odoo setup

---

## How to Set Up Properly

### Step 1: First Time Odoo Access

1. Access: http://localhost:8069
2. You'll see "Create Database" screen
3. Fill in:
   - Master Password: `admin` (default, can change)
   - Database Name: `odoo`
   - Email: your@email.com
   - Password: **YOUR CHOICE** (remember this!)
   - Language: English
   - Country: United States (or your country)
   - Demo data: ✅ Check this (loads sample data)

4. Click "Create Database"

**The password you enter in step 3 is your ODOO_PASSWORD!**

### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# Odoo credentials for API access
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=the_password_you_set_in_step_1
```

**Example:**
```bash
ODOO_PASSWORD=MySecurePassword123
```

---

## Common Mistakes

### ❌ WRONG: Using PostgreSQL credentials for Odoo
```python
# This will FAIL:
odoo = OdooMCPServer(username="odoo", password="odoo")
# Error: Authentication failed
```

### ✅ CORRECT: Using Odoo admin credentials
```python
# This will WORK:
odoo = OdooMCPServer(username="admin", password="your_actual_password")
# Or let it read from .env:
odoo = OdooMCPServer()  # Reads from ODOO_PASSWORD env var
```

---

## Testing Your Credentials

### Test 1: Web Interface
```
URL: http://localhost:8069
Username: admin
Password: [your ODOO_PASSWORD]
```

If you can log in → credentials are correct!

### Test 2: Python Script
```python
from src.mcp_servers.odoo.odoo_mcp_server import OdooMCPServer

# Make sure .env has ODOO_PASSWORD set
odoo = OdooMCPServer()  # Will read from env

# If this doesn't error, credentials work!
print("✅ Connected successfully!")
```

---

## Forgot Your Odoo Password?

### Option 1: Reset via Odoo UI
1. Go to: http://localhost:8069/web/reset_password
2. Enter admin email
3. Check console logs for reset link:
   ```bash
   docker logs odoo-local-odoo-1 | grep "reset_password"
   ```

### Option 2: Database Manager
1. Go to: http://localhost:8069/web/database/manager
2. Use master password: `admin`
3. You can reset database admin password here

### Option 3: Fresh Start (Nuclear)
```bash
cd odoo-local
docker-compose down -v  # DELETES ALL DATA!
docker-compose up -d
# Then access http://localhost:8069 and set new password
```

---

## Summary

| Credential Set | Username | Password | Used For |
|----------------|----------|----------|----------|
| **PostgreSQL** | `odoo` | `odoo` | Database connection (internal) |
| **Odoo Admin** | `admin` | YOU SET THIS | Web UI + API access |

**For MCP Server:** Use ODOO_PASSWORD (Odoo admin password), NOT the PostgreSQL password!
