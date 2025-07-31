// Notification Component JavaScript
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.isVisible = false; // Start collapsed
        this.autoOpened = false; // Track if notifications were auto-opened
        this.hasUserDismissed = false; // Track if user has manually dismissed
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

        // Add touch/swipe support for mobile
        this.setupTouchSupport();
        
        // Handle window resize for mobile responsiveness
        window.addEventListener('resize', () => this.handleResize());
    }

    setupTouchSupport() {
        let startY = 0;
        let currentY = 0;
        let isDragging = false;

        document.addEventListener('touchstart', (e) => {
            const container = document.getElementById('notification-container');
            if (container && container.style.display !== 'none' && this.isVisible) {
                startY = e.touches[0].clientY;
                isDragging = true;
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            currentY = e.touches[0].clientY;
            const deltaY = startY - currentY;
            
            // If swiping up significantly, close notifications
            if (deltaY > 50) {
                this.hideNotifications();
                isDragging = false;
            }
        });

        document.addEventListener('touchend', () => {
            isDragging = false;
        });
    }

    handleResize() {
        // Adjust notification container position on mobile orientation change
        const container = document.getElementById('notification-container');
        const indicator = document.getElementById('notification-indicator');
        
        if (window.innerWidth <= 480) {
            // Very small screens - make notifications fullscreen-like
            if (container && this.isVisible) {
                container.style.maxHeight = 'calc(100vh - 10px)';
            }
        }
    }

    createNotificationContainer() {
        // Create subtle notification indicator (only shows when there are notifications)
        const indicator = document.createElement('div');
        indicator.className = 'notification-indicator';
        indicator.id = 'notification-indicator';
        indicator.innerHTML = '<i class="fas fa-circle"></i>';
        indicator.addEventListener('click', () => this.toggleNotifications());
        indicator.title = 'You have notifications - Click to view (Ctrl+N)';
        indicator.style.display = 'none'; // Hidden by default
        document.body.appendChild(indicator);

        // Create notification container
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.id = 'notification-container';
        document.body.appendChild(container);

        // Add header with close button and dismiss all
        const header = document.createElement('div');
        header.className = 'notification-header-bar';
        header.innerHTML = `
            <div class="notification-title-bar">
                <h6><i class="fas fa-bell me-2"></i>Notifications</h6>
                <span class="notification-count-text" id="notification-count-text">0</span>
            </div>
            <div class="notification-controls">
                <button class="notification-control-btn dismiss-all-btn" title="Dismiss All">
                    <i class="fas fa-trash"></i>
                </button>
                <button class="notification-control-btn close-btn" title="Close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.appendChild(header);

        // Add event listeners for controls
        header.querySelector('.dismiss-all-btn').addEventListener('click', () => this.dismissAllNotifications());
        header.querySelector('.close-btn').addEventListener('click', () => this.hideNotifications());

        // Add notifications list container
        const notificationsList = document.createElement('div');
        notificationsList.className = 'notifications-list';
        notificationsList.id = 'notifications-list';
        container.appendChild(notificationsList);
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
            this.notifications = Array.isArray(data) ? data : (data.notifications || []);
            this.renderNotifications();
            this.updateBadgeCount();
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    renderNotifications() {
        const container = document.getElementById('notifications-list');
        
        // Clear existing notifications
        container.innerHTML = '';

        if (this.notifications.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'notification-empty-state';
            emptyState.innerHTML = `
                <div class="empty-state-content">
                    <i class="fas fa-inbox"></i>
                    <p>No notifications</p>
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
                <span class="notification-type ${notification.notification_type}">${notification.notification_type.replace('_', ' ')}</span>
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
                    `<button class="notification-btn btn-read" onclick="notificationManager.markAsRead(${notification.id})" aria-label="Mark as read">
                        <i class="fas fa-check"></i><span class="btn-text">Read</span>
                    </button>` : 
                    ''
                }
                <button class="notification-btn btn-dismiss" onclick="notificationManager.dismissNotification(${notification.id})" aria-label="Dismiss notification">
                    <i class="fas fa-times"></i><span class="btn-text">Dismiss</span>
                </button>
                ${notification.entry_id ? 
                    `<button class="notification-btn btn-view" onclick="notificationManager.viewEntry(${notification.entry_id})" aria-label="View related entry">
                        <i class="fas fa-external-link-alt"></i><span class="btn-text">View</span>
                    </button>` : 
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
        if (this.isVisible) {
            this.hideNotifications();
        } else {
            this.showNotifications();
        }
    }

    showNotifications() {
        const container = document.getElementById('notification-container');
        container.style.display = 'block';
        this.isVisible = true;
        
        // Mark as auto-opened if there are unread notifications
        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        if (unreadCount > 0) {
            this.autoOpened = true;
        }
    }

    hideNotifications() {
        const container = document.getElementById('notification-container');
        container.style.display = 'none';
        this.isVisible = false;
        this.hasUserDismissed = true; // Mark that user has dismissed
    }

    updateBadgeCount() {
        const indicator = document.getElementById('notification-indicator');
        const countText = document.getElementById('notification-count-text');
        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        // Update count text
        if (countText) {
            countText.textContent = this.notifications.length > 0 ? this.notifications.length : '0';
        }
        
        // Show/hide indicator based on unread notifications
        if (indicator) {
            if (unreadCount > 0) {
                indicator.style.display = 'flex';
                indicator.className = 'notification-indicator pulse'; // Add pulse animation for new notifications
            } else if (this.notifications.length > 0) {
                indicator.style.display = 'flex';
                indicator.className = 'notification-indicator'; // Remove pulse when all read
            } else {
                indicator.style.display = 'none';
            }
        }
        
        // Auto-show notifications if there are unread ones (but less aggressively)
        if (unreadCount > 0 && !this.isVisible && !this.hasUserDismissed) {
            // Only auto-show after a brief delay to be less intrusive
            setTimeout(() => {
                if (unreadCount > 0 && !this.isVisible) {
                    this.showNotifications();
                    this.autoOpened = true;
                }
            }, 2000);
        }
        // Auto-hide if all notifications are read and user hasn't manually opened them
        else if (unreadCount === 0 && this.isVisible && this.autoOpened) {
            setTimeout(() => {
                if (this.autoOpened && this.isVisible) {
                    this.hideNotifications();
                    this.autoOpened = false;
                }
            }, 3000);
        }
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
