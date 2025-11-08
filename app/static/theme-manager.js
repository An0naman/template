/**
 * Unified Theme Manager
 * Manages all theme settings and provides real-time preview updates
 */
class ThemeManager {
    constructor() {
        this.state = {
            // Core theme settings
            theme: 'default',
            darkMode: false,
            autoDarkMode: false,
            darkModeStart: '18:00',
            darkModeEnd: '06:00',
            fontSize: 'normal',
            highContrast: false,
            
            // Color settings
            customColors: {},
            customLightMode: {},
            customDarkMode: {},
            
            // Section styling
            sectionStyles: {
                borderStyle: 'none',
                spacing: 'normal',
                background: 'subtle',
                animation: 'none',
                effect: 'none',
                pattern: 'none',
                decoration: 'none'
            }
        };
        
        this.previewElements = new Map();
        this.themeSchemes = this.getThemeSchemes();
        this.initialized = false;
    }
    
    getThemeSchemes() {
        return {
            'default': {
                'primary': '#0d6efd',
                'primary_hover': '#0b5ed7',
                'secondary': '#6c757d',
                'success': '#198754',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#0dcaf0'
            },
            'emerald': {
                'primary': '#10b981',
                'primary_hover': '#059669',
                'secondary': '#6b7280',
                'success': '#059669',
                'danger': '#ef4444',
                'warning': '#f59e0b',
                'info': '#06b6d4'
            },
            'purple': {
                'primary': '#8b5cf6',
                'primary_hover': '#7c3aed',
                'secondary': '#6b7280',
                'success': '#10b981',
                'danger': '#ef4444',
                'warning': '#f59e0b',
                'info': '#06b6d4'
            },
            'amber': {
                'primary': '#f59e0b',
                'primary_hover': '#d97706',
                'secondary': '#6b7280',
                'success': '#10b981',
                'danger': '#ef4444',
                'warning': '#f97316',
                'info': '#06b6d4'
            },
            'custom': {
                'primary': '#0d6efd',
                'primary_hover': '#0b5ed7',
                'secondary': '#6c757d',
                'success': '#198754',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#0dcaf0'
            }
        };
    }
    
    /**
     * Initialize the theme manager with current settings
     */
    init(initialState = {}) {
        // Merge with current state
        this.state = { ...this.state, ...initialState };
        
        // Create dynamic style element for real-time updates
        this.createDynamicStyleSheet();
        
        // Initialize preview area
        this.initializePreview();
        
        this.initialized = true;
        this.updatePreview();
    }
    
    /**
     * Create dynamic stylesheet for real-time theme updates
     */
    createDynamicStyleSheet() {
        // Remove existing dynamic styles
        const existing = document.getElementById('theme-manager-dynamic-styles');
        if (existing) existing.remove();
        
        // Create new style element
        this.dynamicStyles = document.createElement('style');
        this.dynamicStyles.id = 'theme-manager-dynamic-styles';
        document.head.appendChild(this.dynamicStyles);
    }
    
    /**
     * Update theme setting and trigger preview update
     */
    updateSetting(category, key, value) {
        if (category === 'root') {
            this.state[key] = value;
        } else {
            this.state[category] = this.state[category] || {};
            this.state[category][key] = value;
        }
        
        this.updatePreview();
        this.notifyListeners(category, key, value);
    }
    
