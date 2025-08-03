# 📋 Template - Flask Content Management System

A sophisticated Flask-based content management system with dynamic theming, relationship management, IoT sensor integration, and comprehensive API capabilities.

## 🌟 **Features**

### **Core Functionality**
- 📊 **Dynamic Entry Management**: Flexible content types with configurable fields
- 🔗 **Advanced Relationships**: Complex many-to-many relationships with metadata
- 📝 **Rich Note System**: File attachments, reminders, and notifications
- 🏷️ **Label Generation**: QR codes and professional PDF printing
- 🔔 **Notification System**: Priority-based alerts with scheduling
- 📡 **IoT Sensor Integration**: Real-time data collection and monitoring

### **User Experience**
- 🎨 **Dynamic Theme System**: Multiple color schemes with dark mode support
- 📱 **Responsive Design**: Mobile-friendly interface with Bootstrap 5.3.3
- ♿ **Accessibility Features**: High contrast mode and typography options
- 🔍 **Advanced Filtering**: Multi-dimensional search and filtering

### **Technical Excellence**
- 🏗️ **Modular Architecture**: Blueprint-based Flask application
- 🔌 **Comprehensive REST API**: 10+ specialized API endpoints
- 🐳 **Docker Support**: Production-ready containerization
- 📊 **Database Management**: SQLite with complex schema and migrations

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
│   ├── api/                    # REST API modules
│   │   ├── entry_api.py        # Entry management
│   │   ├── theme_api.py        # Theme system
│   │   ├── notifications_api.py # Notification system
│   │   └── [8+ more APIs]      # Specialized endpoints
│   ├── routes/                 # Flask route handlers
│   │   ├── main_routes.py      # Core application routes
│   │   └── maintenance_routes.py # Management interface
│   ├── templates/              # Jinja2 HTML templates
│   └── static/                 # CSS, JS, and uploads
├── data/                       # Database storage
├── logs/                       # Application logs
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Container definition
└── run.py                     # Application entry point
```

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

#### **Core Endpoints**
- `GET /api/entries` - List all entries
- `POST /api/entries` - Create new entry
- `GET /api/entry_types` - Get entry types
- `GET /api/theme_settings` - Current theme
- `POST /api/theme_settings` - Update theme

#### **Specialized APIs**
- **Relationships**: `/api/relationships`
- **Notes**: `/api/notes`
- **Sensors**: `/api/sensors`
- **Labels**: `/api/labels`
- **Notifications**: `/api/notifications`

### **Testing**
```bash
# Run development tests
python test_new_features.py
python test_notifications.py
python test_attachment_indicator.py

# Test specific features
python test_theme.py
```

### **Database Management**
```bash
# Initialize database
python -c "from app.db import init_db; init_db()"

# Create test data
python create_test_overdue_entry.py

# Check overdue entries
python check_overdue_dates.py
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

## 📚 **Documentation**

- 📖 **[Theme Documentation](THEME_DOCUMENTATION.md)** - Comprehensive theming guide
- 🔔 **[Overdue Notifications](OVERDUE_NOTIFICATIONS.md)** - Notification system setup
- 🏗️ **[API Reference](#)** - Complete API documentation
- 🐳 **[Docker Guide](#)** - Deployment instructions

---

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

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