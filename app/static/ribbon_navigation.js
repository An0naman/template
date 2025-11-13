/**
 * Ribbon Navigation System
 * Handles navigation history tracking and back/forward functionality
 */

(function() {
    'use strict';
    
    const NAV_HISTORY_KEY = 'ribbon_nav_history';
    const NAV_POSITION_KEY = 'ribbon_nav_position';
    const MAX_HISTORY_SIZE = 50;
    
    // Navigation configuration
    const NAV_PAGES = {
        dashboard: {
            url: '/dashboard',
            title: 'Dashboard',
            icon: 'fa-chart-line'
        },
        entries: {
            url: '/entries',
            title: 'Entries',
            icon: 'fa-list'
        },
        settings: {
            url: '/maintenance',
            title: 'Settings',
            icon: 'fa-cog'
        }
    };
    
    class RibbonNavigation {
        constructor() {
            this.currentUrl = window.location.pathname;
            this.init();
        }
        
        init() {
            // Record current page visit
            this.recordPageVisit();
            
            // Update UI
            this.updateNavigationState();
            
            // Attach event listeners
            this.attachEventListeners();
        }
        
        getHistory() {
            try {
                const history = sessionStorage.getItem(NAV_HISTORY_KEY);
                return history ? JSON.parse(history) : [];
            } catch (e) {
                console.error('Error reading navigation history:', e);
                return [];
            }
        }
        
        setHistory(history) {
            try {
                // Limit history size
                const trimmedHistory = history.slice(-MAX_HISTORY_SIZE);
                sessionStorage.setItem(NAV_HISTORY_KEY, JSON.stringify(trimmedHistory));
            } catch (e) {
                console.error('Error saving navigation history:', e);
            }
        }
        
        getPosition() {
            try {
                const pos = sessionStorage.getItem(NAV_POSITION_KEY);
                return pos ? parseInt(pos, 10) : -1;
            } catch (e) {
                return -1;
            }
        }
        
        setPosition(position) {
            try {
                sessionStorage.setItem(NAV_POSITION_KEY, position.toString());
            } catch (e) {
                console.error('Error saving navigation position:', e);
            }
        }
        
        recordPageVisit() {
            const history = this.getHistory();
            const position = this.getPosition();
            
            const pageEntry = {
                url: this.currentUrl,
                title: document.title,
                timestamp: Date.now()
            };
            
            // If we're navigating forward (not using back button)
            if (position === -1 || position === history.length - 1) {
                // Don't add duplicate consecutive entries
                if (history.length === 0 || history[history.length - 1].url !== this.currentUrl) {
                    history.push(pageEntry);
                    this.setHistory(history);
                    this.setPosition(history.length - 1);
                }
            } else {
                // We used back button and are now navigating to a new page
                // Truncate history after current position and add new entry
                const newHistory = history.slice(0, position + 1);
                newHistory.push(pageEntry);
                this.setHistory(newHistory);
                this.setPosition(newHistory.length - 1);
            }
        }
        
        canGoBack() {
            const position = this.getPosition();
            return position > 0;
        }
        
        goBack() {
            if (!this.canGoBack()) {
                return;
            }
            
            const history = this.getHistory();
            const position = this.getPosition();
            const newPosition = position - 1;
            
            this.setPosition(newPosition);
            
            // Navigate to previous page
            const previousPage = history[newPosition];
            if (previousPage && previousPage.url) {
                window.location.href = previousPage.url;
            }
        }
        
        navigateTo(url) {
            // Record this as a new forward navigation
            this.setPosition(this.getHistory().length);
            window.location.href = url;
        }
        
        updateNavigationState() {
            // Update back button state
            const backBtn = document.getElementById('ribbonBackBtn');
            if (backBtn) {
                if (this.canGoBack()) {
                    backBtn.disabled = false;
                    backBtn.classList.remove('disabled');
                    backBtn.title = 'Go back to previous page';
                } else {
                    backBtn.disabled = true;
                    backBtn.classList.add('disabled');
                    backBtn.title = 'No previous page';
                }
            }
            
            // Highlight current page in navigation
            this.highlightCurrentPage();
        }
        
        highlightCurrentPage() {
            // Remove all active states
            document.querySelectorAll('.ribbon-nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Find and highlight current page
            const currentPath = this.currentUrl;
            
            // Check for exact matches or partial matches
            Object.entries(NAV_PAGES).forEach(([key, page]) => {
                if (currentPath === page.url || 
                    currentPath.startsWith(page.url + '/') ||
                    (key === 'entries' && (currentPath === '/' || currentPath.includes('/entry')))) {
                    const btn = document.querySelector(`[data-nav-page="${key}"]`);
                    if (btn) {
                        btn.classList.add('active');
                    }
                }
            });
        }
        
        attachEventListeners() {
            // Back button
            const backBtn = document.getElementById('ribbonBackBtn');
            if (backBtn) {
                backBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.goBack();
                });
            }
            
            // Navigation buttons
            document.querySelectorAll('.ribbon-nav-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const url = btn.getAttribute('href');
                    if (url && url !== '#') {
                        this.navigateTo(url);
                    }
                });
            });
        }
        
        // Get navigation breadcrumb for display
        getBreadcrumb() {
            const history = this.getHistory();
            const position = this.getPosition();
            
            if (position < 0 || position >= history.length) {
                return [];
            }
            
            // Return last 3 items for breadcrumb display
            const start = Math.max(0, position - 2);
            return history.slice(start, position + 1);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.ribbonNav = new RibbonNavigation();
        });
    } else {
        window.ribbonNav = new RibbonNavigation();
    }
})();
