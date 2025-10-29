# 🚀 Deployment Guide

This guide covers various deployment options for the Template Flask application, from development to production environments.

## 📋 **Table of Contents**

- [Development Deployment](#development-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [CasaOS Deployment](#casaos-deployment)
- [Environment Configuration](#environment-configuration)
- [Security Considerations](#security-considerations)
- [Monitoring & Maintenance](#monitoring--maintenance)

---

## 💻 **Development Deployment**

### **Prerequisites**
- Python 3.12 or higher
- Git
- Virtual environment support

### **Step-by-Step Setup**

1. **Clone the Repository**
   ```bash
   git clone https://github.com/An0naman/template.git
   cd template
   ```

2. **Create Virtual Environment**
   ```bash
   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python run.py
   ```

5. **Access Application**
   - URL: `http://localhost:5000`
   - The application will create default database and settings

### **Development Features**
- ✅ Hot reload enabled
- ✅ Debug mode active
- ✅ Detailed error messages
- ✅ File watching for changes

---

## 🐳 **Docker Deployment**

### **Quick Start with Docker Compose**

1. **Clone and Build**
   ```bash
   git clone https://github.com/An0naman/template.git
   cd template
   docker-compose up -d
   ```

2. **Access Application**
   - URL: `http://localhost:5000`
   - Data persisted in named Docker volume

### **Docker Compose Configuration**
```yaml
services:
  template:
    build: .
    container_name: template
    restart: always
    ports:
      - "5000:5000"
    volumes:
      - template_db_data:/app/data
    environment:
      - FLASK_APP=app.py
      - FLASK_ENV=production

volumes:
  template_db_data:
    driver: local
```

### **Custom Docker Build**
```bash
# Build image
docker build -t template-app .

# Run container
docker run -d \
  --name template \
  -p 5000:5000 \
  -v template_data:/app/data \
  template-app
```

### **Docker Environment Variables**
```bash
# Production configuration
docker run -d \
  --name template \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your_production_secret_key \
  -e DATABASE_PATH=/app/data/template.db \
  -v template_data:/app/data \
  template-app
```

---

## 🌐 **Production Deployment**

### **Requirements**
- Linux server (Ubuntu 20.04+ recommended)
- Nginx (reverse proxy)
- SSL certificate
- Domain name
- Minimum 1GB RAM, 10GB storage

### **Option 1: Traditional Server Deployment**

#### **1. Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.12 python3.12-venv python3-pip nginx git -y

# Create application user
sudo useradd -m -s /bin/bash template
sudo su - template
```

#### **2. Application Setup**
```bash
# Clone repository
git clone https://github.com/An0naman/template.git
cd template

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### **3. Production Configuration**
```bash
# Create production config
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_PATH=/home/template/template/data/template.db
EOF
```

#### **4. Systemd Service**
```bash
# Create service file
sudo tee /etc/systemd/system/template.service << EOF
[Unit]
Description=Template Flask Application
After=network.target

[Service]
Type=exec
User=template
Group=template
WorkingDirectory=/home/template/template
Environment=PATH=/home/template/template/.venv/bin
ExecStart=/home/template/template/.venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 run:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable template
sudo systemctl start template
```

#### **5. Nginx Configuration**
```bash
# Create Nginx site
sudo tee /etc/nginx/sites-available/template << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/template/template/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/template /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### **6. SSL Certificate (Let's Encrypt)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Option 2: Docker in Production**

#### **1. Docker Compose for Production**
```yaml
version: '3.8'
services:
  template:
    build: .
    container_name: template-prod
    restart: always
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - template_data:/app/data
      - ./logs:/app/logs
    networks:
      - web

  nginx:
    image: nginx:alpine
    container_name: template-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - template
    networks:
      - web

volumes:
  template_data:

networks:
  web:
    external: true
```

#### **2. Environment File**
```bash
# Create .env file
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///app/data/template.db
FLASK_ENV=production
EOF
```

---

## 🏠 **CasaOS Deployment**

### **Features**
- One-click deployment
- Automatic updates
- Web-based management
- Volume persistence
- Port management

### **Installation Steps**

#### **1. Prepare CasaOS**
```bash
# Install CasaOS (if not already installed)
curl -fsSL https://get.casaos.io | sudo bash
```

#### **2. Deploy via Dev Manager**
1. Open CasaOS dashboard
2. Navigate to **Dev Manager**
3. **Import from Git**:
   - Repository: `https://github.com/An0naman/template.git`
   - Branch: `main`
4. **Configure Settings**:
   - Port: Choose available port (e.g., 5052)
   - Volume: Automatic persistence
5. **Deploy**: Click "Deploy" button

#### **3. Access Application**
- URL: `http://casaos-ip:chosen-port`
- Data automatically persisted
- Updates available through CasaOS

### **CasaOS Configuration**
```yaml
x-casaos:
  main: template
  developer: an0naman
  icon: https://cdn-icons-png.flaticon.com/512/8648/8648719.png
  description:
    en_us: "A Python Flask app with SQLite persistence."
  tag:
    en_us: latest
  category: My App
  port_map: '5000'
  container_scheme: http
```

---

## ⚙️ **Environment Configuration**

### **Environment Variables**
```bash
# Application Configuration
FLASK_APP=app.py
FLASK_ENV=production  # or development
DEBUG=False

# Security
SECRET_KEY=your_super_secret_key_here

# Database
DATABASE_PATH=/app/data/template.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=/app/logs

# Features
ENABLE_OVERDUE_CHECK=true
ENABLE_SENSOR_MONITORING=true
```

### **Production Settings**
```python
# config.py additions for production
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'
```

---

## 🔒 **Security Considerations**

### **Essential Security Steps**

#### **1. Secret Key**
```bash
# Generate secure secret key
python -c 'import secrets; print(secrets.token_hex(32))'
```

#### **2. Database Security**
```bash
# Set appropriate permissions
chmod 640 data/template.db
chown template:template data/template.db
```

#### **3. Firewall Configuration**
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

#### **4. Regular Updates**
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Application updates
cd /home/template/template
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart template
```

### **Security Checklist**
- ✅ Change default secret key
- ✅ Use HTTPS in production
- ✅ Regular security updates
- ✅ Backup database regularly
- ✅ Monitor logs for suspicious activity
- ✅ Implement rate limiting (future enhancement)
- ✅ Use strong passwords for server access

---

## 📊 **Monitoring & Maintenance**

### **Log Monitoring**
```bash
# Application logs
tail -f /home/template/template/logs/app_errors.log
tail -f /home/template/template/logs/flask_info.log

# System service logs
sudo journalctl -u template -f
```

### **Health Checks**
```bash
# Simple health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
if [ $response = "200" ]; then
    echo "Application is healthy"
else
    echo "Application health check failed: $response"
    sudo systemctl restart template
fi
```

### **Database Backup**
```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/template/template/data/template.db /home/template/backups/template_$DATE.db
find /home/template/backups -name "template_*.db" -mtime +7 -delete
```

### **Performance Monitoring**
```bash
# Monitor application performance
htop
iotop
netstat -tuln | grep :5000

# Check disk usage
df -h
du -sh /home/template/template/data/
```

---

## 🔄 **Updates & Rollbacks**

### **Update Process**
```bash
# 1. Backup current version
cp -r /home/template/template /home/template/template_backup_$(date +%Y%m%d)

# 2. Pull latest changes
cd /home/template/template
git pull origin main

# 3. Update dependencies
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. Restart service
sudo systemctl restart template

# 5. Verify deployment
curl http://localhost:5000/
```

### **Rollback Process**
```bash
# If update fails, rollback
sudo systemctl stop template
rm -rf /home/template/template
mv /home/template/template_backup_YYYYMMDD /home/template/template
sudo systemctl start template
```

---

## 📞 **Support & Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Find process using port
sudo lsof -i :5000
sudo kill -9 <PID>
```

#### **Permission Denied**
```bash
# Fix permissions
sudo chown -R template:template /home/template/template
chmod 755 /home/template/template
```

#### **Database Locked**
```bash
# Check for processes using database
sudo lsof /home/template/template/data/template.db
```

### **Getting Help**
- 📖 **Documentation**: Check README.md and API docs
- 🐛 **Issues**: [GitHub Issues](https://github.com/An0naman/template/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/An0naman/template/discussions)

---

**Happy Deploying! 🚀**
