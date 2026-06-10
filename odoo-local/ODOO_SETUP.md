# Odoo Setup Guide - Fix Chart of Accounts

## Issue
Chart of accounts not showing up after creating invoices/payments.

## Root Cause
The **Accounting** app module is not installed or fiscal localization not configured.

## Solution

### Step 1: Access Odoo
1. Open browser: http://localhost:8069
2. Login with your admin credentials

### Step 2: Install Accounting Module

1. **Go to Apps**
   - Click on top menu: **Apps**
   - Remove "Apps" filter to see all modules

2. **Search for "Accounting"**
   - Type "accounting" in search box
   - Find "**Accounting**" or "**Invoicing**" module

3. **Install**
   - Click **Install** button
   - Wait for installation to complete (may take 1-2 minutes)

### Step 3: Configure Chart of Accounts

After installation, Odoo will prompt you to configure:

1. **Select Country/Localization**
   - Choose your country (e.g., "United States - Chart of Accounts")
   - This sets up the default chart of accounts

2. **Company Information**
   - Verify company name
   - Enter tax ID if needed

3. **Fiscal Year**
   - Select fiscal year start date
   - Usually January 1st

4. **Click "Create"**

### Step 4: Verify Chart of Accounts

1. **Go to Accounting Dashboard**
   - Top menu → **Accounting**

2. **Check Configuration**
   - Go to: **Configuration** → **Chart of Accounts**
   - You should now see account list:
     - Assets
     - Liabilities
     - Equity
     - Revenue
     - Expenses

3. **Verify Journals**
   - Go to: **Configuration** → **Journals**
   - You should see:
     - Customer Invoices
     - Vendor Bills
     - Bank
     - Cash
     - Miscellaneous Operations

## If Chart of Accounts Still Missing

### Option 1: Install via Command Line
```bash
docker exec odoo-local-odoo-1 odoo -d odoo -i account --stop-after-init
```

### Option 2: Database Manager
1. Go to: http://localhost:8069/web/database/manager
2. Duplicate your database
3. During creation, select "**Load demonstration data**"
4. This ensures accounting data is pre-loaded

### Option 3: Fresh Start (Nuclear Option)
```bash
cd /mnt/d/FTE_Employee/hackathon_zero/odoo-local
docker-compose down -v  # Removes volumes (deletes data!)
docker-compose up -d
```
Then:
1. Access http://localhost:8069
2. Create NEW database
3. Check "**Load demonstration data**" ✅
4. Select language and country
5. Install Accounting module

## Verify Working

After setup, you should be able to:

1. **Create Invoice**
   - Accounting → Customers → Invoices
   - Create → Add lines → Confirm

2. **View Chart of Accounts**
   - Accounting → Configuration → Chart of Accounts
   - See all accounts with numbers (e.g., 100000 - Accounts Receivable)

3. **Register Payment**
   - Open an invoice → Register Payment
   - Select bank/cash journal
   - Payment should post to accounts

4. **View Journal Entries**
   - Accounting → Accounting → Journal Entries
   - See the accounting entries created

## Quick Test

Run this to check if accounting is installed:
```bash
docker exec odoo-local-odoo-1 odoo shell -d odoo --no-http -c - <<EOF
env['ir.module.module'].search([('name', '=', 'account')]).write({'state': 'installed'})
env.cr.commit()
EOF
```

## For MCP Integration

Once working, note these details:
- **URL:** http://localhost:8069
- **Database:** odoo
- **Username:** admin
- **Password:** [your_password]
- **Port:** 8069

These will be used in the Odoo MCP server configuration.
