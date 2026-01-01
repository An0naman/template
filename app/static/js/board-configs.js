/**
 * ESP32 Board Configuration Database
 * ==================================
 * 
 * This file contains detailed configuration for various ESP32 board types,
 * including pin layouts, capabilities, and visual representation coordinates.
 */

const BOARD_CONFIGS = {
    'ESP32-WROOM-32': {
        name: 'ESP32-WROOM-32',
        image: '/static/images/boards/esp32-wroom-32.svg',
        fallbackImage: '/static/images/boards/esp32-wroom-32.png',
        chipOverlay: {
            // Position where logs should appear (over the silver chip)
            x: 95,  // Left position in pixels
            y: 115,  // Top position in pixels
            width: 150,
            height: 190
        },
        pins: [
            // Left Side (Top to Bottom) - coordinates match SVG pinout
            { pin: 36, name: 'VP/A0', x: 10, y: 110, side: 'left', type: 'input', analog: true },
            { pin: 39, name: 'VN/A3', x: 10, y: 130, side: 'left', type: 'input', analog: true },
            { pin: 34, name: 'A6', x: 10, y: 150, side: 'left', type: 'input', analog: true },
            { pin: 35, name: 'A7', x: 10, y: 170, side: 'left', type: 'input', analog: true },
            { pin: 32, name: 'A4/T9', x: 10, y: 190, side: 'left', type: 'io', analog: true, touch: true },
            { pin: 33, name: 'A5/T8', x: 10, y: 210, side: 'left', type: 'io', analog: true, touch: true },
            { pin: 25, name: 'A18/DAC1', x: 10, y: 230, side: 'left', type: 'io', analog: true, dac: true },
            { pin: 26, name: 'A19/DAC2', x: 10, y: 250, side: 'left', type: 'io', analog: true, dac: true },
            { pin: 27, name: 'A17/T7', x: 10, y: 270, side: 'left', type: 'io', analog: true, touch: true },
            { pin: 14, name: 'A16/T6', x: 10, y: 290, side: 'left', type: 'io', analog: true, touch: true },
            { pin: 12, name: 'A15/T5', x: 10, y: 310, side: 'left', type: 'io', analog: true, touch: true },
            { pin: 13, name: 'A14/T4', x: 10, y: 350, side: 'left', type: 'io', analog: true, touch: true },
            { pin: -1, name: 'GND', x: 10, y: 330, side: 'left', type: 'power' },
            { pin: -1, name: 'VIN', x: 10, y: 430, side: 'left', type: 'power' },
            
            // Right Side (Top to Bottom) - coordinates match SVG pinout
            { pin: -1, name: '3V3', x: 330, y: 70, side: 'right', type: 'power' },
            { pin: -1, name: 'GND', x: 330, y: 190, side: 'right', type: 'power' },
            { pin: 23, name: 'MOSI', x: 330, y: 90, side: 'right', type: 'io', spi: true },
            { pin: 22, name: 'SCL', x: 330, y: 110, side: 'right', type: 'io', i2c: true },
            { pin: 1, name: 'TX0', x: 330, y: 130, side: 'right', type: 'io', uart: true },
            { pin: 3, name: 'RX0', x: 330, y: 150, side: 'right', type: 'io', uart: true },
            { pin: 21, name: 'SDA', x: 330, y: 170, side: 'right', type: 'io', i2c: true },
            { pin: 19, name: 'MISO', x: 330, y: 210, side: 'right', type: 'io', spi: true },
            { pin: 18, name: 'SCK', x: 330, y: 230, side: 'right', type: 'io', spi: true },
            { pin: 5, name: 'SS', x: 330, y: 250, side: 'right', type: 'io', spi: true },
            { pin: 17, name: 'TX2', x: 330, y: 270, side: 'right', type: 'io', uart: true },
            { pin: 16, name: 'RX2', x: 330, y: 290, side: 'right', type: 'io', uart: true },
            { pin: 4, name: 'A10/T0', x: 330, y: 310, side: 'right', type: 'io', analog: true, touch: true },
            { pin: 0, name: 'BOOT/T1', x: 330, y: 330, side: 'right', type: 'io', analog: true, touch: true, boot: true },
            { pin: 2, name: 'LED/T2', x: 330, y: 350, side: 'right', type: 'io', analog: true, touch: true, led: true },
            { pin: 15, name: 'A13/T3', x: 330, y: 370, side: 'right', type: 'io', analog: true, touch: true }
        ],
        
        // Pin capabilities mapping
        capabilities: {
            digital_output: [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
            digital_input: [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39],
            analog_input: [32, 33, 34, 35, 36, 39],
            pwm: [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
            dac: [25, 26],
            touch: [0, 2, 4, 12, 13, 14, 15, 27, 32, 33]
        }
    },
    
    'ESP32-DevKitC': {
        name: 'ESP32-DevKitC',
        image: '/static/images/boards/esp32-devkitc.png',
        chipOverlay: {
            x: 90,
            y: 100,
            width: 110,
            height: 130
        },
        pins: [
            // Similar structure - can be expanded for other boards
        ],
        capabilities: {
            // Similar capabilities
        }
    },
    
    'firebeetle2_esp32c6': {
        name: 'FireBeetle 2 ESP32-C6',
        image: '/static/images/boards/firebeetle2-esp32c6.png', // Placeholder
        chipOverlay: {
            x: 95,
            y: 115,
            width: 150,
            height: 190
        },
        pins: [
            // Left Side
            { pin: 0, name: 'A0/Bat', x: 10, y: 110, side: 'left', type: 'input', analog: true, battery: true },
            { pin: 1, name: 'A1', x: 10, y: 130, side: 'left', type: 'io', analog: true },
            { pin: 2, name: 'A2', x: 10, y: 150, side: 'left', type: 'io', analog: true },
            { pin: 3, name: 'A3', x: 10, y: 170, side: 'left', type: 'io', analog: true },
            { pin: 4, name: 'A4/SDA', x: 10, y: 190, side: 'left', type: 'io', analog: true, i2c: true },
            { pin: 5, name: 'A5/SCL', x: 10, y: 210, side: 'left', type: 'io', analog: true, i2c: true },
            { pin: 6, name: 'IO6', x: 10, y: 230, side: 'left', type: 'io', analog: true },
            { pin: 7, name: 'IO7', x: 10, y: 250, side: 'left', type: 'io', analog: true },
            
            // Right Side
            { pin: 15, name: 'IO15/LED', x: 330, y: 110, side: 'right', type: 'io', led: true },
            { pin: 8, name: 'IO8', x: 330, y: 130, side: 'right', type: 'io' },
            { pin: 9, name: 'IO9', x: 330, y: 150, side: 'right', type: 'io', boot: true },
            { pin: 10, name: 'IO10', x: 330, y: 170, side: 'right', type: 'io' },
            { pin: 11, name: 'IO11', x: 330, y: 190, side: 'right', type: 'io' },
            { pin: 12, name: 'IO12', x: 330, y: 210, side: 'right', type: 'io' },
            { pin: 13, name: 'IO13', x: 330, y: 230, side: 'right', type: 'io' },
            { pin: 14, name: 'IO14', x: 330, y: 250, side: 'right', type: 'io' }
        ],
        capabilities: {
            digital_output: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            digital_input: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            analog_input: [0, 1, 2, 3, 4, 5, 6], // LP_ADC pins
            pwm: [1, 2, 3, 4, 5, 6, 7, 8, 15],
            i2c: [4, 5],
            led: [15],
            battery: [0]
        }
    }
};

/**
 * Get board configuration by type
 */
function getBoardConfig(boardType) {
    return BOARD_CONFIGS[boardType] || BOARD_CONFIGS['ESP32-WROOM-32'];
}

/**
 * Get pin information by pin number
 */
function getPinInfo(boardType, pinNumber) {
    const config = getBoardConfig(boardType);
    return config.pins.find(p => p.pin === pinNumber);
}

/**
 * Check if a pin supports a specific capability
 */
function pinSupportsCapability(boardType, pinNumber, capability) {
    const config = getBoardConfig(boardType);
    if (!config.capabilities[capability]) return false;
    return config.capabilities[capability].includes(pinNumber);
}

/**
 * Get all pins with a specific capability
 */
function getPinsWithCapability(boardType, capability) {
    const config = getBoardConfig(boardType);
    return config.capabilities[capability] || [];
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BOARD_CONFIGS, getBoardConfig, getPinInfo, pinSupportsCapability, getPinsWithCapability };
}