    /**
     * Generate CSS variables based on current state
     */
    generateCSSVariables() {
        const colors = this.getCurrentColors();
        const spacing = this.getSectionSpacing();
        const borderStyling = this.getSectionBorderStyling();
        const sectionBackground = this.getSectionBackground();
        
        const cssVars = {
            // Theme colors
            '--theme-primary': colors.primary,
            '--theme-primary-hover': colors.primary_hover,
            '--theme-secondary': colors.secondary,
            '--theme-success': colors.success,
            '--theme-danger': colors.danger,
            '--theme-warning': colors.warning,
            '--theme-info': colors.info,
            
            // RGB variations for transparency
            '--theme-primary-rgb': this.hexToRgb(colors.primary),
            '--theme-primary-hover-rgb': this.hexToRgb(colors.primary_hover),
            '--theme-secondary-rgb': this.hexToRgb(colors.secondary),
            '--theme-success-rgb': this.hexToRgb(colors.success),
            '--theme-danger-rgb': this.hexToRgb(colors.danger),
            '--theme-warning-rgb': this.hexToRgb(colors.warning),
            '--theme-info-rgb': this.hexToRgb(colors.info),
            
            // Enhanced color variations
            '--theme-primary-lighter': this.lightenColor(colors.primary, 0.1),
            '--theme-primary-darker': this.darkenColor(colors.primary, 0.1),
            '--theme-secondary-hover': this.darkenColor(colors.secondary, 0.1),
            '--theme-secondary-darker': this.darkenColor(colors.secondary, 0.1),
            '--theme-success-hover': this.darkenColor(colors.success, 0.1),
            '--theme-success-darker': this.darkenColor(colors.success, 0.1),
            '--theme-danger-hover': this.darkenColor(colors.danger, 0.1),
            '--theme-danger-darker': this.darkenColor(colors.danger, 0.1),
            '--theme-warning-hover': this.darkenColor(colors.warning, 0.1),
            '--theme-warning-darker': this.darkenColor(colors.warning, 0.1),
            '--theme-info-hover': this.darkenColor(colors.info, 0.1),
            '--theme-info-darker': this.darkenColor(colors.info, 0.1),
            
            // Subtle color variations for backgrounds
            '--theme-primary-subtle': `rgba(${this.hexToRgb(colors.primary)}, 0.1)`,
            '--theme-secondary-subtle': `rgba(${this.hexToRgb(colors.secondary)}, 0.1)`,
            '--theme-success-subtle': `rgba(${this.hexToRgb(colors.success)}, 0.1)`,
            '--theme-danger-subtle': `rgba(${this.hexToRgb(colors.danger)}, 0.1)`,
            '--theme-warning-subtle': `rgba(${this.hexToRgb(colors.warning)}, 0.1)`,
            '--theme-info-subtle': `rgba(${this.hexToRgb(colors.info)}, 0.1)`,
            
            // Border variations
            '--theme-primary-border': `rgba(${this.hexToRgb(colors.primary)}, 0.2)`,
            '--theme-secondary-border': `rgba(${this.hexToRgb(colors.secondary)}, 0.2)`,
            '--theme-success-border': `rgba(${this.hexToRgb(colors.success)}, 0.2)`,
            '--theme-danger-border': `rgba(${this.hexToRgb(colors.danger)}, 0.2)`,
            '--theme-warning-border': `rgba(${this.hexToRgb(colors.warning)}, 0.2)`,
            '--theme-info-border': `rgba(${this.hexToRgb(colors.info)}, 0.2)`,
            
            // Focus ring color
            '--theme-focus-ring': `rgba(${this.hexToRgb(colors.primary)}, 0.25)`,
            
            // Bootstrap CSS Variable Overrides
            '--bs-primary': colors.primary,
            '--bs-primary-rgb': this.hexToRgb(colors.primary),
            '--bs-secondary': colors.secondary,
            '--bs-secondary-rgb': this.hexToRgb(colors.secondary),
            '--bs-success': colors.success,
            '--bs-success-rgb': this.hexToRgb(colors.success),
            '--bs-danger': colors.danger,
            '--bs-danger-rgb': this.hexToRgb(colors.danger),
            '--bs-warning': colors.warning,
            '--bs-warning-rgb': this.hexToRgb(colors.warning),
            '--bs-info': colors.info,
            '--bs-info-rgb': this.hexToRgb(colors.info),
            
            // Bootstrap button and badge text colors
            '--bs-primary-text-emphasis': this.state.darkMode ? colors.primary : this.darkenColor(colors.primary, 0.2),
            '--bs-secondary-text-emphasis': this.state.darkMode ? colors.secondary : this.darkenColor(colors.secondary, 0.2),
            '--bs-success-text-emphasis': this.state.darkMode ? colors.success : this.darkenColor(colors.success, 0.2),
            '--bs-danger-text-emphasis': this.state.darkMode ? colors.danger : this.darkenColor(colors.danger, 0.2),
            '--bs-warning-text-emphasis': this.state.darkMode ? colors.warning : this.darkenColor(colors.warning, 0.2),
            '--bs-info-text-emphasis': this.state.darkMode ? colors.info : this.darkenColor(colors.info, 0.2),
            
            // Bootstrap border emphasis colors
            '--bs-primary-border-subtle': `rgba(${this.hexToRgb(colors.primary)}, 0.2)`,
            '--bs-secondary-border-subtle': `rgba(${this.hexToRgb(colors.secondary)}, 0.2)`,
            '--bs-success-border-subtle': `rgba(${this.hexToRgb(colors.success)}, 0.2)`,
            '--bs-danger-border-subtle': `rgba(${this.hexToRgb(colors.danger)}, 0.2)`,
            '--bs-warning-border-subtle': `rgba(${this.hexToRgb(colors.warning)}, 0.2)`,
            '--bs-info-border-subtle': `rgba(${this.hexToRgb(colors.info)}, 0.2)`,
            
            // Bootstrap background subtle colors for badges and alerts
            '--bs-primary-bg-subtle': `rgba(${this.hexToRgb(colors.primary)}, 0.1)`,
            '--bs-secondary-bg-subtle': `rgba(${this.hexToRgb(colors.secondary)}, 0.1)`,
            '--bs-success-bg-subtle': `rgba(${this.hexToRgb(colors.success)}, 0.1)`,
            '--bs-danger-bg-subtle': `rgba(${this.hexToRgb(colors.danger)}, 0.1)`,
            '--bs-warning-bg-subtle': `rgba(${this.hexToRgb(colors.warning)}, 0.1)`,
            '--bs-info-bg-subtle': `rgba(${this.hexToRgb(colors.info)}, 0.1)`,
            
            // Bootstrap background and text overrides
            '--bs-body-bg': this.state.darkMode 
                ? (this.state.customDarkMode.bg_body || '#0d1117')
                : (this.state.customLightMode.bg_body || '#ffffff'),
            '--bs-body-color': this.state.darkMode 
                ? (this.state.customDarkMode.text || '#f0f6fc')
                : (this.state.customLightMode.text || '#212529'),
            '--bs-secondary-bg': this.state.darkMode 
                ? (this.state.customDarkMode.bg_surface || '#21262d')
                : (this.state.customLightMode.bg_surface || '#f8f9fa'),
            '--bs-border-color': this.state.darkMode 
                ? (this.state.customDarkMode.border || '#30363d')
                : (this.state.customLightMode.border || '#dee2e6'),
            
            // Section styling
            '--section-padding': spacing,
            '--section-margin-bottom': spacing,
            '--section-animation': this.getSectionAnimation(),
            
            // Border styling properties
            ...borderStyling,
            
            // Section background properties
            ...sectionBackground,
            
            // Light/Dark mode colors
            ...(this.state.darkMode ? this.getDarkModeColors() : this.getLightModeColors())
        };
        
        return cssVars;
    }
    
