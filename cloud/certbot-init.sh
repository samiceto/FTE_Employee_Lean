#!/usr/bin/env bash
# Obtain Let's Encrypt certificate for Odoo
# Run AFTER azure_vm_setup.sh and after Nginx is up
# Usage: ./certbot-init.sh yourdomain.example.com your@email.com

set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"

[[ -n "$DOMAIN" ]] || { echo "Usage: $0 DOMAIN EMAIL"; exit 1; }
[[ -n "$EMAIL" ]] || { echo "Usage: $0 DOMAIN EMAIL"; exit 1; }

echo "[certbot] Obtaining certificate for ${DOMAIN}..."

# Update nginx config with real domain
sed -i "s/YOUR_DOMAIN_OR_IP/${DOMAIN}/g" "$(dirname "$0")/nginx/conf.d/odoo.conf"

# Reload nginx to pick up domain change
docker compose exec nginx nginx -s reload || true

# Run certbot
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    -d "${DOMAIN}"

# Reload nginx with SSL
docker compose exec nginx nginx -s reload

echo ""
echo "✅ Certificate obtained for ${DOMAIN}"
echo "   Odoo is now available at https://${DOMAIN}"
echo ""
echo "   Certificate auto-renews via certbot container."
echo "   Check renewal: docker compose logs certbot"
