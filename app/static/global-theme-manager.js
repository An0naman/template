/**
 * Global Theme Manager
 * Handles automatic dark mode transitions across all pages
 */
class GlobalThemeManager {
    constructor() {
        this.checkInterval = null;
        this.settings = {
            autoDarkMode: false,
            darkModeStart: '18:00',
            darkModeEnd: '06:00',
            currentTheme: 'default',
            customColors: {},
            customLightMode: {},
            customDarkMode: {}
        };
    }

    /**
     * Initialize the global theme manager
     */
    async init() {
        try {
            // Load current theme settings from server
            await this.loadSettings();
            
            // Start auto-checking if auto dark mode is enabled
            if (this.settings.autoDarkMode) {
                this.startAutoModeCheck();
            }
        } catch (error) {
            console.error('Failed to initialize global theme manager:', error);
        }
    }

    /**
     * Load theme settings from server
     */
    async loadSettings() {
        try {
            const response = await fetch('/api/theme_settings');
            if (response.ok) {
                const data = await response.json();
                this.settings = {
                    autoDarkMode: data.auto_dark_mode || false,
                    darkModeStart: data.dark_mode_start || '18:00',
                    darkModeEnd: data.dark_mode_end || '06:00',
                    currentTheme: data.theme || 'default',
                    customColors: data.custom_colors || {},
                    customLightMode: data.custom_light_mode || {},
                    customDarkMode: data.custom_dark_mode || {}
                };
            }
        } catch (error) {
            console.error('Failed to load theme settings:', error);
        }
    }

    /**
     * Start automatic mode checking
     */
    startAutoModeCheck() {
        // Clear any existing interval
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }

        // Check immediately
        this.checkAndApplyAutoMode();

        // Check every minute
        this.checkInterval = setInterval(() => {
            this.checkAndApplyAutoMode();
        }, 60000); // Check every minute
    }

    /**
     * Stop automatic mode checking
     */
    stopAutoModeCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }

    /**
     * Check if current time is within dark mode hours and apply if needed
     */
    checkAndApplyAutoMode() {
        if (!this.settings.autoDarkMode) {
            return;
        }

        const shouldBeDark = this.isAutoDarkModeTime();
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const isDark = currentTheme === 'dark';

        // Only change if there's a mismatch
        if (shouldBeDark !== isDark) {
            this.applyTheme(shouldBeDark);
        }
    }

    /**
     * Calculate if dark mode should be active based on current time
     */
    isAutoDarkModeTime() {
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        const startTime = this.parseTime(this.settings.darkModeStart);
        const endTime = this.parseTime(this.settings.darkModeEnd);
        
        // Handle overnight periods (e.g., 18:00 to 06:00)
        if (startTime > endTime) {
            return currentTime >= startTime || currentTime < endTime;
        } else {
            return currentTime >= startTime && currentTime < endTime;
        }
    }

    /**
     * Parse time string (HH:MM) to minutes since midnight
     */
    parseTime(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    }

    /**
     * Apply theme (dark/light mode)
     */
    applyTheme(isDark) {
        // Update HTML attribute
        document.documentElement.setAttribute('data-bs-theme', isDark ? 'dark' : 'light');
        
        // Update CSS variables if needed
        this.updateCSSVariables(isDark);
        
        // Dispatch custom event for other components to listen
        const event = new CustomEvent('themeChanged', {
            detail: { isDark, auto: true }
        });
        document.dispatchEvent(event);
    }

    /**
     * Update CSS variables based on current theme
     */
    updateCSSVariables(isDark) {
        const root = document.documentElement;
        
        // Apply light/dark mode colors
        const colors = isDark ? this.getDarkModeColors() : this.getLightModeColors();
        
        Object.entries(colors).forEach(([property, value]) => {
            root.style.setProperty(property, value);
        });
    }

    /**
     * Get light mode CSS variables
     */
    getLightModeColors() {
        const defaults = {
            '--theme-bg-body': '#ffffff',
            '--theme-bg-card': '#ffffff',
            '--theme-bg-surface': '#f8f9fa',
            '--theme-text': '#212529',
            '--theme-text-muted': '#6c757d',
            '--theme-border': '#dee2e6'
        };
        
        const custom = {};
        Object.keys(this.settings.customLightMode).forEach(key => {
            custom[`--theme-${key.replace(/_/g, '-')}`] = this.settings.customLightMode[key];
        });
        
        return { ...defaults, ...custom };
    }

    /**
     * Get dark mode CSS variables
     */
    getDarkModeColors() {
        const defaults = {
            '--theme-bg-body': '#0d1117',
            '--theme-bg-card': '#161b22',
            '--theme-bg-surface': '#21262d',
            '--theme-text': '#f0f6fc',
            '--theme-text-muted': '#8b949e',
            '--theme-border': '#30363d'
        };
        
        const custom = {};
        Object.keys(this.settings.customDarkMode).forEach(key => {
            custom[`--theme-${key.replace(/_/g, '-')}`] = this.settings.customDarkMode[key];
        });
        
        return { ...defaults, ...custom };
    }

    /**
     * Refresh settings from server (called when settings are updated)
     */
    async refreshSettings() {
        await this.loadSettings();
        
        if (this.settings.autoDarkMode) {
            this.startAutoModeCheck();
        } else {
            this.stopAutoModeCheck();
        }
    }
}

// Initialize global theme manager when DOM is ready
let globalThemeManager;

document.addEventListener('DOMContentLoaded', function() {
    globalThemeManager = new GlobalThemeManager();
    globalThemeManager.init();
});

// Make it globally available
window.globalThemeManager = globalThemeManager;