    /**
     * Get current theme colors (with custom overrides)
     */
    getCurrentColors() {
        const baseColors = this.themeSchemes[this.state.theme] || this.themeSchemes.default;
        
        if (this.state.theme === 'custom') {
            return { ...baseColors, ...this.state.customColors };
        }
        
        return baseColors;
    }
    
    /**
     * Get light mode colors (with custom overrides)
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
        Object.keys(this.state.customLightMode).forEach(key => {
            custom[`--theme-${key.replace(/_/g, '-')}`] = this.state.customLightMode[key];
        });
        
        return { ...defaults, ...custom };
    }
    
    /**
     * Get dark mode colors (with custom overrides)
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
        Object.keys(this.state.customDarkMode).forEach(key => {
            custom[`--theme-${key.replace(/_/g, '-')}`] = this.state.customDarkMode[key];
        });
        
        return { ...defaults, ...custom };
    }
    
    /**
     * Get section spacing based on current setting
     */
    getSectionSpacing() {
        const spacingMap = {
            'compact': '1rem',
            'normal': '1.5rem',
            'spacious': '2rem'
        };
        return spacingMap[this.state.sectionStyles.spacing] || spacingMap.normal;
    }
    
    /**
     * Get comprehensive border styling - 4 TRULY DISTINCT styles
     */
    getSectionBorderStyling() {
        const borderStyle = this.state.sectionStyles.borderStyle || 'none';
        const borderColor = this.state.darkMode 
            ? (this.state.customDarkMode.border || '#30363d')
            : (this.state.customLightMode.border || '#dee2e6');
        
        const borderStyleMap = {
            'none': {
                '--section-border-radius': '8px',
                '--section-border-width': '0',
                '--section-border-style': 'none',
                '--section-border-color': 'transparent',
                '--section-border': 'none'
            },
            'thin': {
                '--section-border-radius': '4px',
                '--section-border-width': '1px',
                '--section-border-style': 'solid',
                '--section-border-color': borderColor,
                '--section-border': `1px solid ${borderColor}`
            },
            'thick': {
                '--section-border-radius': '12px',
                '--section-border-width': '4px',
                '--section-border-style': 'solid',
                '--section-border-color': borderColor,
                '--section-border': `4px solid ${borderColor}`
            },
            'dashed': {
                '--section-border-radius': '8px',
                '--section-border-width': '3px',
                '--section-border-style': 'dashed',
                '--section-border-color': borderColor,
                '--section-border': `3px dashed ${borderColor}`
            }
        };
        
        return borderStyleMap[borderStyle] || borderStyleMap.none;
    }
    
