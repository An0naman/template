# Documentation Index

## 📚 Overview

This directory contains all technical documentation for the Template Application Framework.

## 🎯 Quick Navigation

### Getting Started
- **[Quick Start Guide](guides/QUICK_START.md)** - Complete walkthrough for using Sensor Master Control
- **[Quick Reference](guides/QUICK_REFERENCE.md)** - Quick reference card with common commands

### Core Systems

#### Sensor Master Control
- **[Sensor Master Control](SENSOR_MASTER_CONTROL.md)** - Complete reference documentation
- **[Dynamic Script Updates](api/DYNAMIC_SCRIPT_UPDATES.md)** - Real-time script updates over WiFi
- **[JSON Script Commands](api/JSON_SCRIPT_COMMANDS.md)** - Command reference for ESP32 scripts

#### ESP32 Integration
- **[ESP32 Code Export Guide](guides/ESP32_CODE_EXPORT.md)** - Comprehensive code generation guide
- **[ESP32 Code Export Quick](guides/ESP32_CODE_EXPORT_QUICK.md)** - Quick implementation reference
- **[ESP32 Detection Requirements](guides/ESP32_DETECTION_REQUIREMENTS.md)** - Hardware detection setup

### Framework

#### Setup & Deployment
- **[Quick Start](framework/QUICK_START.md)** - Framework quick start guide
- **[Deployment Guide](framework/DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[Update Guide](framework/UPDATE_GUIDE.md)** - Updating existing instances

#### Auto-Update System
- **[Auto Update](framework/AUTO_UPDATE.md)** - Complete auto-update system documentation
- **[Auto Update Quick Reference](framework/AUTO_UPDATE_QUICK_REF.md)** - Quick reference

### Database
- **[Migrations](MIGRATIONS.md)** - Database migration system guide
- **[Migrations Quick Reference](MIGRATIONS_QUICK_REF.md)** - Quick reference for migrations

### Security
- **[Security Implementation](guides/SECURITY_IMPLEMENTATION.md)** - Security features
- **[Security Testing Guide](guides/SECURITY_TESTING_GUIDE.md)** - Testing security features

## 📂 Directory Structure

```
docs/
├── README.md (this file)
├── SENSOR_MASTER_CONTROL.md        # Main sensor control reference
├── MIGRATIONS.md                   # Database migrations
│
├── api/                            # API & Technical References
│   ├── DYNAMIC_SCRIPT_UPDATES.md
│   └── JSON_SCRIPT_COMMANDS.md
│
├── guides/                         # User Guides & Tutorials
│   ├── QUICK_START.md              # Sensor Master Control quick start
│   ├── QUICK_REFERENCE.md          # Quick reference card
│   ├── ESP32_CODE_EXPORT.md
│   ├── ESP32_CODE_EXPORT_QUICK.md
│   ├── ESP32_DETECTION_REQUIREMENTS.md
│   ├── SECURITY_IMPLEMENTATION.md
│   └── SECURITY_TESTING_GUIDE.md
│
├── framework/                      # Framework Documentation
│   ├── QUICK_START.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── UPDATE_GUIDE.md
│   ├── AUTO_UPDATE.md
│   └── FRAMEWORK_USAGE.md
│
├── development/                    # Development Notes
├── bug-fixes/                      # Bug Fix Documentation
├── features/                       # Active Features
└── features-archive/               # Historical Documentation
```

## 🔍 Finding What You Need

### I want to...

- **Set up sensor control** → [Quick Start Guide](guides/QUICK_START.md)
- **Export ESP32 code** → [ESP32 Code Export Quick](guides/ESP32_CODE_EXPORT_QUICK.md)
- **Update scripts dynamically** → [Dynamic Script Updates](api/DYNAMIC_SCRIPT_UPDATES.md)
- **Understand JSON commands** → [JSON Script Commands](api/JSON_SCRIPT_COMMANDS.md)
- **Deploy to production** → [Deployment Guide](framework/DEPLOYMENT_GUIDE.md)
- **Set up auto-updates** → [Auto Update Quick Reference](framework/AUTO_UPDATE_QUICK_REF.md)
- **Run migrations** → [Migrations Quick Reference](MIGRATIONS_QUICK_REF.md)

## 📝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) in the root directory for contribution guidelines.
