#!/bin/bash
# Deployment script for Magang Berdampak API

set -e  # Exit on any error

echo "🚀 Starting Magang Berdampak API Deployment..."

# Configuration
PROJECT_NAME="magang-berdampak-api"
PROJECT_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="magang-api"
USER="www-data"
GROUP="www-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

print_status "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv nginx sqlite3 curl

# Create project directory
print_status "Setting up project directory..."
mkdir -p $PROJECT_DIR
mkdir -p /var/log/magang-api
mkdir -p /var/run/magang-api

# Set permissions
chown -R $USER:$GROUP $PROJECT_DIR
chown -R $USER:$GROUP /var/log/magang-api
chown -R $USER:$GROUP /var/run/magang-api

print_status "Copying application files..."
# Copy current directory to project directory
cp -r . $PROJECT_DIR/
cd $PROJECT_DIR

print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Fix requirements.txt (remove problematic entries)
sed -i '/sqlite3/d' requirements.txt
sed -i '/asyncio/d' requirements.txt
pip install -r requirements.txt

print_status "Setting up database directory..."
mkdir -p database
chown -R $USER:$GROUP database
chmod 755 database

print_status "Setting up systemd service..."
cp deployment/magang-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

print_status "Setting up log rotation..."
cat > /etc/logrotate.d/magang-api << EOF
/var/log/magang-api/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

print_status "Setting up cron job for scraping..."
# Add cron job for www-data user
crontab -u $USER -l 2>/dev/null | { cat; echo "0 */6 * * * cd $PROJECT_DIR/scraper_new && $PROJECT_DIR/venv/bin/python scraper.py >> /var/log/magang-api/scraper-cron.log 2>&1"; } | crontab -u $USER -

print_status "Setting up Nginx (optional)..."
read -p "Do you want to setup Nginx reverse proxy? (y/n): " setup_nginx

if [ "$setup_nginx" = "y" ] || [ "$setup_nginx" = "Y" ]; then
    print_status "Configuring Nginx..."
    
    cat > /etc/nginx/sites-available/magang-api << EOF
server {
    listen 80;
    server_name _; # Change this to your domain
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Optional: serve static files directly (if you have any)
    location /static/ {
        alias $PROJECT_DIR/static/;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/magang-api /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    print_status "Nginx configured successfully"
fi

print_status "Setting up environment variables..."
cat > $PROJECT_DIR/.env << EOF
ENVIRONMENT=production
MAGANG_API_KEY=$(openssl rand -hex 32)
EOF

print_status "Setting final permissions..."
chown -R $USER:$GROUP $PROJECT_DIR
chmod +x $PROJECT_DIR/scraper_new/scraper.py

print_status "Starting services..."
systemctl start $SERVICE_NAME
systemctl status $SERVICE_NAME --no-pager

print_status "Running initial scrape..."
cd $PROJECT_DIR/scraper_new
sudo -u $USER $PROJECT_DIR/venv/bin/python scraper.py

echo ""
print_status "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. API is running on http://localhost:8000"
echo "2. API documentation: http://localhost:8000/docs"
echo "3. Check API status: http://localhost:8000/health"
echo "4. View logs: journalctl -u $SERVICE_NAME -f"
echo "5. Check scraper logs: tail -f /var/log/magang-api/scraper-cron.log"
echo ""
echo "🔑 Your API key is stored in $PROJECT_DIR/.env"
echo "📝 Update your domain in /etc/nginx/sites-available/magang-api if using Nginx"
echo ""
echo "🔄 The scraper will run automatically every 6 hours"
echo "📊 Access API stats: http://localhost:8000/api/v1/stats" 