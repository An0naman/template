# URL Bookmarks Feature

## Overview

The URL Bookmarks feature allows you to attach multiple URL links to notes with friendly, human-readable names. This is useful for saving reference links, documentation, or any web resources related to your notes.

## Database Schema

### New Column: `url_bookmarks`

- **Type**: TEXT (JSON array)
- **Default**: `'[]'` (empty array)
- **Format**: Array of objects with `url` and `friendly_name` properties

### Example Data Structure

```json
[
  {
    "url": "https://www.example.com",
    "friendly_name": "Example Website"
  },
  {
    "url": "https://github.com/user/repo",
    "friendly_name": "Project Repository"
  },
  {
    "url": "https://docs.python.org/3/",
    "friendly_name": "Python 3 Documentation"
  }
]
```

## API Usage

### Creating Notes with URL Bookmarks

**Endpoint**: `POST /api/entries/{entry_id}/notes`

**Request Body** (JSON):
```json
{
  "note_title": "Research Notes",
  "note_text": "Important findings from my research",
  "note_type": "General",
  "url_bookmarks": [
    {
      "url": "https://www.research-site.com/article",
      "friendly_name": "Main Research Article"
    },
    {
      "url": "https://github.com/researcher/data",
      "friendly_name": "Data Repository"
    }
  ]
}
```

**Request Body** (Form Data):
```
note_title=Research Notes
note_text=Important findings from my research
note_type=General
url_bookmarks=[{"url":"https://www.research-site.com/article","friendly_name":"Main Research Article"}]
```

### Updating Notes with URL Bookmarks

**Endpoint**: `PUT /api/notes/{note_id}`

**Request Body** (Form Data):
```
note_title=Updated Research Notes
note_text=Updated content
url_bookmarks=[{"url":"https://updated-link.com","friendly_name":"Updated Link"}]
```

### Retrieving Notes

**Endpoint**: `GET /api/entries/{entry_id}/notes`

**Response**:
```json
[
  {
    "id": 1,
    "entry_id": 1,
    "note_title": "Research Notes",
    "note_text": "Important findings from my research",
    "note_type": "General",
    "created_at": "2025-08-30T10:00:00",
    "file_paths": [],
    "associated_entry_ids": [],
    "url_bookmarks": [
      {
        "url": "https://www.research-site.com/article",
        "friendly_name": "Main Research Article"
      },
      {
        "url": "https://github.com/researcher/data",
        "friendly_name": "Data Repository"
      }
    ],
    "reminder": null
  }
]
```

## Migration

The system automatically migrates existing `urls` data to the new `url_bookmarks` format:

1. **Simple URLs**: Converted to bookmark objects with domain name as friendly name
2. **Existing bookmark objects**: Preserved as-is
3. **Invalid data**: Logged as warnings and skipped

### Migration Example

**Before** (old `urls` column):
```json
["https://www.example.com", "https://github.com/user/repo"]
```

**After** (new `url_bookmarks` column):
```json
[
  {
    "url": "https://www.example.com",
    "friendly_name": "www.example.com"
  },
  {
    "url": "https://github.com/user/repo",
    "friendly_name": "github.com"
  }
]
```

## Frontend Integration

### JavaScript Example

```javascript
// Creating a note with URL bookmarks
const noteData = {
    note_title: "My Research",
    note_text: "Important research findings",
    url_bookmarks: [
        {
            url: "https://example.com",
            friendly_name: "Example Site"
        }
    ]
};

fetch(`/api/entries/${entryId}/notes`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(noteData)
});

// Displaying URL bookmarks
function displayUrlBookmarks(urlBookmarks) {
    const container = document.getElementById('url-bookmarks');
    container.innerHTML = '';
    
    urlBookmarks.forEach(bookmark => {
        const link = document.createElement('a');
        link.href = bookmark.url;
        link.textContent = bookmark.friendly_name;
        link.target = '_blank';
        link.className = 'bookmark-link';
        container.appendChild(link);
    });
}
```

## Benefits

1. **Better Organization**: Friendly names make links easier to identify
2. **User Experience**: More readable than raw URLs
3. **Flexibility**: Support for any number of bookmarks per note
4. **Backward Compatibility**: Existing URLs are automatically migrated
5. **API Consistency**: Follows existing patterns for other note fields

## Validation

- URLs should be valid HTTP/HTTPS URLs
- Friendly names should be non-empty strings
- Maximum recommended: 20 bookmarks per note (for performance)
- Each bookmark object must have both `url` and `friendly_name` fields
