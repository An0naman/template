# 📋 Template - Flask Content Management System

A sophisticated Flask-based content management system with dynamic theming, relationship management, IoT sensor integration, and comprehensive API capabilities. **Designed to be used as a framework** for creating multiple independent applications.

## 🌟 **Features**

### **Core Functionality**
- 📊 **Dynamic Entry Management**: Flexible content types with configurable fields
- 🔗 **Advanced Relationships**: Complex many-to-many relationships with metadata
- 📝 **Rich Note System**: File attachments, reminders, and notifications
- 🏷️ **Label Printing**: QR codes, thermal printers (Niimbot B1/D110), A4 sheets
- 🔔 **Notification System**: Priority-based alerts with scheduling and ntfy integration
- 📡 **IoT Sensor Integration**: Real-time data collection from ESP32/network devices

### **User Experience**
- 🎨 **Dynamic Theme System**: Multiple color schemes with dark mode support
- 📱 **Responsive Design**: Mobile-friendly interface with Bootstrap 5.3.3
- ♿ **Accessibility Features**: High contrast mode and typography options
- 🔍 **Advanced Filtering**: Multi-dimensional search and filtering
- 📊 **Dashboards**: Customizable widgets and data visualization

### **Technical Excellence**
- 🏗️ **Modular Architecture**: Blueprint-based Flask application
- 🔌 **Comprehensive REST API**: 10+ specialized API endpoints
- 🐳 **Docker Support**: Production-ready containerization
- 📊 **Database Management**: SQLite with all config in SQL (framework-ready)
- 🔄 **Framework Design**: Reusable across multiple independent applications

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.12 or higher
- Docker (optional, for containerized deployment)

### **Installation**

#### **Option 1: Local Development**
```bash
# Clone the repository
git clone https://github.com/An0naman/template.git
cd template

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database and run
python run.py
```

#### **Option 2: Docker Deployment**
```bash
# Clone the repository
git clone https://github.com/An0naman/template.git
cd template

# Build and run with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:5000
```

### **First Setup**
1. **Access the application** at `http://localhost:5000`
2. **Configure entry types** via Settings → Data Structure → Entry Types
3. **Set up themes** via Settings → System Configuration → System Theme
4. **Configure notifications** via Settings → Overdue Notification Settings

---

## 📁 **Project Structure**

```
template/
├── app/                         # Core application package
│   ├── __init__.py             # Application factory
│   ├── config.py               # Configuration management
│   ├── db.py                   # Database utilities
│   ├── api/                    # REST API modules (10+ endpoints)
│   ├── routes/                 # Flask route handlers
│   ├── services/               # Business logic layer
│   ├── templates/              # Jinja2 HTML templates
│   └── static/                 # CSS, JS, and uploads
├── data/                       # Database & uploaded files
├── docs/                       # 📚 Documentation
│   ├── setup/                  # Installation & deployment guides
│   ├── features/               # Feature-specific documentation
│   ├── guides/                 # User & API guides
│   ├── development/            # Technical documentation
│   └── framework/              # Framework usage guide
├── logs/                       # Application logs
├── archive/                    # Archived docs (reference only)
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Container definition
└── run.py                     # Application entry point
```

---

## 📚 **Documentation**

### **Setup & Installation**
- **[Installation Guide](docs/setup/INSTALLATION.md)** - Getting started
- **[CasaOS Setup](docs/setup/CASAOS_SETUP.md)** - CasaOS deployment
- **[Deployment Guide](docs/setup/DEPLOYMENT.md)** - Production deployment

### **Features**
- **[Label Printing](docs/features/LABEL_PRINTING.md)** - Complete printing system guide
- **[Niimbot Printers](docs/features/NIIMBOT.md)** - Bluetooth thermal printers
- **[AI Chatbot](docs/features/AI_CHATBOT_FEATURE.md)** - AI-powered assistance
- **[Sensors & IoT](docs/features/SENSORS.md)** - Device integration
- **[Notifications](docs/features/NOTIFICATIONS.md)** - Alert system
- **[Dashboards](docs/features/DASHBOARDS.md)** - Custom dashboards

### **Framework Usage**
- **[Framework Guide](docs/framework/FRAMEWORK_USAGE.md)** - ⭐ Use as a multi-app framework
- **[Architecture](docs/development/ARCHITECTURE.md)** - System design
- **[API Reference](docs/guides/API_REFERENCE.md)** - Complete API docs

### **Security & Guides**
- **[Security Guide](docs/guides/SECURITY_IMPLEMENTATION.md)** - Security best practices
- **[Testing Guide](docs/guides/SECURITY_TESTING_GUIDE.md)** - Security testing

---

## 🚀 **Using as a Framework**

This project is designed to be used as a **framework for multiple independent applications**:

