#!/usr/bin/env bash
# ============================================================
# MIT Assistent — Production Deploy Script for Ubuntu 24.04
# Run as root on a fresh VPS
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC} $*"; exit 1; }

# --- Config ---
PROJECT_DIR="/opt/mit-assistent/backend"
VENV_DIR="$PROJECT_DIR/venv"
APP_USER="www-data"
LOG_DIR="/var/log/mit-assistent"

# --- Check root ---
if [ "$(id -u)" -ne 0 ]; then
    err "This script must be run as root"
fi

# --- System packages ---
log "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3.12 python3.12-venv python3.12-dev \
    postgresql postgresql-client \
    nginx certbot python3-certbot-nginx \
    build-essential libpq-dev \
    curl git

# --- PostgreSQL setup ---
log "Setting up PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

# Generate random password
DB_PASSWORD=$(openssl rand -base64 32)

# Create user and database
su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='mit_assistent_user'\" | grep -q 1" || \
    su - postgres -c "psql -c \"CREATE USER mit_assistent_user WITH PASSWORD '$DB_PASSWORD';\""

su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='mit_assistent'\" | grep -q 1" || \
    su - postgres -c "psql -c \"CREATE DATABASE mit_assistent OWNER mit_assistent_user;\""

su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE mit_assistent TO mit_assistent_user;\""
su - postgres -c "psql -c \"ALTER USER mit_assistent_user CREATEDB;\""

log "PostgreSQL: database=mit_assistent, user=mit_assistent_user"

# --- Project directory ---
log "Creating project directory..."
mkdir -p "$PROJECT_DIR"
mkdir -p "$LOG_DIR"
chown -R "$APP_USER:$APP_USER" "$LOG_DIR"

# --- Python venv ---
log "Creating Python virtual environment..."
python3.12 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q

# --- Generate SECRET_KEY ---
SECRET_KEY=$(python3.12 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# --- .env file ---
log "Creating .env..."
cat > "$PROJECT_DIR/.env" << EOF
# Django
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=api.titovtech.ru,localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=mit_assistent
DB_USER=mit_assistent_user
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://titovtech.ru,https://www.titovtech.ru
CSRF_TRUSTED_ORIGINS=https://api.titovtech.ru,https://titovtech.ru,https://www.titovtech.ru
EOF

chmod 640 "$PROJECT_DIR/.env"
chown "$APP_USER:$APP_USER" "$PROJECT_DIR/.env"

log ".env created at $PROJECT_DIR/.env"

# --- Install Python dependencies ---
log "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q

# --- Django setup ---
log "Running Django migrations..."
cd "$PROJECT_DIR"
"$VENV_DIR/bin/python" manage.py migrate --noinput

log "Collecting static files..."
"$VENV_DIR/bin/python" manage.py collectstatic --noinput

log "Running deploy checks..."
"$VENV_DIR/bin/python" manage.py check --deploy || warn "Deploy checks have warnings (review above)"

# --- Set permissions ---
chown -R "$APP_USER:$APP_USER" "$PROJECT_DIR"

# --- systemd ---
log "Setting up systemd service..."
cp "$PROJECT_DIR/deploy/mit-assistent.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable mit-assistent
systemctl start mit-assistent

log "Gunicorn service started"

# --- Nginx ---
log "Setting up Nginx..."
cp "$PROJECT_DIR/deploy/nginx-api.titovtech.ru.conf" /etc/nginx/sites-available/api.titovtech.ru
ln -sf /etc/nginx/sites-available/api.titovtech.ru /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

log "Nginx configured"

# --- SSL (Certbot) ---
log "Requesting SSL certificate..."
certbot --nginx -d api.titovtech.ru --non-interactive --agree-tos -m "admin@titovtech.ru" --redirect || \
    warn "Certbot failed — run manually: certbot --nginx -d api.titovtech.ru"

# --- Firewall ---
log "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable || warn "UFW not available"

# --- Summary ---
echo ""
echo "============================================"
echo -e "${GREEN}  MIT Assistent Backend — Deployed!${NC}"
echo "============================================"
echo ""
echo "  Project dir:  $PROJECT_DIR"
echo "  .env file:    $PROJECT_DIR/.env"
echo "  DB name:      mit_assistent"
echo "  DB user:      mit_assistent_user"
echo "  DB password:  $DB_PASSWORD"
echo ""
echo "  Check status:"
echo "    systemctl status mit-assistent"
echo "    systemctl status nginx"
echo "    systemctl status postgresql"
echo ""
echo "  View logs:"
echo "    journalctl -u mit-assistent -f"
echo "    tail -f $LOG_DIR/gunicorn-error.log"
echo ""
echo "  Restart backend:"
echo "    systemctl restart mit-assistent"
echo ""
echo "  Backup PostgreSQL:"
echo "    su - postgres -c 'pg_dump mit_assistent' > backup_\$(date +%Y%m%d).sql"
echo ""
echo "  URLs:"
echo "    https://api.titovtech.ru/admin/"
echo "    https://api.titovtech.ru/api/faqs/"
echo "    https://api.titovtech.ru/api/leads/"
echo ""
echo "  Create superuser:"
echo "    cd $PROJECT_DIR && $VENV_DIR/bin/python manage.py createsuperuser"
echo ""
echo "============================================"