    /**
     * Get section border radius based on current setting (legacy method for backward compatibility)
     */
    getSectionBorderRadius() {
        const borderStyling = this.getSectionBorderStyling();
        return borderStyling['--section-border-radius'] || '0.75rem';
    }
    
    /**
     * Get section background styling based on current setting
     */
    getSectionBackground() {
        const background = this.state.sectionStyles.background || 'subtle';
        const isDark = this.state.darkMode;
        
        // Get the base color from custom settings or defaults
        const baseColor = isDark 
            ? (this.state.customDarkMode.bg_surface || '#161b22')
            : (this.state.customLightMode.bg_surface || '#ffffff');
        
        const borderColor = isDark 
            ? (this.state.customDarkMode.border || '#30363d')
            : (this.state.customLightMode.border || '#dee2e6');
        
        if (isDark) {
            switch (background) {
                case 'flat':
                    return {
                        '--section-bg': this.state.customDarkMode.bg_body || '#0d1117',
                        '--section-border': 'transparent',
                        '--section-shadow': 'none'
                    };
                case 'subtle':
                    return {
                        '--section-bg': baseColor,
                        '--section-border': borderColor,
                        '--section-shadow': '0 1px 3px rgba(0, 0, 0, 0.2)'
                    };
                case 'elevated':
                    return {
                        '--section-bg': this.lightenColor(baseColor, 0.03),
                        '--section-border': this.lightenColor(borderColor, 0.1),
                        '--section-shadow': '0 4px 12px rgba(0, 0, 0, 0.4)'
                    };
                case 'glassmorphic':
                    const rgb = this.hexToRgb(baseColor);
                    return {
                        '--section-bg': `rgba(${rgb}, 0.8)`,
                        '--section-border': this.lightenColor(borderColor, 0.2),
                        '--section-shadow': '0 8px 32px rgba(0, 0, 0, 0.3)',
                        '--section-backdrop-filter': 'blur(8px)'
                    };
            }
        } else {
            switch (background) {
                case 'flat':
                    return {
                        '--section-bg': this.state.customLightMode.bg_body || '#ffffff',
                        '--section-border': 'transparent',
                        '--section-shadow': 'none'
                    };
                case 'subtle':
                    return {
                        '--section-bg': baseColor,
                        '--section-border': borderColor,
                        '--section-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)'
                    };
                case 'elevated':
                    return {
                        '--section-bg': this.lightenColor(baseColor, 0.02),
                        '--section-border': this.darkenColor(borderColor, 0.1),
                        '--section-shadow': '0 4px 12px rgba(0, 0, 0, 0.15)'
                    };
                case 'glassmorphic':
                    const rgb = this.hexToRgb(baseColor);
                    return {
                        '--section-bg': `rgba(${rgb}, 0.9)`,
                        '--section-border': this.darkenColor(borderColor, 0.2),
                        '--section-shadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
                        '--section-backdrop-filter': 'blur(8px)'
                    };
            }
        }
        
        return {};
    }
    
    /**
     * Get section animation based on current setting
     */
    getSectionAnimation() {
        const animationMap = {
            'none': 'none',
            'fade': 'fadeIn 0.5s ease-in-out',
            'slide': 'slideInUp 0.6s ease-out',
            'bounce': 'bounceIn 0.8s ease-out',
            'pulse': 'pulse 2s infinite ease-in-out'
        };
        return animationMap[this.state.sectionStyles.animation] || animationMap.none;
    }
    
