/**
 * ESP32 Web Interface with Interactive Board Visualization
 * =========================================================
 * 
 * This header contains the HTML/CSS/JS for the ESP32's web interface
 * with interactive board visualization and pin controls.
 */

#ifndef ESP32_WEB_INTERFACE_H
#define ESP32_WEB_INTERFACE_H

#include <Arduino.h>

// Board configuration as JSON string
const char* BOARD_CONFIG_JSON PROGMEM = R"({
  "name": "ESP32-WROOM-32",
  "pins": [
    {"pin": 36, "name": "VP/A0", "x": 15, "y": 60, "side": "left"},
    {"pin": 39, "name": "VN/A3", "x": 15, "y": 75, "side": "left"},
    {"pin": 34, "name": "A6", "x": 15, "y": 90, "side": "left"},
    {"pin": 35, "name": "A7", "x": 15, "y": 105, "side": "left"},
    {"pin": 32, "name": "A4/T9", "x": 15, "y": 120, "side": "left"},
    {"pin": 33, "name": "A5/T8", "x": 15, "y": 135, "side": "left"},
    {"pin": 25, "name": "A18/DAC1", "x": 15, "y": 150, "side": "left"},
    {"pin": 26, "name": "A19/DAC2", "x": 15, "y": 165, "side": "left"},
    {"pin": 27, "name": "A17/T7", "x": 15, "y": 180, "side": "left"},
    {"pin": 14, "name": "A16/T6", "x": 15, "y": 195, "side": "left"},
    {"pin": 12, "name": "A15/T5", "x": 15, "y": 210, "side": "left"},
    {"pin": 13, "name": "A14/T4", "x": 15, "y": 225, "side": "left"},
    {"pin": 2, "name": "A12/T2/LED", "x": 275, "y": 105, "side": "right"},
    {"pin": 15, "name": "A13/T3", "x": 275, "y": 90, "side": "right"},
    {"pin": 0, "name": "BOOT", "x": 275, "y": 120, "side": "right"},
    {"pin": 4, "name": "A10/T0", "x": 275, "y": 135, "side": "right"},
    {"pin": 16, "name": "RX2", "x": 275, "y": 150, "side": "right"},
    {"pin": 17, "name": "TX2", "x": 275, "y": 165, "side": "right"},
    {"pin": 5, "name": "SS", "x": 275, "y": 180, "side": "right"},
    {"pin": 18, "name": "SCK", "x": 275, "y": 195, "side": "right"},
    {"pin": 19, "name": "MISO", "x": 275, "y": 210, "side": "right"},
    {"pin": 21, "name": "SDA", "x": 275, "y": 225, "side": "right"},
    {"pin": 3, "name": "RX0", "x": 275, "y": 240, "side": "right"},
    {"pin": 1, "name": "TX0", "x": 275, "y": 255, "side": "right"},
    {"pin": 22, "name": "SCL", "x": 275, "y": 270, "side": "right"},
    {"pin": 23, "name": "MOSI", "x": 275, "y": 285, "side": "right"}
  ]
})";

/**
 * Generate the web interface HTML
 */
