# 🔌 API Documentation

This document provides comprehensive information about the Template Flask application's REST API endpoints.

## 📋 **Table of Contents**

- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
- [Entry Management](#entry-management)
- [Relationship System](#relationship-system)
- [Note System](#note-system)
- [Theme System](#theme-system)
- [Notification System](#notification-system)
- [Sensor Integration](#sensor-integration)
- [Label Generation](#label-generation)
- [System Parameters](#system-parameters)
- [Error Handling](#error-handling)

---

## 🔐 **Authentication**

Currently, the API does not require authentication. All endpoints are publicly accessible.

**Base URL**: `http://localhost:5000/api`

---

## 🏠 **Core Endpoints**

### **Health Check**
```http
GET /api/health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-08-03T10:30:00Z",
    "version": "1.0.0"
}
```

---

## 📊 **Entry Management**

### **List All Entries**
```http
GET /api/entries
```

**Query Parameters:**
- `entry_type_id` (optional) - Filter by entry type
- `search` (optional) - Search in entry names and descriptions
- `active_only` (optional) - Show only active entries (true/false)

**Response:**
```json
{
    "entries": [
        {
            "id": 1,
            "name": "Sample Entry",
            "description": "This is a sample entry",
            "entry_type_id": 1,
            "entry_type_name": "Book",
            "is_active": true,
            "created_at": "2025-08-03T10:00:00Z",
            "updated_at": "2025-08-03T10:00:00Z"
        }
    ],
    "total": 1
}
```

### **Get Single Entry**
```http
GET /api/entries/{id}
```

**Response:**
```json
{
    "id": 1,
    "name": "Sample Entry",
    "description": "This is a sample entry",
    "entry_type_id": 1,
    "entry_type_name": "Book",
    "is_active": true,
    "custom_fields": {
        "author": "John Doe",
        "isbn": "978-0123456789"
    },
    "relationships": [
        {
            "id": 1,
            "related_entry_id": 2,
            "related_entry_name": "Related Entry",
            "relationship_type": "authored_by"
        }
    ],
    "notes": [
        {
            "id": 1,
            "title": "Reading Notes",
            "content": "Excellent book...",
            "created_at": "2025-08-03T10:00:00Z"
        }
    ]
}
```

### **Create Entry**
```http
POST /api/entries
```

**Request Body:**
```json
{
    "name": "New Entry",
    "description": "Entry description",
    "entry_type_id": 1,
    "custom_fields": {
        "author": "Jane Doe",
        "isbn": "978-9876543210"
    }
}
```

**Response:**
```json
{
    "message": "Entry created successfully",
    "entry_id": 2
}
```

### **Update Entry**
```http
PUT /api/entries/{id}
```

**Request Body:**
```json
{
    "name": "Updated Entry Name",
    "description": "Updated description",
    "is_active": false
}
```

**Response:**
```json
{
    "message": "Entry updated successfully"
}
```

### **Delete Entry**
```http
DELETE /api/entries/{id}
```

**Response:**
```json
{
    "message": "Entry deleted successfully"
}
```

---

## 🏷️ **Entry Types**

### **List Entry Types**
```http
GET /api/entry_types
```

**Response:**
```json
{
    "entry_types": [
        {
            "id": 1,
            "name": "Book",
            "description": "Book entries",
            "custom_fields": [
                {
                    "name": "author",
                    "type": "text",
                    "required": true
                },
                {
                    "name": "isbn",
                    "type": "text",
                    "required": false
                }
            ],
            "show_end_dates": true,
            "is_active": true
        }
    ]
}
```

### **Create Entry Type**
```http
POST /api/entry_types
```

**Request Body:**
```json
{
    "name": "Movie",
    "description": "Movie entries",
    "custom_fields": [
        {
            "name": "director",
            "type": "text",
            "required": true
        },
        {
            "name": "release_year",
            "type": "number",
            "required": false
        }
    ],
    "show_end_dates": false
}
```

---

## 🔗 **Relationship System**

### **List Relationships**
```http
GET /api/relationships
```

**Query Parameters:**
- `entry_id` (optional) - Get relationships for specific entry

**Response:**
```json
{
    "relationships": [
        {
            "id": 1,
            "entry_id": 1,
            "related_entry_id": 2,
            "relationship_type": "authored_by",
            "metadata": {
                "start_date": "2020-01-01",
                "confidence": "high"
            }
        }
    ]
}
```

### **Create Relationship**
```http
POST /api/relationships
```

**Request Body:**
```json
{
    "entry_id": 1,
    "related_entry_id": 2,
    "relationship_type": "authored_by",
    "metadata": {
        "start_date": "2020-01-01"
    }
}
```

---

## 📝 **Note System**

### **List Notes**
```http
GET /api/notes
```

**Query Parameters:**
- `entry_id` (required) - Get notes for specific entry

**Response:**
```json
{
    "notes": [
        {
            "id": 1,
            "entry_id": 1,
            "note_title": "Reading Notes",
            "note_text": "This book is excellent...",
            "note_type": "general",
            "created_at": "2025-08-03T10:00:00Z",
            "file_paths": ["uploads/note_1_screenshot.png"],
            "associated_entry_ids": [2, 3],
            "url_bookmarks": [
                {
                    "url": "https://example.com/book-review",
                    "friendly_name": "Book Review Article"
                },
                {
                    "url": "https://author-website.com",
                    "friendly_name": "Author's Website"
                }
            ],
            "reminder": {
                "notification_id": 5,
                "scheduled_for": "2025-09-01T10:00:00Z",
                "is_read": false,
                "is_dismissed": false,
                "title": "Reminder: Reading Notes"
            },
            "relationship_type": "primary"
        }
    ]
}
```

### **Create Note**
```http
POST /api/entries/{entry_id}/notes
```

**Request Body (JSON):**
```json
{
    "note_title": "Research Notes",
    "note_text": "Important research findings",
    "note_type": "general",
    "associated_entry_ids": [2, 3],
    "url_bookmarks": [
        {
            "url": "https://example.com/research",
            "friendly_name": "Research Article"
        },
        {
            "url": "https://github.com/user/repo",
            "friendly_name": "Code Repository"
        }
    ],
    "reminder_date": "2025-09-01T10:00:00"
}
```

**Request Body (multipart/form-data):**
- `note_title` - Note title
- `note_text` - Note content  
- `note_type` - Note type (general, important, warning, etc.)
- `associated_entry_ids` - JSON array of related entry IDs
- `url_bookmarks` - JSON array of bookmark objects with url and friendly_name
- `files` - File attachments (optional)
- `reminder_date` - ISO datetime for reminder (optional)

**Response:**
```json
{
    "message": "Note added successfully",
    "note_id": 1,
    "file_paths": ["uploads/note_1_document.pdf"],
    "files_uploaded": 1
}
```

### **Update Note**
```http
PUT /api/notes/{note_id}
```

**Request Body (form-data):**
- `note_title` - Updated note title
- `note_text` - Updated note content
- `associated_entry_ids` - JSON array of related entry IDs
- `url_bookmarks` - JSON array of bookmark objects

**Response:**
```json
{
    "message": "Note updated successfully",
    "note_title": "Updated Research Notes",
    "note_text": "Updated content",
    "associated_entry_ids": [2, 3],
    "url_bookmarks": [
        {
            "url": "https://updated-example.com",
            "friendly_name": "Updated Research Link"
        }
    ]
}
```

---

## 🎨 **Theme System**

### **Get Theme Settings**
```http
GET /api/theme_settings
```

**Response:**
```json
{
    "theme_color_scheme": "default",
    "theme_dark_mode": false,
    "theme_font_size": "normal",
    "theme_high_contrast": false
}
```

### **Update Theme Settings**
```http
POST /api/theme_settings
```

**Request Body:**
```json
{
    "theme_color_scheme": "purple",
    "theme_dark_mode": true,
    "theme_font_size": "large",
    "theme_high_contrast": false
}
```

**Response:**
```json
{
    "success": true,
    "message": "Theme settings saved successfully"
}
```

**Available Options:**
- **Color Schemes**: `default`, `emerald`, `purple`, `amber`
- **Font Sizes**: `small`, `normal`, `large`, `extra-large`
- **Dark Mode**: `true`, `false`
- **High Contrast**: `true`, `false`

---

## 🔔 **Notification System**

### **List Notifications**
```http
GET /api/notifications
```

**Query Parameters:**
- `priority` (optional) - Filter by priority (low, normal, high)
- `read` (optional) - Filter by read status (true/false)

**Response:**
```json
{
    "notifications": [
        {
            "id": 1,
            "title": "Overdue Entry",
            "message": "Entry 'Sample Book' is 5 days overdue",
            "priority": "high",
            "is_read": false,
            "created_at": "2025-08-03T10:00:00Z"
        }
    ]
}
```

### **Mark Notification as Read**
```http
PUT /api/notifications/{id}/read
```

**Response:**
```json
{
    "message": "Notification marked as read"
}
```

### **Check Overdue Entries**
```http
POST /api/check_overdue_end_dates
```

**Response:**
```json
{
    "message": "Overdue check completed",
    "notifications_created": 3
}
```

---

## 📡 **Sensor Integration**

### **List Sensors**
```http
GET /api/sensors
```

**Response:**
```json
{
    "sensors": [
        {
            "id": 1,
            "entry_id": 1,
            "sensor_type": "temperature",
            "value": 23.5,
            "unit": "°C",
            "timestamp": "2025-08-03T10:00:00Z"
        }
    ]
}
```

### **Add Sensor Data**
```http
POST /api/sensors
```

**Request Body:**
```json
{
    "entry_id": 1,
    "sensor_type": "temperature",
    "value": 24.0,
    "unit": "°C"
}
```

---

## 🏷️ **Label Generation**

### **Generate QR Code**
```http
POST /api/labels/qr
```

**Request Body:**
```json
{
    "entry_id": 1,
    "format": "png",
    "size": "medium"
}
```

**Response:**
```json
{
    "qr_code_url": "/static/qr_codes/entry_1_qr.png",
    "message": "QR code generated successfully"
}
```

### **Generate PDF Label**
```http
POST /api/labels/pdf
```

**Request Body:**
```json
{
    "entry_id": 1,
    "template": "standard",
    "include_qr": true
}
```

**Response:**
```json
{
    "pdf_url": "/static/labels/entry_1_label.pdf",
    "message": "PDF label generated successfully"
}
```

---

## ⚙️ **System Parameters**

### **Get System Parameters**
```http
GET /api/system_params
```

**Response:**
```json
{
    "project_name": "My Template Project",
    "entry_label": "Entry",
    "entry_plural_label": "Entries",
    "overdue_check_enabled": true,
    "overdue_check_schedule": "0 9 * * *"
}
```

### **Update System Parameter**
```http
PUT /api/system_params/{param_name}
```

**Request Body:**
```json
{
    "value": "New Project Name"
}
```

---

## ❌ **Error Handling**

### **Standard Error Response**
```json
{
    "error": "Error description",
    "code": "ERROR_CODE",
    "timestamp": "2025-08-03T10:00:00Z"
}
```

### **HTTP Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `409` - Conflict (e.g., duplicate entry)
- `500` - Internal Server Error

### **Common Error Codes**
- `VALIDATION_ERROR` - Invalid request data
- `NOT_FOUND` - Resource not found
- `DUPLICATE_ENTRY` - Attempt to create duplicate
- `INTEGRITY_ERROR` - Database constraint violation
- `FILE_TOO_LARGE` - File upload exceeds size limit

---

## 📊 **Rate Limiting**

Currently, no rate limiting is implemented. All endpoints can be called without restrictions.

## 🔄 **Pagination**

For endpoints that return lists, pagination is handled via query parameters:
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 50, max: 100)

---

## 🧪 **Testing the API**

### **Using cURL**
```bash
# Get all entries
curl http://localhost:5000/api/entries

# Create new entry
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Entry", "entry_type_id": 1}'

# Update theme
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{"theme_color_scheme": "purple", "theme_dark_mode": true}'
```

### **Using Python**
```python
import requests

# Get entries
response = requests.get('http://localhost:5000/api/entries')
entries = response.json()

# Create entry
data = {"name": "New Entry", "entry_type_id": 1}
response = requests.post('http://localhost:5000/api/entries', json=data)
```

---

**For more examples and advanced usage, see the test files in the project directory.**