    /**
     * Update the live preview with current settings
     */
    updatePreview() {
        if (!this.initialized) return;
        
        const cssVars = this.generateCSSVariables();
        const cssString = Object.entries(cssVars)
            .map(([key, value]) => `${key}: ${value};`)
            .join('\n');
        
        this.dynamicStyles.textContent = `:root { ${cssString} }`;
        
        // Also update the server-side theme styles element if it exists
        const serverThemeStyles = document.getElementById('theme-styles');
        if (serverThemeStyles) {
            serverThemeStyles.textContent = `:root { ${cssString} }`;
        }
        
        // Update HTML theme attribute
        document.documentElement.setAttribute(
            'data-bs-theme', 
            this.state.darkMode ? 'dark' : 'light'
        );
        
        // Update font size
        this.updateFontSize();
        
        // Update section effects
        this.updateSectionEffects();
    }
    
    /**
     * Update font size based on current setting
     */
    updateFontSize() {
        const fontSizeMap = {
            'small': '14px',
            'normal': '16px',
            'large': '18px',
            'extra-large': '20px'
        };
        
        const fontSize = fontSizeMap[this.state.fontSize] || fontSizeMap.normal;
        document.documentElement.style.fontSize = fontSize;
    }
    
    /**
     * Update section visual effects
     */
    updateSectionEffects() {
        const preview = document.getElementById('unified-preview');
        if (!preview) return;
        
        // Update section classes
        const sections = preview.querySelectorAll('.preview-section');
        sections.forEach(section => {
            // Remove existing effect classes
            section.className = section.className.replace(/\b(effect|pattern|decoration)-\S+/g, '');
            
            // Add current effect classes
            if (this.state.sectionStyles.effect !== 'none') {
                section.classList.add(`effect-${this.state.sectionStyles.effect}`);
            }
            if (this.state.sectionStyles.pattern !== 'none') {
                section.classList.add(`pattern-${this.state.sectionStyles.pattern}`);
            }
            if (this.state.sectionStyles.decoration !== 'none') {
                section.classList.add(`decoration-${this.state.sectionStyles.decoration}`);
            }
        });
    }
    
    /**
     * Initialize the preview area with real app components
     */
    initializePreview() {
        const previewContainer = document.getElementById('unified-preview');
        if (!previewContainer) return;
        
        // Clear existing content
        previewContainer.innerHTML = '';
        
        // Add real app-like components
        previewContainer.appendChild(this.createEntryPreview());
        previewContainer.appendChild(this.createFormPreview());
        previewContainer.appendChild(this.createProgressPreview());
        previewContainer.appendChild(this.createTablePreview());
        previewContainer.appendChild(this.createAlertsPreview());
    }
    
    /**
     * Create entry detail preview (mirrors entry_detail.html structure)
     */
    createEntryPreview() {
        const section = document.createElement('div');
        section.className = 'preview-section theme-section mb-4';
        section.innerHTML = `
            <div class="section-header">
                <h4 class="section-title">
                    <i class="fas fa-file-alt"></i>
                    Sample Entry
                </h4>
                <div class="btn-group">
                    <button class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-outline-secondary btn-sm">
                        <i class="fas fa-share"></i> Share
                    </button>
                </div>
            </div>
            <div class="section-content">
                <p class="text-muted mb-3">Created: January 15, 2025 | Last updated: 2 hours ago</p>
                <div class="mb-3">
                    <span class="badge bg-primary me-1">Primary</span>
                    <span class="badge bg-success me-1">Success</span>
                    <span class="badge bg-warning me-1">Warning</span>
                    <span class="badge bg-danger me-1">Danger</span>
                    <span class="badge bg-info">Info</span>
                </div>
                <p>This is a sample entry showing how content appears with your theme settings. The text should be clearly readable with good contrast.</p>
                <blockquote class="blockquote border-start border-primary border-3 ps-3 text-muted">
                    "This blockquote demonstrates how quoted content appears in your selected theme."
                </blockquote>
            </div>
        `;
        return section;
    }
    