```bash
# 1. Publish framework image
docker build -t ghcr.io/yourusername/template:latest .
docker push ghcr.io/yourusername/template:latest

# 2. Create app instance (e.g., homebrews)
mkdir ~/apps/homebrews && cd ~/apps/homebrews
cat > docker-compose.yml << EOF
services:
  app:
    image: ghcr.io/yourusername/template:latest
    ports: ["5001:5001"]
    volumes: ["./data:/app/data"]
EOF

# 3. Start and configure via UI
docker-compose up -d
# Visit http://localhost:5001 and configure project name, entry types, etc.
```

**See [Framework Usage Guide](docs/framework/FRAMEWORK_USAGE.md) for complete details.**

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Application Settings
FLASK_APP=app.py
FLASK_ENV=development  # or production

# Database Configuration
DATABASE_PATH=data/template.db

# Security (IMPORTANT: Change for production)
SECRET_KEY=your_super_secret_key_here
```

### **Database Schema**
The application uses SQLite with the following main tables:
- `entries` - Core content items
- `entry_types` - Configurable content types
- `relationships` - Many-to-many relationships
- `notes` - Rich notes with attachments
- `sensors` - IoT sensor data
- `notifications` - Alert system
- `system_params` - Application settings

---

## 🎨 **Theme System**

### **Available Themes**
- **Default Blue**: Classic Bootstrap-inspired theme
- **Emerald Green**: Nature-inspired green palette  
- **Purple**: Modern purple/violet scheme
- **Amber**: Warm golden amber theme

### **Features**
- 🌙 **Dark Mode**: Toggle between light and dark themes
- 📝 **Typography**: Adjustable font sizes (14px - 20px)
- ♿ **High Contrast**: Enhanced visibility mode
- 🎯 **Live Preview**: Real-time theme changes

### **API Usage**
```bash
# Get current theme settings
curl http://localhost:5000/api/theme_settings

# Update theme
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{"theme": "purple", "dark_mode": true}'
```

---

## 🔔 **Notification System**

### **Overdue Date Monitoring**
Automatically creates notifications for entries with past due dates:
- **Smart Filtering**: Only active entries with enabled end dates
- **Configurable Scheduling**: Multiple cron expression options
- **High Priority**: Overdue notifications marked as high priority
- **Detailed Messages**: Shows days overdue

### **Configuration Options**
| Schedule | Description | Cron Expression |
|----------|-------------|-----------------|
| Daily 9 AM | Recommended | `0 9 * * *` |
| Every 6 hours | Frequent | `0 */6 * * *` |
| Weekdays only | Business days | `0 8 * * 1-5` |

---

## 🛠️ **Development**

### **API Endpoints**

Complete API documentation: **[API Reference](docs/guides/API_REFERENCE.md)**

#### **Quick Reference**
- `GET/POST /api/entries` - Entry management
- `GET/POST /api/entry_types` - Entry type configuration
- `GET/POST /api/theme_settings` - Theme customization
- `POST /api/labels/print_niimbot` - Print to Bluetooth printers
- `GET /api/sensors/data` - Sensor data retrieval
- `POST /api/notifications` - Create notifications

### **Testing**
```bash
# Run feature tests
python test_notifications.py
python test_file_upload.py
python test_security.py
```

### **Database Management**
```bash
# Initialize database
python run.py  # Auto-initializes on first run

# Backup database
cp data/template.db data/template.db.backup
```

---

## 🐳 **Docker Deployment**

### **Docker Compose**
```yaml
services:
  template:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - template_db_data:/app/data
    environment:
      - FLASK_APP=app.py

volumes:
  template_db_data:
```

### **CasaOS Integration**
The application includes CasaOS metadata for easy deployment:
- **Auto-discovery**: Detected by CasaOS Dev Manager
- **Volume Management**: Persistent data storage
- **Port Configuration**: Flexible port mapping
- **Health Monitoring**: Built-in status checking

---

## 📚 **Additional Resources**

- **[CHANGELOG](CHANGELOG.md)** - Version history and release notes
- **[CONTRIBUTING](CONTRIBUTING.md)** - Contribution guidelines
- **[Archived Docs](archive/)** - Historical implementation notes (reference)

---

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines.

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 **Links**

- **Repository**: [github.com/An0naman/template](https://github.com/An0naman/template)
- **Issues**: [Report bugs or request features](https://github.com/An0naman/template/issues)
- **Discussions**: [Community discussions](https://github.com/An0naman/template/discussions)

---

## 🙏 **Acknowledgments**

- **Flask** - The web framework that powers this application
- **Bootstrap 5.3.3** - Modern, responsive UI framework
- **Font Awesome** - Beautiful icon library
- **SQLite** - Reliable embedded database
- **Docker** - Containerization platform

---

**Built with ❤️ by [An0naman](https://github.com/An0naman)**