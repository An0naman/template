// Notification Component JavaScript
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.isVisible = true;
        this.pollInterval = 30000; // Check for new notifications every 30 seconds
        this.init();
    }

    init() {
        this.createNotificationContainer();
        this.loadNotifications();
        this.startPolling();
        
        // Add keyboard shortcut (Ctrl+N) to toggle notifications
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                this.toggleNotifications();
            }
        });
    }

    createNotificationContainer() {
        // Create toggle button
        const toggle = document.createElement('button');
        toggle.className = 'notification-toggle';
        toggle.innerHTML = '<i class="fas fa-bell"></i><span class="badge" id="notification-count">0</span>';
        toggle.addEventListener('click', () => this.toggleNotifications());
        toggle.title = 'Toggle Notifications (Ctrl+N)';
        document.body.appendChild(toggle);

        // Create notification container
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.id = 'notification-container';
        document.body.appendChild(container);

        // Add dismiss all button
        const dismissAllBtn = document.createElement('button');
        dismissAllBtn.className = 'dismiss-all-btn';
        dismissAllBtn.textContent = 'Dismiss All';
        dismissAllBtn.addEventListener('click', () => this.dismissAllNotifications());
        container.appendChild(dismissAllBtn);
    }

    async loadNotifications() {
        try {
            const currentEntryId = this.getCurrentEntryId();
            const params = new URLSearchParams();
            if (currentEntryId) {
                params.append('entry_id', currentEntryId);
            }
            
            const response = await fetch(`/api/notifications?${params}`);
            if (!response.ok) throw new Error('Failed to load notifications');
            
            const data = await response.json();
            this.notifications = data.notifications || [];
            this.renderNotifications();
            this.updateBadgeCount();
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    renderNotifications() {
        const container = document.getElementById('notification-container');
        const dismissAllBtn = container.querySelector('.dismiss-all-btn');
        
        // Clear existing notifications but keep dismiss all button
        const notifications = container.querySelectorAll('.notification-item');
        notifications.forEach(n => n.remove());

        if (this.notifications.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'notification-item';
            emptyState.innerHTML = `
                <div class="notification-message" style="text-align: center; color: #6c757d;">
                    <i class="fas fa-inbox"></i><br>
                    No notifications
                </div>
            `;
            container.appendChild(emptyState);
            return;
        }

        this.notifications.forEach(notification => {
            const notificationEl = this.createNotificationElement(notification);
            container.appendChild(notificationEl);
        });
    }

    createNotificationElement(notification) {
        const el = document.createElement('div');
        el.className = `notification-item priority-${notification.priority}${notification.is_read ? ' read' : ''}`;
        el.dataset.notificationId = notification.id;

        const createdDate = new Date(notification.created_at).toLocaleDateString();
        const createdTime = new Date(notification.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        let scheduledInfo = '';
        if (notification.scheduled_for) {
            const scheduledDate = new Date(notification.scheduled_for);
            const now = new Date();
            if (scheduledDate > now) {
                scheduledInfo = `<div style="font-size: 10px; color: #fd7e14; margin-top: 4px;">
                    <i class="fas fa-clock"></i> Scheduled for ${scheduledDate.toLocaleDateString()} ${scheduledDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </div>`;
            }
        }

        el.innerHTML = `
            <div class="notification-header">
                <h6 class="notification-title">${this.escapeHtml(notification.title)}</h6>
                <span class="notification-type ${notification.type}">${notification.type.replace('_', ' ')}</span>
            </div>
            <div class="notification-message">${this.escapeHtml(notification.message)}</div>
            ${scheduledInfo}
            <div class="notification-meta">
                <span class="notification-entry">
                    ${notification.entry_title ? 
                        `<i class="fas fa-file-alt"></i> ${this.escapeHtml(notification.entry_title)}` : 
                        '<i class="fas fa-globe"></i> Global'
                    }
                </span>
                <span>${createdDate} ${createdTime}</span>
            </div>
            <div class="notification-actions">
                ${!notification.is_read ? 
                    '<button class="notification-btn btn-read" onclick="notificationManager.markAsRead(' + notification.id + ')">Mark Read</button>' : 
                    ''
                }
                <button class="notification-btn btn-dismiss" onclick="notificationManager.dismissNotification(' + notification.id + ')">Dismiss</button>
                ${notification.entry_id ? 
                    '<button class="notification-btn btn-view" onclick="notificationManager.viewEntry(' + notification.entry_id + ')">View Entry</button>' : 
                    ''
                }
            </div>
        `;

        // Add click to mark as read
        el.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-actions') && !notification.is_read) {
                this.markAsRead(notification.id);
            }
        });

        return el;
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Failed to mark notification as read');

            // Update local state
            const notification = this.notifications.find(n => n.id === notificationId);
            if (notification) {
                notification.is_read = true;
                this.renderNotifications();
                this.updateBadgeCount();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async dismissNotification(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to dismiss notification');

            // Remove from local state
            this.notifications = this.notifications.filter(n => n.id !== notificationId);
            this.renderNotifications();
            this.updateBadgeCount();
        } catch (error) {
            console.error('Error dismissing notification:', error);
        }
    }

    async dismissAllNotifications() {
        if (this.notifications.length === 0) return;

        if (!confirm('Are you sure you want to dismiss all notifications?')) return;

        try {
            const promises = this.notifications.map(n => 
                fetch(`/api/notifications/${n.id}`, { method: 'DELETE' })
            );
            
            await Promise.all(promises);
            this.notifications = [];
            this.renderNotifications();
            this.updateBadgeCount();
        } catch (error) {
            console.error('Error dismissing all notifications:', error);
        }
    }

    toggleNotifications() {
        const container = document.getElementById('notification-container');
        this.isVisible = !this.isVisible;
        
        if (this.isVisible) {
            container.classList.remove('hidden');
        } else {
            container.classList.add('hidden');
        }
    }

    updateBadgeCount() {
        const badge = document.getElementById('notification-count');
        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        badge.textContent = unreadCount;
        badge.style.display = unreadCount > 0 ? 'flex' : 'none';
    }

    startPolling() {
        setInterval(() => {
            this.loadNotifications();
        }, this.pollInterval);
    }

    getCurrentEntryId() {
        // Try to get entry ID from URL path
        const pathMatch = window.location.pathname.match(/\/entry\/(\d+)/);
        if (pathMatch) {
            return parseInt(pathMatch[1]);
        }
        
        // Try to get from a data attribute or global variable
        const entryElement = document.querySelector('[data-entry-id]');
        if (entryElement) {
            return parseInt(entryElement.dataset.entryId);
        }
        
        return null;
    }

    viewEntry(entryId) {
        window.location.href = `/entry/${entryId}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Method to create a new notification from frontend
    async createNotification(title, message, type = 'manual', priority = 'medium', entryId = null, scheduledFor = null) {
        try {
            const response = await fetch('/api/notifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    message,
                    type,
                    priority,
                    entry_id: entryId,
                    scheduled_for: scheduledFor
                })
            });

            if (!response.ok) throw new Error('Failed to create notification');

            // Reload notifications to show the new one
            await this.loadNotifications();
        } catch (error) {
            console.error('Error creating notification:', error);
        }
    }
}

// Initialize notification manager when DOM is loaded
let notificationManager;
document.addEventListener('DOMContentLoaded', () => {
    notificationManager = new NotificationManager();
});

// Helper function to show a quick notification
function showQuickNotification(title, message, type = 'manual', priority = 'medium') {
    if (notificationManager) {
        notificationManager.createNotification(title, message, type, priority);
    }
}