    /**
     * Create form preview
     */
    createFormPreview() {
        const section = document.createElement('div');
        section.className = 'preview-section theme-section mb-4';
        section.innerHTML = `
            <div class="section-header">
                <h5 class="section-title">
                    <i class="fas fa-wpforms"></i>
                    Form Elements
                </h5>
            </div>
            <div class="section-content">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Text Input</label>
                            <input type="text" class="form-control" placeholder="Sample input" value="Preview text">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Select Dropdown</label>
                            <select class="form-select">
                                <option>Choose option...</option>
                                <option selected>Selected option</option>
                                <option>Another option</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">Textarea</label>
                            <textarea class="form-control" rows="3">Sample textarea content showing multi-line input styling.</textarea>
                        </div>
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-primary">Primary Action</button>
                    <button class="btn btn-outline-secondary">Secondary</button>
                    <button class="btn btn-success">Save</button>
                    <button class="btn btn-outline-danger">Cancel</button>
                </div>
            </div>
        `;
        return section;
    }
    
    /**
     * Create progress bars preview
     */
    createProgressPreview() {
        const section = document.createElement('div');
        section.className = 'preview-section theme-section mb-4';
        section.innerHTML = `
            <div class="section-header">
                <h5 class="section-title">
                    <i class="fas fa-tasks"></i>
                    Progress & Status
                </h5>
            </div>
            <div class="section-content">
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <label class="form-label mb-0">File Upload Progress</label>
                        <small class="text-muted">65%</small>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar bg-primary" role="progressbar" style="width: 65%;" 
                             aria-valuenow="65" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <label class="form-label mb-0">Task Completion</label>
                        <small class="text-muted">8/10 tasks</small>
                    </div>
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar bg-success" role="progressbar" style="width: 80%;" 
                             aria-valuenow="80" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <label class="form-label mb-0">Storage Usage</label>
                        <small class="text-muted">3.2GB / 5GB</small>
                    </div>
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-warning" role="progressbar" style="width: 64%;" 
                             aria-valuenow="64" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <label class="form-label mb-0">System Load</label>
                        <small class="text-muted">High (92%)</small>
                    </div>
                    <div class="progress" style="height: 12px;">
                        <div class="progress-bar bg-danger" role="progressbar" style="width: 92%;" 
                             aria-valuenow="92" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <label class="form-label mb-0">Multi-step Process</label>
                        <small class="text-muted">Step 2 of 4</small>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar bg-info" role="progressbar" style="width: 25%;" 
                             aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
                        <div class="progress-bar bg-info" role="progressbar" style="width: 25%;" 
                             aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
                
                <div class="mb-0">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <label class="form-label mb-0">Animated Progress</label>
                        <small class="text-muted">Loading...</small>
                    </div>
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                             role="progressbar" style="width: 45%;" 
                             aria-valuenow="45" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            </div>
        `;
        return section;
    }
    