String generateWebInterface(String sensorName, String sensorId, String sensorType, 
                           OperatingMode mode, String masterUrl, String firmwareVersion,
                           float temperature, bool relayState, unsigned long uptime) {
    
    String statusClass = (mode == MODE_ONLINE) ? "good" : "warning";
    String statusIcon = (mode == MODE_ONLINE) ? "✅" : "⚠️";
    String statusText = (mode == MODE_ONLINE) ? "Online (Connected to Master)" : "Offline (Standalone)";
    
    String html = R"(<!DOCTYPE html>
<html><head>
<title>)" + sensorName + R"( - ESP32</title>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<style>
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
.container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); overflow: hidden; }
.header { background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%); color: white; padding: 20px; text-align: center; }
.header h1 { margin: 0; font-size: 2em; font-weight: 300; }
.header h2 { margin: 5px 0 0 0; font-size: 1em; opacity: 0.8; font-weight: normal; }
.content { padding: 20px; display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }
.board-section { background: #f8f9fa; padding: 20px; border-radius: 10px; }
.board-container { position: relative; width: 290px; height: 500px; margin: 0 auto; background: #2d3748; border-radius: 10px; }
.pin { position: absolute; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; cursor: pointer; transition: all 0.2s; }
.pin:hover { transform: scale(1.3); z-index: 10; }
.pin-label { position: absolute; font-size: 0.7em; color: white; pointer-events: none; white-space: nowrap; }
.pin-left { background: #3b82f6; }
.pin-right { background: #10b981; }
.pin-active { background: #fbbf24 !important; box-shadow: 0 0 10px #fbbf24; }
.logs-section { }
.sensor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }
.sensor-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; }
.sensor-value { font-size: 1.8em; font-weight: bold; color: #2d3748; }
.sensor-label { color: #718096; font-size: 0.9em; margin-bottom: 5px; }
.status { padding: 12px; margin: 15px 0; border-radius: 8px; display: flex; align-items: center; }
.status.good { background-color: #d4edda; color: #155724; border-left: 4px solid #28a745; }
.status.warning { background-color: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }
.log-monitor { background: #1a202c; color: #48bb78; padding: 15px; border-radius: 5px; font-family: monospace; height: 350px; overflow-y: auto; font-size: 0.85em; white-space: pre-wrap; }
.btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; transition: all 0.2s; margin: 5px; }
.btn-primary { background: #4a5568; color: white; }
.btn-primary:hover { background: #2d3748; }
.btn-success { background: #10b981; color: white; }
.btn-danger { background: #ef4444; color: white; }
.btn-secondary { background: #e2e8f0; color: #4a5568; }
.pin-controls { margin-top: 15px; }
.pin-control { background: white; padding: 10px; margin: 8px 0; border-radius: 6px; border: 1px solid #e2e8f0; }
.pin-control-header { font-weight: 600; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
@media (max-width: 1024px) { .content { grid-template-columns: 1fr; } }
</style>
</head><body>
<div class='container'>
<div class='header'>
<h1>🔧 )" + sensorName + R"(</h1>
<h2>ESP32 Interactive Board Monitor</h2>
</div>
<div class='content'>
<div class='board-section'>
<h3 style='margin-top: 0;'>🖥️ Board Visualization</h3>
<div class='board-container' id='boardContainer'>
<!-- Pins will be dynamically added here -->
</div>
<div class='pin-controls' id='pinControls'></div>
</div>
<div class='logs-section'>
<div class='status )" + statusClass + R"('>
<span style='font-size: 1.3em; margin-right: 10px;'>)" + statusIcon + R"(</span>
<span><strong>Status:</strong> )" + statusText + R"(</span>
</div>
<div class='sensor-grid'>
<div class='sensor-card'>
<div class='sensor-label'>🌡️ Temperature</div>
<div class='sensor-value'>)" + String(temperature, 1) + R"(°C</div>
</div>
<div class='sensor-card'>
<div class='sensor-label'>🔌 Relay</div>
<div class='sensor-value'>)" + String(relayState ? "ON" : "OFF") + R"(</div>
</div>
<div class='sensor-card'>
<div class='sensor-label'>⏱️ Uptime</div>
<div class='sensor-value' style='font-size: 1.2em;'>)" + String(uptime) + R"(s</div>
</div>
</div>
<h3>📟 Live Logs</h3>
<div id='serialMonitor' class='log-monitor'>Connecting...</div>
<div>
<button class='btn btn-secondary' onclick='clearSerial()'>🗑️ Clear</button>
<button class='btn btn-secondary' onclick='toggleAutoScroll()' id='autoScrollBtn'>⬇️ Auto-scroll: ON</button>
</div>
</div>
</div>
</div>
<script>
const BOARD_CONFIG = )" + String(BOARD_CONFIG_JSON) + R"(;
let autoScroll = true;
let activePins = new Map();

// Initialize board
function initBoard() {
  const container = document.getElementById('boardContainer');
  BOARD_CONFIG.pins.forEach(pinInfo => {
    const pin = document.createElement('div');
    pin.className = 'pin pin-' + pinInfo.side;
    pin.style.left = pinInfo.x + 'px';
    pin.style.top = pinInfo.y + 'px';
    pin.title = `Pin ${pinInfo.pin} - ${pinInfo.name}`;
    pin.id = 'pin-' + pinInfo.pin;
    
    const label = document.createElement('div');
    label.className = 'pin-label';
    label.textContent = pinInfo.name;
    label.style.left = (pinInfo.side === 'left' ? pinInfo.x + 15 : pinInfo.x - 40) + 'px';
    label.style.top = (pinInfo.y - 2) + 'px';
    
    container.appendChild(pin);
    container.appendChild(label);
  });
  
  // Fetch pin states from device
  updatePinStates();
}

async function updatePinStates() {
  try {
    const response = await fetch('/api/pins');
    const data = await response.json();
    
    const controlsContainer = document.getElementById('pinControls');
    controlsContainer.innerHTML = '<h4 style="margin-top: 15px;">Pin Controls</h4>';
    
    if (data.pins && data.pins.length > 0) {
      data.pins.forEach(pin => {
        // Update visual indicator
        const pinEl = document.getElementById('pin-' + pin.pin);
        if (pinEl) {
          if (pin.state === 'HIGH' || pin.state === 1) {
            pinEl.classList.add('pin-active');
          } else {
            pinEl.classList.remove('pin-active');
          }
        }
        
        // Add control if it's a write pin
        if (pin.type === 'gpio_write') {
          const control = document.createElement('div');
          control.className = 'pin-control';
          control.innerHTML = `
            <div class='pin-control-header'>
              <span>Pin ${pin.pin} ${pin.alias ? '(' + pin.alias + ')' : ''}</span>
              <span style='font-size: 0.8em; color: #718096;'>${pin.type}</span>
            </div>
            <button class='btn ${pin.state === 'HIGH' ? 'btn-success' : 'btn-secondary'}' 
                    onclick='setPinState(${pin.pin}, "HIGH")'>HIGH</button>
            <button class='btn ${pin.state === 'LOW' ? 'btn-danger' : 'btn-secondary'}' 
                    onclick='setPinState(${pin.pin}, "LOW")'>LOW</button>
          `;
          controlsContainer.appendChild(control);
        }
      });
    } else {
      controlsContainer.innerHTML += '<p style="color: #718096;">No controllable pins in current logic</p>';
    }
  } catch (e) {
    console.error('Failed to fetch pin states', e);
  }
}

async function setPinState(pin, value) {
  try {
    const response = await fetch('/api/pin-control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin: pin, value: value })
    });
    
    if (response.ok) {
      updatePinStates();
    }
  } catch (e) {
    console.error('Failed to set pin', e);
  }
}

function toggleAutoScroll() { 
  autoScroll = !autoScroll; 
  document.getElementById('autoScrollBtn').innerText = '⬇️ Auto-scroll: ' + (autoScroll ? 'ON' : 'OFF'); 
}

function clearSerial() { 
  document.getElementById('serialMonitor').innerHTML = ''; 
}

async function updateSerial() {
  try {
    const response = await fetch('/api/serial');
    const logs = await response.json();
    const monitor = document.getElementById('serialMonitor');
    monitor.innerHTML = logs.join('<br>');
    if (autoScroll) monitor.scrollTop = monitor.scrollHeight;
  } catch (e) { console.error('Serial update failed', e); }
}

initBoard();
setInterval(updateSerial, 2000);
setInterval(updatePinStates, 3000);
</script>
</body></html>)";
    
    return html;
}

#endif // ESP32_WEB_INTERFACE_H
