# ntfy Push Notifications Setup Guide

This guide will help you set up ntfy push notifications to receive alerts from your app on your iPhone.

## What is ntfy?

ntfy is a simple HTTP-based pub-sub notification service. It allows you to send notifications to your devices via simple HTTP PUT/POST requests. It's free, open-source, and works great for personal projects.

## Quick Setup

### 1. Download the ntfy App

- **iPhone**: Download from the [App Store](https://apps.apple.com/app/ntfy/id1625396347)
- **Android**: Download from [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy) or [F-Droid](https://f-droid.org/en/packages/io.heckel.ntfy/)

### 2. Configure Your App

1. Go to your app's settings: **Settings → Push Notifications**
2. Choose a unique topic name (e.g., `my-app-notifications-xyz123`)
3. Optionally set an authentication token for private notifications
4. Save the configuration

### 3. Subscribe in the ntfy App

1. Open the ntfy app on your device
2. Tap the "+" button to add a new subscription
3. Enter your topic name from step 2
4. If using a custom server, change the server URL
5. Tap "Subscribe"

### 4. Test Your Setup

1. In your app's Push Notifications settings, click "Send Test Notification"
2. You should receive a notification on your device within seconds

## Server Options

### Public Server (Default)
- Uses `https://ntfy.sh` (free, public server)
- No registration required
- Choose a unique topic name to avoid conflicts
- Suitable for most personal use cases

### Self-Hosted Server
- Host your own ntfy server for maximum privacy
- See [ntfy.sh documentation](https://docs.ntfy.sh/install/) for setup instructions
- Change the server URL in your app configuration

## Security Considerations

### Topic Names
- Choose unique, hard-to-guess topic names
- Avoid including personal information in topic names
- Consider using random strings (e.g., `myapp-d8f7a9b2-4e1c-9f6a`)

### Authentication
- Use authentication tokens for sensitive applications
- Set up access control on your own server if needed
- The public ntfy.sh server supports authentication for paid plans

## Notification Features

Your app automatically includes:
- **Emoji tags** based on notification type (📝 for notes, 📊 for sensors, etc.)
- **Priority levels** (low, medium, high, critical)
- **Click actions** to open related entries in your app
- **Rich formatting** with titles and detailed messages

## Troubleshooting

### Not Receiving Notifications?
1. Check that your topic name is configured correctly
2. Verify your device has internet connectivity
3. Ensure notifications are enabled for the ntfy app in your device settings
4. Try sending a test notification from the app

### Notifications Delayed?
- The public ntfy.sh server may have occasional delays during high traffic
- Consider using your own server for guaranteed delivery times
- Check your device's battery optimization settings

### Topic Conflicts?
- If you suspect someone else is using your topic, choose a more unique name
- Consider adding random characters or UUIDs to your topic name

## Advanced Configuration

### Custom Actions
The app can send notifications with action buttons that:
- Open specific entries in your app
- Trigger API endpoints
- Open external URLs

### Message Formatting
- Supports emoji in titles and messages
- Long messages are automatically truncated with "..." 
- Links in messages become clickable

### Rate Limiting
- The public server has rate limits to prevent abuse
- Your app respects these limits automatically
- Self-hosted servers can have custom rate limits

## Privacy

### Data Handled by ntfy
- Notification titles and messages
- Your chosen topic name
- Timestamp of notifications
- No personal information is required for basic usage

### Data Retention
- Public server retains messages for 12 hours by default
- Self-hosted servers can configure custom retention
- No message content is logged or stored permanently

For more detailed information, visit the [official ntfy documentation](https://docs.ntfy.sh/).