    /**
     * Create table preview
     */
    createTablePreview() {
        const section = document.createElement('div');
        section.className = 'preview-section theme-section mb-4';
        section.innerHTML = `
            <div class="section-header">
                <h5 class="section-title">
                    <i class="fas fa-table"></i>
                    Data Table
                </h5>
            </div>
            <div class="section-content">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Sample Entry 1</td>
                                <td><span class="badge bg-success">Active</span></td>
                                <td>2025-01-15</td>
                                <td>
                                    <button class="btn btn-outline-primary btn-sm">Edit</button>
                                </td>
                            </tr>
                            <tr>
                                <td>Sample Entry 2</td>
                                <td><span class="badge bg-warning">Pending</span></td>
                                <td>2025-01-14</td>
                                <td>
                                    <button class="btn btn-outline-primary btn-sm">Edit</button>
                                </td>
                            </tr>
                            <tr>
                                <td>Sample Entry 3</td>
                                <td><span class="badge bg-danger">Inactive</span></td>
                                <td>2025-01-13</td>
                                <td>
                                    <button class="btn btn-outline-primary btn-sm">Edit</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        return section;
    }
    
    /**
     * Create alerts preview
     */
    createAlertsPreview() {
        const section = document.createElement('div');
        section.className = 'preview-section theme-section mb-4';
        section.innerHTML = `
            <div class="section-header">
                <h5 class="section-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Alerts & Messages
                </h5>
            </div>
            <div class="section-content">
                <div class="alert alert-primary">
                    <i class="fas fa-info-circle me-2"></i>
                    Primary alert with informational content.
                </div>
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Success alert indicating completed action.
                </div>
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Warning alert requiring attention.
                </div>
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle me-2"></i>
                    Danger alert indicating an error.
                </div>
            </div>
        `;
        return section;
    }
    
    /**
     * Utility function to convert hex to RGB
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (result) {
            const r = parseInt(result[1], 16);
            const g = parseInt(result[2], 16);
            const b = parseInt(result[3], 16);
            return `${r}, ${g}, ${b}`;
        }
        return '0, 0, 0';
    }
    
    /**
     * Utility function to lighten a color
     */
    lightenColor(hex, percent) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!result) return hex;
        
        const r = Math.round(parseInt(result[1], 16) + (255 - parseInt(result[1], 16)) * percent);
        const g = Math.round(parseInt(result[2], 16) + (255 - parseInt(result[2], 16)) * percent);
        const b = Math.round(parseInt(result[3], 16) + (255 - parseInt(result[3], 16)) * percent);
        
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
    
    /**
     * Utility function to darken a color
     */
    darkenColor(hex, percent) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!result) return hex;
        
        const r = Math.round(parseInt(result[1], 16) * (1 - percent));
        const g = Math.round(parseInt(result[2], 16) * (1 - percent));
        const b = Math.round(parseInt(result[3], 16) * (1 - percent));
        
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
    
    /**
     * Export current theme settings
     */
    exportSettings() {
        return JSON.stringify(this.state, null, 2);
    }
    
    /**
     * Import theme settings
     */
    importSettings(settingsJson) {
        try {
            const imported = JSON.parse(settingsJson);
            this.state = { ...this.state, ...imported };
            this.updatePreview();
            return true;
        } catch (error) {
            console.error('Failed to import settings:', error);
            return false;
        }
    }
    
    /**
     * Reset to default settings
     */
    reset() {
        this.state = {
            theme: 'default',
            darkMode: false,
            fontSize: 'normal',
            highContrast: false,
            customColors: {},
            customLightMode: {},
            customDarkMode: {},
            sectionStyles: {
                borderStyle: 'none',
                spacing: 'normal',
                background: 'subtle',
                animation: 'none',
                effect: 'none',
                pattern: 'none',
                decoration: 'none'
            }
        };
        this.updatePreview();
    }
    
    /**
     * Calculate if dark mode should be active based on current time
     */
    isAutoDarkModeTime() {
        if (!this.state.autoDarkMode) return false;
        
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        const startTime = this.parseTime(this.state.darkModeStart);
        const endTime = this.parseTime(this.state.darkModeEnd);
        
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
     * Format current time for display
     */
    getCurrentTimeString() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    }
    
    /**
     * Get the mode that would be active based on auto settings
     */
    getAutoDarkModePreview() {
        if (!this.state.autoDarkMode) return 'Manual';
        return this.isAutoDarkModeTime() ? 'Dark' : 'Light';
    }
    
    /**
     * Update time display and mode preview
     */
    updateTimeDisplay() {
        const currentTimeEl = document.getElementById('currentTime');
        const modePreviewEl = document.getElementById('currentModePreview');
        
        if (currentTimeEl) {
            currentTimeEl.textContent = this.getCurrentTimeString();
        }
        
        if (modePreviewEl) {
            const mode = this.getAutoDarkModePreview();
            modePreviewEl.textContent = mode;
            modePreviewEl.className = mode === 'Dark' ? 'text-primary' : mode === 'Light' ? 'text-warning' : 'text-muted';
        }
    }

    /**
     * Save current settings to server
     */
    async saveSettings() {
        try {
            const requestData = {
                theme: this.state.theme,
                dark_mode: this.state.darkMode,
                auto_dark_mode: this.state.autoDarkMode,
                dark_mode_start: this.state.darkModeStart,
                dark_mode_end: this.state.darkModeEnd,
                font_size: this.state.fontSize,
                high_contrast: this.state.highContrast,
                custom_colors: this.state.customColors,
                custom_light_mode: this.state.customLightMode,
                custom_dark_mode: this.state.customDarkMode,
                section_styles: this.state.sectionStyles
            };

            const response = await fetch('/api/theme_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            return result.success || false;
        } catch (error) {
            console.error('Failed to save settings:', error);
            return false;
        }
    }
    
    /**
     * Event listener management
     */
    listeners = new Map();
    
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    notifyListeners(category, key, value) {
        const listeners = this.listeners.get('change') || [];
        listeners.forEach(callback => callback(category, key, value));
    }
}

// Global theme manager instance
window.themeManager = new ThemeManager();
