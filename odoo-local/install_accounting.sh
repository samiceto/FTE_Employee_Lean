#!/bin/bash
# Quick script to install accounting module in Odoo

echo "Installing Accounting module in Odoo..."

# Method 1: Try via odoo-bin
docker exec odoo-local-odoo-1 bash -c "odoo -d odoo -i account --stop-after-init" 2>&1 || {
    echo "Method 1 failed, trying Method 2..."

    # Method 2: Try via Python
    docker exec odoo-local-odoo-1 python3 -c "
import odoorpc

try:
    odoo = odoorpc.ODOO('localhost', port=8069)
    odoo.login('odoo', 'admin', 'admin')  # database, username, password

    # Install account module
    module = odoo.env['ir.module.module']
    account_module = module.search([('name', '=', 'account')])

    if account_module:
        module.browse(account_module[0]).button_immediate_install()
        print('✅ Accounting module installed!')
    else:
        print('❌ Account module not found')
except Exception as e:
    print(f'❌ Error: {e}')
    print('Please install manually via Odoo UI at http://localhost:8069')
" 2>&1
}

echo ""
echo "==== Next Steps ===="
echo "1. Access Odoo: http://localhost:8069"
echo "2. Login with your admin credentials"
echo "3. Go to Apps → Search 'Accounting' → Install"
echo "4. Configure Chart of Accounts for your country"
echo ""
