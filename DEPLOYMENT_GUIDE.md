# 🚀 Production Deployment Guide - Sacco Management System

## ⚠️ **CRITICAL SECURITY FIXES REQUIRED**

Before deploying to production, you **MUST** address these critical security issues:

### 1. **SECRET KEY SECURITY** 🔐
```bash
# Generate a new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set in environment variables
export SECRET_KEY="your-new-secret-key-here"
```

### 2. **ENVIRONMENT CONFIGURATION** ⚙️
```bash
# Copy environment template
cp env.example .env

# Edit .env with your production values
nano .env
```

### 3. **DATABASE MIGRATION** 🗄️
```bash
# Install PostgreSQL dependencies
sudo apt-get install postgresql postgresql-contrib python3-psycopg2

# Create database
sudo -u postgres createdb sacco_system

# Run migrations
python manage.py migrate --settings=sacco_system.settings_production
```

## 🐳 **Docker Deployment (Recommended)**

### Prerequisites
- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (for HTTPS)

### Step 1: Clone and Configure
```bash
git clone <your-repo>
cd sacco-system

# Copy environment file
cp env.example .env

# Edit .env with production values
nano .env
```

### Step 2: Build and Deploy
```bash
# Build and start services
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate --settings=sacco_system.settings_production

# Create superuser
docker-compose exec web python manage.py createsuperuser --settings=sacco_system.settings_production

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput --settings=sacco_system.settings_production
```

### Step 3: Verify Deployment
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f web

# Test application
curl http://localhost:8000
```

## 🖥️ **Manual Deployment**

### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Nginx
sudo apt install nginx
```

### Step 2: Application Setup
```bash
# Create application directory
sudo mkdir -p /var/www/sacco-system
sudo chown $USER:$USER /var/www/sacco-system

# Clone repository
cd /var/www/sacco-system
git clone <your-repo> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_production.txt
```

### Step 3: Database Configuration
```bash
# Create database user
sudo -u postgres createuser --interactive
# Enter username: sacco_user
# Enter role: y

# Create database
sudo -u postgres createdb sacco_system

# Set password for user
sudo -u postgres psql
ALTER USER sacco_user PASSWORD 'your-secure-password';
\q
```

### Step 4: Application Configuration
```bash
# Create environment file
cp env.example .env
nano .env

# Set production settings
export DJANGO_SETTINGS_MODULE=sacco_system.settings_production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create logs directory
mkdir -p logs
```

### Step 5: Gunicorn Configuration
```bash
# Create Gunicorn service file
sudo nano /etc/systemd/system/sacco-system.service
```

```ini
[Unit]
Description=Sacco Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sacco-system
Environment="PATH=/var/www/sacco-system/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=sacco_system.settings_production"
ExecStart=/var/www/sacco-system/venv/bin/gunicorn --workers 3 --bind unix:/var/www/sacco-system/sacco-system.sock sacco_system.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable sacco-system
sudo systemctl start sacco-system
sudo systemctl status sacco-system
```

### Step 6: Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/sacco-system
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /var/www/sacco-system;
    }

    location /media/ {
        root /var/www/sacco-system;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/sacco-system/sacco-system.sock;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sacco-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 **SSL Configuration (Let's Encrypt)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 📊 **Monitoring and Maintenance**

### Log Monitoring
```bash
# Application logs
tail -f /var/www/sacco-system/logs/django.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u sacco-system -f
```

### Database Backup
```bash
# Create backup script
nano /var/www/sacco-system/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/www/sacco-system/backups"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump sacco_system > $BACKUP_DIR/sacco_system_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Make executable and add to crontab
chmod +x /var/www/sacco-system/backup.sh
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /var/www/sacco-system/backup.sh
```

### Performance Monitoring
```bash
# Install monitoring tools
pip install django-debug-toolbar

# Monitor system resources
htop
iostat -x 1
```

## 🚨 **Security Checklist**

- [ ] Secret key moved to environment variables
- [ ] DEBUG = False in production
- [ ] ALLOWED_HOSTS configured
- [ ] Database credentials secured
- [ ] SSL certificate installed
- [ ] Firewall configured (UFW)
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Log monitoring in place
- [ ] Rate limiting configured
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] Content Security Policy configured

## 🔧 **Troubleshooting**

### Common Issues

1. **Static files not loading**
   ```bash
   python manage.py collectstatic --noinput
   sudo chown -R www-data:www-data /var/www/sacco-system/staticfiles
   ```

2. **Database connection errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check database exists
   sudo -u postgres psql -l
   ```

3. **Permission errors**
   ```bash
   sudo chown -R www-data:www-data /var/www/sacco-system
   sudo chmod -R 755 /var/www/sacco-system
   ```

4. **Gunicorn not starting**
   ```bash
   # Check logs
   sudo journalctl -u sacco-system -f
   
   # Test Gunicorn manually
   cd /var/www/sacco-system
   source venv/bin/activate
   gunicorn --bind 0.0.0.0:8000 sacco_system.wsgi:application
   ```

## 📈 **Performance Optimization**

1. **Database Optimization**
   - Add database indexes
   - Use select_related and prefetch_related
   - Enable query caching

2. **Static Files**
   - Use CDN for static files
   - Enable gzip compression
   - Set proper cache headers

3. **Caching**
   - Enable Redis caching
   - Use template caching
   - Implement view caching

4. **Database Connection Pooling**
   - Configure pgbouncer
   - Optimize connection settings

## 🆘 **Support and Maintenance**

- Regular security updates
- Database maintenance
- Log rotation
- Performance monitoring
- Backup verification
- SSL certificate renewal

---

**⚠️ IMPORTANT**: This system handles sensitive financial data. Ensure all security measures are properly implemented before going live.











