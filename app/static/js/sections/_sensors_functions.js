/**
 * Sensor Data Management for Entry v2
 * Handles sensor data display, CRUD operations, charts, and filtering
 */

// Global state
let sensorData = [];
let filteredData = [];
let sensorTypes = [];
let sensorChartV2 = null;  // Renamed to avoid collision with V1 sensors.js
let currentSensorType = '';
let currentTimeRange = '30d';  // Changed from 7d to 30d to capture more data
let currentChartType = 'line';  // Current chart type selection
let customStartDate = null;
let customEndDate = null;
let autoRefreshInterval = null;

/**
 * Initialize the sensor section
 */
async function initializeSensorSection() {
	try {
		// Load saved configuration first (must await to set currentSensorType before loading data)
		await loadSensorConfiguration();
		
		// Load sensor types for this entry type
		await loadSensorTypes();
        
		// Load sensor data
		await loadSensorDataV2();
        
		// Set up form handlers
		setupFormHandlers();
        
		// Initialize auto-refresh if enabled
		checkAutoRefresh();
        
	} catch (error) {
		console.error('Error initializing sensor section:', error);
		showNotification('Failed to initialize sensor section', 'error');
	}
}

/**
 * Load available sensor types for the entry type
 */
async function loadSensorTypes() {
	try {
		const response = await fetch(`/api/entry/${window.currentEntryId}/sensor-types`);
		if (!response.ok) throw new Error('Failed to load sensor types');
        
		const data = await response.json();
		sensorTypes = data.sensor_types || [];
        
		// Populate sensor type selectors
		try {
			populateSensorTypeSelect();
		} catch (selectError) {
			console.error('Error in populateSensorTypeSelect:', selectError);
		}
        
	} catch (error) {
		console.error('Error loading sensor types:', error);
		// Use defaults if API fails
		sensorTypes = ['Temperature', 'Humidity', 'Pressure', 'pH', 'Light', 'CO2'];
		populateSensorTypeSelect();
	}
}

/**
 * Populate sensor type dropdown
 */
function populateSensorTypeSelect() {
	const selects = ['sensorTypeSelect', 'addSensorType', 'defaultSensorType'];
    
	selects.forEach(selectId => {
		const select = document.getElementById(selectId);
		if (!select) {
			return;
		}
        
		// Clear existing options (keep first "All Sensors" option for main select and config)
		if (selectId === 'sensorTypeSelect' || selectId === 'defaultSensorType') {
			select.innerHTML = '<option value="">All Sensors</option>';
		} else {
			select.innerHTML = '<option value="">Select sensor type...</option>';
		}
        
		// Add sensor type options
		sensorTypes.forEach(type => {
			const option = document.createElement('option');
			option.value = type;
			option.textContent = type;
			select.appendChild(option);
		});
		
		// Restore saved value for both config and main dropdown
		// Use currentSensorType which was already loaded from database preferences
		if (selectId === 'defaultSensorType' || selectId === 'sensorTypeSelect') {
			if (currentSensorType) {
				select.value = currentSensorType;
				console.log(`🔧 populateSensorTypeSelect: Set ${selectId} to`, currentSensorType);
			}
		}
	});
}

/**
 * Get available chart types based on data type
 * @param {string} dataType - 'numeric' or 'categorical'
 * @returns {Array} - Array of available chart type objects {value, label}
 */
function getAvailableChartTypes(dataType) {
	// FIXED: Logic was inverted - now correctly showing options for each data type
	if (dataType === 'numeric') {
		// For numeric data, all chart types are available
		return [
			{ value: 'line', label: 'Line Chart' },
			{ value: 'bar', label: 'Bar Chart' },
			{ value: 'area', label: 'Area Chart' }
		];
	} else {
		// For categorical data: timeline, bar, and pie chart
		return [
			{ value: 'line', label: 'Timeline (Line)' },
			{ value: 'bar', label: 'Bar Chart' },
			{ value: 'pie', label: 'Pie Chart' }
		];
	}
}

/**
 * Update chart type selector based on current data type
 */
async function updateChartTypeSelector() {
	const chartTypeSelect = document.getElementById('chartTypeSelect');
	if (!chartTypeSelect) return;
	
	// Determine data type based on current selection
	let dataType = 'numeric'; // default
	
	if (currentSensorType && filteredData.length > 0) {
		// Single sensor selected - detect its type
		dataType = detectDataType(filteredData);
	} else if (!currentSensorType && sensorData.length > 0) {
		// "All Sensors" view - always numeric (categorical filtered out)
		dataType = 'numeric';
	}
	
	// Get available chart types for this data type
	const availableTypes = getAvailableChartTypes(dataType);
	
	// Try to load saved preference for this specific sensor type from JSON structure
	let preferredType = null;
	try {
		const response = await fetch('/api/user_preferences');
		if (response.ok) {
			const data = await response.json();
			const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
			const prefsJson = data.preferences?.[prefKey];
			
			if (prefsJson) {
				try {
					const prefs = JSON.parse(prefsJson);
					const chartTypes = prefs.chart_types || {};
					preferredType = currentSensorType ? chartTypes[currentSensorType] : null;
					
					console.log('📊 updateChartTypeSelector:', {
						currentSensorType,
						dataType,
						preferredType,
						availableTypes: availableTypes.map(t => t.value)
					});
				} catch (e) {
					console.error('Failed to parse preferences:', e);
				}
			}
		}
	} catch (error) {
		console.error('Failed to load chart type preference:', error);
	}
	
	// Repopulate dropdown
	chartTypeSelect.innerHTML = '';
	availableTypes.forEach(type => {
		const option = document.createElement('option');
		option.value = type.value;
		option.textContent = type.label;
		chartTypeSelect.appendChild(option);
	});
	
	// Priority: saved preference > current selection > first available
	const currentSelection = chartTypeSelect.value;
	
	if (preferredType && availableTypes.some(t => t.value === preferredType)) {
		// Use saved preference if valid
		chartTypeSelect.value = preferredType;
		currentChartType = preferredType;
	} else if (availableTypes.some(t => t.value === currentSelection)) {
		// Keep current if still valid
		chartTypeSelect.value = currentSelection;
		currentChartType = currentSelection;
	} else {
		// Fall back to first available
		chartTypeSelect.value = availableTypes[0].value;
		currentChartType = availableTypes[0].value;
	}
}

/**
 * Filter sensor data based on current filters (V2 version)
 */
function filterSensorDataV2(data) {
	let filtered = data;
	
	// Filter by sensor type
	if (currentSensorType) {
		filtered = filtered.filter(r => r.sensor_type === currentSensorType);
	}
	
	// Filter by time range
	const timeRange = getTimeRangeParams();
	if (timeRange.start) {
		const startTime = new Date(timeRange.start).getTime();
		filtered = filtered.filter(r => new Date(r.recorded_at).getTime() >= startTime);
	}
	if (timeRange.end) {
		const endTime = new Date(timeRange.end).getTime();
		filtered = filtered.filter(r => new Date(r.recorded_at).getTime() <= endTime);
	}
	
	return filtered;
}

/**
 * Load sensor data for the current entry
 */
async function loadSensorDataV2() {
	showLoading(true);
    
	try {
		// Use the existing V1 API endpoint that works
		const response = await fetch(`/api/entries/${window.currentEntryId}/sensor_data`);
		if (!response.ok) throw new Error('Failed to load sensor data');
        
		const data = await response.json();
		
		// V1 API returns array directly, not wrapped in {readings: [...]}
		sensorData = data || [];
		
		// Apply client-side filtering
		try {
			filteredData = filterSensorDataV2(sensorData);
		} catch (err) {
			console.error('Error in filterSensorDataV2:', err);
			filteredData = sensorData; // Fallback to unfiltered
		}
        
		// Update UI
		updateDisplay();
        
	} catch (error) {
		console.error('Error loading sensor data:', error);
		showNotification('Failed to load sensor data', 'error');
		showNoData();
	} finally {
		showLoading(false);
	}
}

/**
 * Get time range parameters based on current selection
 */
function getTimeRangeParams() {
	const now = new Date();
	let start, end;
    
	switch (currentTimeRange) {
		case '24h':
			start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
			break;
		case '7d':
			start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
			break;
		case '30d':
			start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
			break;
		case '90d':
			start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
			break;
		case 'custom':
			start = customStartDate ? new Date(customStartDate) : null;
			end = customEndDate ? new Date(customEndDate) : null;
			break;
	}
    
	end = end || now;
    
	return {
		start: start ? start.toISOString() : null,
		end: end.toISOString()
	};
}

/**
 * Update all display elements with current data
 */
async function updateDisplay() {
	if (filteredData.length === 0) {
		showNoData();
		return;
	}
    
	// Hide no data message
	document.getElementById('noDataMessage').style.display = 'none';
    
	// Update chart type selector based on data type (await since it loads preferences)
	await updateChartTypeSelector();
	
	// Update statistics
	updateStatistics();
    
	// Update chart (await since it's async now)
	await updateChart();
    
	// Update table
	updateTable();
    
	// Update device list
	updateDeviceList();
}

/**
 * Update statistics panel
 */
function updateStatistics() {
	const statsPanel = document.getElementById('sensorStats');
	
	// Hide stats if no data or "All Sensors" selected (mixed units don't make sense)
	if (filteredData.length === 0 || !currentSensorType) {
		if (statsPanel) statsPanel.style.display = 'none';
		return;
	}
    
	// Detect data type
	const dataType = detectDataType(filteredData);
	
	// For categorical data, show different statistics (state distribution)
	if (dataType === 'categorical') {
		renderCategoricalStatistics();
		return;
	}
    
	if (statsPanel) statsPanel.style.display = 'flex';
    
	// Calculate statistics - filter out any non-numeric values
	const values = filteredData
		.map(d => parseFloat(d.value))
		.filter(v => !isNaN(v));
	
	if (values.length === 0) {
		document.getElementById('sensorStats').style.display = 'none';
		return;
	}
	
	const current = values[0];  // V1 API returns newest first
	const average = values.reduce((a, b) => a + b, 0) / values.length;
	const max = Math.max(...values);
	const min = Math.min(...values);
    
	// Get unit - could be from metadata or infer from sensor type
	const unit = filteredData[0].unit || '';
    
	// Update display with proper formatting
	document.getElementById('statCurrent').textContent = isNaN(current) ? 'N/A' : current.toFixed(2);
	document.getElementById('statCurrentUnit').textContent = unit;
	document.getElementById('statAverage').textContent = isNaN(average) ? 'N/A' : average.toFixed(2);
	document.getElementById('statAverageUnit').textContent = unit;
	document.getElementById('statMax').textContent = isNaN(max) ? 'N/A' : max.toFixed(2);
	document.getElementById('statMaxUnit').textContent = unit;
	document.getElementById('statMin').textContent = isNaN(min) ? 'N/A' : min.toFixed(2);
	document.getElementById('statMinUnit').textContent = unit;
}

/**
 * Render statistics for categorical (text-based) data
 */
function renderCategoricalStatistics() {
	const statsPanel = document.getElementById('sensorStats');
	if (!statsPanel) return;
	
	// Count occurrences of each state
	const stateCounts = {};
	let totalReadings = filteredData.length;
	
	filteredData.forEach(reading => {
		const state = String(reading.value).toLowerCase().trim();
		stateCounts[state] = (stateCounts[state] || 0) + 1;
	});
	
	// Get most common state
	const sortedStates = Object.entries(stateCounts).sort((a, b) => b[1] - a[1]);
	const currentState = filteredData[0]?.value || 'N/A';
	const mostCommonState = sortedStates[0]?.[0] || 'N/A';
	const stateCount = Object.keys(stateCounts).length;
	const changeCount = filteredData.length - 1; // Number of state changes
	
	// Update stats panel with categorical data
	statsPanel.style.display = 'flex';
	document.getElementById('statCurrent').textContent = currentState;
	document.getElementById('statCurrentUnit').textContent = '(now)';
	document.getElementById('statAverage').textContent = mostCommonState;
	document.getElementById('statAverageUnit').textContent = '(most common)';
	document.getElementById('statMax').textContent = stateCount;
	document.getElementById('statMaxUnit').textContent = 'unique states';
	document.getElementById('statMin').textContent = changeCount;
	document.getElementById('statMinUnit').textContent = 'changes';
}

/**
 * Update chart with current data
 */
async function updateChart() {
	const chartContainer = document.getElementById('chartContainer');
	const canvas = document.getElementById('sensorChart');
    
	if (filteredData.length === 0) {
		chartContainer.style.display = 'none';
		return;
	}
    
	chartContainer.style.display = 'block';
    
	// Destroy existing chart
	if (sensorChartV2) {
		sensorChartV2.destroy();
	}
	
	// Use the current chart type from global state
	const chartType = currentChartType;
	
	// When viewing a specific sensor type, detect if it's numeric or categorical
	// When viewing "All Sensors", only show numeric sensors to avoid mixing types
	if (currentSensorType) {
		// Single sensor type selected - detect its data type
		const dataType = detectDataType(filteredData);
		
		// For categorical data, force bar chart or timeline visualization
		if (dataType === 'categorical') {
			renderCategoricalChart(filteredData, chartType);
			return;
		}
	} else {
		// "All Sensors" selected - filter to only numeric sensors
		// Group by sensor type and check each type
		const sensorTypeGroups = {};
		filteredData.forEach(reading => {
			const type = reading.sensor_type;
			if (!sensorTypeGroups[type]) {
				sensorTypeGroups[type] = [];
			}
			sensorTypeGroups[type].push(reading);
		});
		
		// Filter out categorical sensor types
		const numericData = [];
		Object.entries(sensorTypeGroups).forEach(([type, readings]) => {
			const dataType = detectDataType(readings);
			if (dataType === 'numeric') {
				numericData.push(...readings);
			}
		});
		
		// Use only numeric data
		filteredData = numericData;
		
		if (filteredData.length === 0) {
			chartContainer.innerHTML = '<p class="text-muted text-center py-4">No numeric sensor data available. Select a specific sensor type to view categorical data.</p>';
			return;
		}
	}
	
	// Group numeric data by sensor type (simplified to match original sensors.js)
	const datasets = {};
	filteredData.forEach(reading => {
		const type = reading.sensor_type;
		if (!datasets[type]) {
			// Set background color based on chart type
			let bgColor;
			if (chartType === 'bar') {
				bgColor = getColorForSensorType(type, 0.7);
			} else if (chartType === 'area') {
				bgColor = getColorForSensorType(type, 0.2); // Transparent for area fill
			} else {
				bgColor = 'transparent'; // No fill for line charts
			}
			
			datasets[type] = {
				label: `${type} ${reading.unit || ''}`.trim(),
				data: [],
				borderColor: getColorForSensorType(type),
				backgroundColor: bgColor,
				borderWidth: 2,
				pointRadius: 3,
				pointHoverRadius: 5,
				fill: chartType === 'area' // Only fill for area charts
			};
		}
		datasets[type].data.push({
			x: new Date(reading.recorded_at),
			y: parseFloat(reading.value)
		});
	});
    
	// Create chart with saved chart type preference
	// Note: 'area' is actually a line chart with fill=true, so map it to 'line'
	const actualChartType = (chartType === 'area') ? 'line' : chartType;
	
	const ctx = canvas.getContext('2d');
	sensorChartV2 = new Chart(ctx, {
		type: actualChartType,
		data: {
			datasets: Object.values(datasets)
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: 'index',
				intersect: false,
			},
			plugins: {
				legend: {
					display: true,
					position: 'top',
				},
				tooltip: {
					callbacks: {
						label: function(context) {
							return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
						}
					}
				},
				zoom: {
					enabled: true,
					mode: 'x',
				}
			},
			scales: {
				x: {
					type: 'time',
					time: {
						unit: getTimeUnit(),
						displayFormats: {
							hour: 'MMM d, HH:mm',
							day: 'MMM d',
							week: 'MMM d',
							month: 'MMM yyyy'
						}
					},
					title: {
						display: true,
						text: 'Time'
					}
				},
				y: {
					beginAtZero: false,
					title: {
						display: true,
						text: 'Value'
					}
				}
			}
		}
	});
}

/**
 * Get appropriate time unit for chart based on time range
 */
function getTimeUnit() {
	switch (currentTimeRange) {
		case '24h': return 'hour';
		case '7d': return 'day';
		case '30d': return 'day';
		case '90d': return 'week';
		default: return 'day';
	}
}

/**
 * Get color for sensor type (consistent colors)
 */
function getColorForSensorType(type, alpha = 1) {
	const colors = {
		'Temperature': `rgba(255, 99, 132, ${alpha})`,
		'Humidity': `rgba(54, 162, 235, ${alpha})`,
		'Pressure': `rgba(255, 206, 86, ${alpha})`,
		'pH': `rgba(75, 192, 192, ${alpha})`,
		'Light': `rgba(255, 159, 64, ${alpha})`,
		'CO2': `rgba(153, 102, 255, ${alpha})`,
	};
    
	return colors[type] || `rgba(201, 203, 207, ${alpha})`;
}

/**
 * Detect if sensor data is numeric or categorical (text-based)
 */
function detectDataType(data) {
	if (!data || data.length === 0) return 'numeric';
	
	// Sample first few readings to determine type
	const sample = data.slice(0, Math.min(20, data.length));
	let numericCount = 0;
	let textCount = 0;
	
	for (const reading of sample) {
		const value = String(reading.value).trim();
		const numValue = parseFloat(value);
		
		// Check if value is numeric (possibly with units)
		// parseFloat will extract the numeric part from strings like "26.3125°C", "100ml", etc.
		if (!isNaN(numValue) && isFinite(numValue)) {
			// If parseFloat succeeds, it's numeric data (with or without units)
			// Examples: "26.3125", "26.3125°C", "100ml", "5.5kg" are all numeric
			numericCount++;
		} else {
			// parseFloat failed completely - it's pure text
			// Examples: "on", "off", "open", "closed", "active"
			if (value.length > 0) {
				textCount++;
			}
		}
	}
	
	// If any text values found, treat as categorical
	// This ensures "on"/"off" is categorical even if mixed with numbers
	if (textCount > 0) {
		return 'categorical';
	}
	
	// Otherwise numeric
	return 'numeric';
}

/**
 * Render chart for categorical (text-based) sensor data
 * E.g., relay states: "on"/"off", door states: "open"/"closed", etc.
 */
function renderCategoricalChart(data, preferredChartType) {
	// If pie chart requested, use specialized pie chart function
	if (preferredChartType === 'pie') {
		renderCategoricalPieChart(data);
		return;
	}
	
	const canvas = document.getElementById('sensorChart');
	const ctx = canvas.getContext('2d');
	
	// Get unique categorical values across all data and build mapping
	const categoryMap = {};
	const categoryArray = [];
	
	// First pass: collect unique values
	data.forEach(reading => {
		const value = String(reading.value).toLowerCase().trim();
		if (!categoryMap.hasOwnProperty(value)) {
			categoryMap[value] = categoryArray.length;
			categoryArray.push(value);
		}
	});
	
	// Create dataset configuration based on chart type
	const isBarChart = preferredChartType === 'bar';
	
	const dataset = {
		label: data[0]?.sensor_type || 'Sensor States',
		data: [],
		showLine: !isBarChart, // Show line for timeline, hide for bar
		stepped: !isBarChart ? 'after' : false, // Stepped line for timeline only
		borderColor: 'rgba(108, 117, 125, 0.5)', // Gray line
		borderWidth: 2,
		pointRadius: isBarChart ? 6 : 8, // Slightly smaller points for bar chart
		pointHoverRadius: isBarChart ? 8 : 12,
		pointBackgroundColor: [],
		pointBorderColor: [],
		pointBorderWidth: 2,
		fill: false
	};
	
	// Add each reading as a point
	data.forEach(reading => {
		const value = String(reading.value).toLowerCase().trim();
		const yPosition = categoryMap[value];
		const pointColor = getCategoryColor(reading.value, 1);
		
		dataset.pointBackgroundColor.push(pointColor);
		dataset.pointBorderColor.push(pointColor);
		
		dataset.data.push({
			x: new Date(reading.recorded_at),
			y: yPosition,
			originalValue: reading.value,
			timestamp: reading.recorded_at
		});
	});
	
	// Add a plugin to draw colored background zones for each state row
	const stateBackgroundPlugin = {
		id: 'stateBackgrounds',
		beforeDraw: (chart) => {
			const ctx = chart.ctx;
			const chartArea = chart.chartArea;
			const yScale = chart.scales.y;
			
			// Draw colored background for each state row
			categoryArray.forEach((state, index) => {
				const yTop = yScale.getPixelForValue(index + 0.4);
				const yBottom = yScale.getPixelForValue(index - 0.4);
				const stateColor = getCategoryColor(state, 0.15);
				
				ctx.fillStyle = stateColor;
				ctx.fillRect(chartArea.left, yTop, chartArea.right - chartArea.left, yBottom - yTop);
				
				// Draw border line between states
				if (index < categoryArray.length - 1) {
					const borderY = yScale.getPixelForValue(index + 0.5);
					ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
					ctx.lineWidth = 2;
					ctx.beginPath();
					ctx.moveTo(chartArea.left, borderY);
					ctx.lineTo(chartArea.right, borderY);
					ctx.stroke();
				}
			});
		}
	};
	
	// Create chart as scatter plot
	sensorChartV2 = new Chart(ctx, {
		type: 'scatter',
		data: {
			datasets: [dataset]
		},
		plugins: [stateBackgroundPlugin],
		options: {
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: 'point',
				intersect: false,
			},
			plugins: {
				legend: {
					display: true,
					position: 'top',
				},
				tooltip: {
					callbacks: {
						title: function(context) {
							const point = context[0];
							const timestamp = new Date(point.raw.timestamp);
							return timestamp.toLocaleString();
						},
						label: function(context) {
							const originalValue = context.raw.originalValue;
							return `State: ${originalValue.toUpperCase()}`;
						},
						afterLabel: function(context) {
							return `Reading #${context.dataIndex + 1}`;
						},
						labelColor: function(context) {
							const originalValue = context.raw.originalValue;
							return {
								borderColor: getCategoryColor(originalValue, 1),
								backgroundColor: getCategoryColor(originalValue, 0.8),
								borderWidth: 2
							};
						}
					}
				},
				title: {
					display: true,
					text: 'State Changes Over Time',
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			},
			scales: {
				x: {
					type: 'time',
					time: {
						unit: getTimeUnit(),
						displayFormats: {
							hour: 'MMM d, HH:mm',
							day: 'MMM d',
							week: 'MMM d',
							month: 'MMM yyyy'
						}
					},
					title: {
						display: true,
						text: 'Time'
					}
				},
				y: {
					type: 'linear',
					min: -0.5,
					max: categoryArray.length - 0.5,
					ticks: {
						stepSize: 1,
						callback: function(value) {
							// Only show labels for actual state positions (integers)
							if (Number.isInteger(value) && value >= 0 && value < categoryArray.length) {
								const label = categoryArray[value];
								return '  ' + label.toUpperCase() + '  ';
							}
							return '';
						},
						color: function(context) {
							// Color the Y-axis labels to match their state
							const value = context.tick.value;
							if (Number.isInteger(value) && value >= 0 && value < categoryArray.length) {
								const label = categoryArray[value];
								return getCategoryColor(label, 1);
							}
							return '#666';
						},
						font: {
							weight: 'bold',
							size: 14
						},
						padding: 8
					},
					title: {
						display: true,
						text: 'State',
						font: {
							size: 14,
							weight: 'bold'
						}
					},
					grid: {
						drawOnChartArea: false, // Let the plugin handle backgrounds
						display: true,
						color: 'rgba(0, 0, 0, 0.1)',
						lineWidth: 1
					}
				}
			}
		}
	});
}

/**
 * Render pie chart for categorical data showing distribution of states
 */
function renderCategoricalPieChart(data) {
	const canvas = document.getElementById('sensorChart');
	const ctx = canvas.getContext('2d');
	
	// Count occurrences of each categorical value
	const categoryCount = {};
	data.forEach(reading => {
		const value = String(reading.value).toLowerCase().trim();
		categoryCount[value] = (categoryCount[value] || 0) + 1;
	});
	
	// Prepare data for pie chart
	const labels = Object.keys(categoryCount);
	const counts = Object.values(categoryCount);
	const colors = labels.map(label => getCategoryColor(label, 0.8));
	const borderColors = labels.map(label => getCategoryColor(label, 1));
	
	// Calculate percentages for display
	const total = counts.reduce((sum, count) => sum + count, 0);
	const percentages = counts.map(count => ((count / total) * 100).toFixed(1));
	
	// Create pie chart
	sensorChartV2 = new Chart(ctx, {
		type: 'pie',
		data: {
			labels: labels.map(label => label.toUpperCase()),
			datasets: [{
				data: counts,
				backgroundColor: colors,
				borderColor: borderColors,
				borderWidth: 2
			}]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					display: true,
					position: 'right',
					labels: {
						font: {
							size: 14
						},
						generateLabels: function(chart) {
							const data = chart.data;
							if (data.labels.length && data.datasets.length) {
								return data.labels.map((label, i) => {
									const value = data.datasets[0].data[i];
									const percentage = percentages[i];
									return {
										text: `${label}: ${value} (${percentage}%)`,
										fillStyle: data.datasets[0].backgroundColor[i],
										strokeStyle: data.datasets[0].borderColor[i],
										lineWidth: 2,
										hidden: false,
										index: i
									};
								});
							}
							return [];
						}
					}
				},
				tooltip: {
					callbacks: {
						label: function(context) {
							const label = context.label || '';
							const value = context.parsed || 0;
							const percentage = percentages[context.dataIndex];
							return `${label}: ${value} readings (${percentage}%)`;
						}
					}
				},
				title: {
					display: true,
					text: `${data[0]?.sensor_type || 'Sensor'} State Distribution`,
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			}
		}
	});
}

/**
 * Get color for categorical value
 */
function getCategoryColor(value, alpha = 1) {
	const normalizedValue = String(value).toLowerCase().trim();
	
	// Common state colors
	const stateColors = {
		// Binary states
		'on': `rgba(40, 167, 69, ${alpha})`,      // green
		'off': `rgba(220, 53, 69, ${alpha})`,     // red
		'true': `rgba(40, 167, 69, ${alpha})`,
		'false': `rgba(220, 53, 69, ${alpha})`,
		'1': `rgba(40, 167, 69, ${alpha})`,
		'0': `rgba(220, 53, 69, ${alpha})`,
		'yes': `rgba(40, 167, 69, ${alpha})`,
		'no': `rgba(220, 53, 69, ${alpha})`,
		
		// Door/lock states
		'open': `rgba(255, 193, 7, ${alpha})`,    // yellow/warning
		'closed': `rgba(40, 167, 69, ${alpha})`,  // green
		'locked': `rgba(40, 167, 69, ${alpha})`,
		'unlocked': `rgba(255, 193, 7, ${alpha})`,
		
		// Activity states
		'active': `rgba(40, 167, 69, ${alpha})`,
		'inactive': `rgba(108, 117, 125, ${alpha})`, // gray
		'idle': `rgba(108, 117, 125, ${alpha})`,
		'running': `rgba(40, 167, 69, ${alpha})`,
		'stopped': `rgba(220, 53, 69, ${alpha})`,
		
		// Motion/presence
		'detected': `rgba(255, 193, 7, ${alpha})`,
		'clear': `rgba(40, 167, 69, ${alpha})`,
		'motion': `rgba(255, 193, 7, ${alpha})`,
		'no motion': `rgba(108, 117, 125, ${alpha})`,
		
		// Alert states
		'ok': `rgba(40, 167, 69, ${alpha})`,
		'warning': `rgba(255, 193, 7, ${alpha})`,
		'error': `rgba(220, 53, 69, ${alpha})`,
		'critical': `rgba(220, 53, 69, ${alpha})`,
		'normal': `rgba(40, 167, 69, ${alpha})`,
	};
	
	return stateColors[normalizedValue] || `rgba(201, 203, 207, ${alpha})`;
}

/**
 * Update data table
 */
function updateTable(page = 1) {
	const tbody = document.getElementById('sensorTableBody');
	if (!tbody) return;
    
	tbody.innerHTML = '';
    
	// Calculate pagination
	const start = (page - 1) * window.itemsPerPage;
	const end = start + window.itemsPerPage;
	const paginatedData = filteredData.slice(start, end);
    
	// Populate table rows
	paginatedData.forEach(reading => {
		const row = tbody.insertRow();
		
		// Format value based on type (numeric vs categorical)
		let displayValue;
		const numericValue = parseFloat(reading.value);
		if (!isNaN(numericValue) && isFinite(numericValue)) {
			// Numeric value - show with 2 decimal places
			displayValue = `<strong>${numericValue.toFixed(2)}</strong> ${reading.unit || ''}`;
		} else {
			// Categorical/text value - show as badge with color
			const categoryColor = getCategoryColor(reading.value, 1);
			displayValue = `<span class="badge" style="background-color: ${categoryColor}">${reading.value}</span>`;
		}
		
		row.innerHTML = `
			<td>${formatTimestamp(reading.recorded_at)}</td>
			<td><span class="badge bg-secondary">${reading.sensor_type}</span></td>
			<td>${displayValue}</td>
			<td>
				<button class="btn btn-sm btn-outline-primary" onclick="editSensorReading(${reading.id})" title="Edit">
					<i class="fas fa-edit"></i>
				</button>
				<button class="btn btn-sm btn-outline-danger" onclick="deleteSensorReadingConfirm(${reading.id})" title="Delete">
					<i class="fas fa-trash"></i>
				</button>
			</td>
		`;
	});
    
	// Update pagination
	updatePagination(page, Math.ceil(filteredData.length / window.itemsPerPage));
}

/**
 * Update pagination controls
 */
function updatePagination(currentPage, totalPages) {
	const pagination = document.getElementById('sensorPagination');
	if (!pagination) return;
    
	pagination.innerHTML = '';
    
	if (totalPages <= 1) return;
    
	// Previous button
	const prevLi = document.createElement('li');
	prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
	prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Previous</a>`;
	pagination.appendChild(prevLi);
    
	// Page numbers
	for (let i = 1; i <= totalPages; i++) {
		if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
			const li = document.createElement('li');
			li.className = `page-item ${i === currentPage ? 'active' : ''}`;
			li.innerHTML = `<a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>`;
			pagination.appendChild(li);
		} else if (i === currentPage - 3 || i === currentPage + 3) {
			const li = document.createElement('li');
			li.className = 'page-item disabled';
			li.innerHTML = '<span class="page-link">...</span>';
			pagination.appendChild(li);
		}
	}
    
	// Next button
	const nextLi = document.createElement('li');
	nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
	nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>`;
	pagination.appendChild(nextLi);
}

/**
 * Change table page
 */
function changePage(page) {
	window.currentPage = page;
	updateTable(page);
}

/**
 * Update device list
 */
function updateDeviceList() {
	const deviceList = document.getElementById('deviceList');
	if (!deviceList) return;
    
	// Get unique devices/sources
	const sources = {};
	filteredData.forEach(reading => {
		const key = reading.source_id || reading.source_type;
		if (!sources[key]) {
			sources[key] = {
				type: reading.source_type,
				id: reading.source_id,
				count: 0,
				lastSeen: reading.recorded_at
			};
		}
		sources[key].count++;
		if (new Date(reading.recorded_at) > new Date(sources[key].lastSeen)) {
			sources[key].lastSeen = reading.recorded_at;
		}
	});
    
	// Build device list HTML
	const html = Object.entries(sources).map(([key, source]) => `
		<div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
			<div>
				<i class="fas fa-${source.type === 'device' ? 'microchip' : source.type === 'api' ? 'cloud' : 'user'} me-2"></i>
				<strong>${source.id || source.type}</strong>
			</div>
			<div class="text-muted">
				<span class="badge bg-secondary">${source.count} readings</span>
				<small class="ms-2">Last: ${formatTimestamp(source.lastSeen)}</small>
			</div>
		</div>
	`).join('');
    
	deviceList.innerHTML = html || '<p class="text-muted mb-0">No devices found</p>';
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
	const date = new Date(timestamp);
	const now = new Date();
	const diffMs = now - date;
	const diffMins = Math.floor(diffMs / 60000);
	const diffHours = Math.floor(diffMs / 3600000);
	const diffDays = Math.floor(diffMs / 86400000);
    
	if (diffMins < 1) return 'Just now';
	if (diffMins < 60) return `${diffMins}m ago`;
	if (diffHours < 24) return `${diffHours}h ago`;
	if (diffDays < 7) return `${diffDays}d ago`;
    
	return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
	const loading = document.getElementById('loadingIndicator');
	const noData = document.getElementById('noDataMessage');
	const chartContainer = document.getElementById('chartContainer');
	const stats = document.getElementById('sensorStats');
    
	if (show) {
		loading.style.display = 'block';
		noData.style.display = 'none';
		chartContainer.style.display = 'none';
		stats.style.display = 'none';
	} else {
		loading.style.display = 'none';
	}
}

/**
 * Show no data message
 */
function showNoData() {
	document.getElementById('noDataMessage').style.display = 'block';
	document.getElementById('chartContainer').style.display = 'none';
	document.getElementById('sensorStats').style.display = 'none';
	document.getElementById('sensorDataTable').style.display = 'none';
}

/**
 * Event Handlers
 */

function onSensorTypeChange() {
	currentSensorType = document.getElementById('sensorTypeSelect').value;
	loadSensorData();
}

function onTimeRangeChange() {
	const select = document.getElementById('timeRangeSelect');
	currentTimeRange = select.value;
    
	// Show/hide custom date range inputs
	const customDateRange = document.getElementById('customDateRange');
	if (currentTimeRange === 'custom') {
		customDateRange.style.display = 'flex';
		// Set default values
		const now = new Date();
		const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
		document.getElementById('startDate').value = weekAgo.toISOString().slice(0, 16);
		document.getElementById('endDate').value = now.toISOString().slice(0, 16);
	} else {
		customDateRange.style.display = 'none';
		loadSensorData();
	}
}

function onCustomDateChange() {
	customStartDate = document.getElementById('startDate').value;
	customEndDate = document.getElementById('endDate').value;
	loadSensorData();
}

function refreshSensorData() {
	loadSensorData();
	showBanner('Sensor data refreshed', 'success');
}

function toggleDataTable() {
	const tableSection = document.getElementById('sensorDataTableSection');
	const showButton = document.getElementById('showTableButton');
    
	if (tableSection.style.display === 'none') {
		// Show the table section
		tableSection.style.display = 'block';
		showButton.style.display = 'none';
		updateTable(1);
	} else {
		// Hide the table section
		tableSection.style.display = 'none';
		showButton.style.display = 'block';
	}
}

/**
 * Setup form handlers
 */
function setupFormHandlers() {
	// Sensor type filter
	const sensorTypeSelect = document.getElementById('sensorTypeSelect');
	if (sensorTypeSelect) {
		sensorTypeSelect.addEventListener('change', async function() {
			currentSensorType = this.value;
			await loadSensorDataV2();
		});
	}
	
	// Time range filter
	const timeRangeSelect = document.getElementById('timeRangeSelect');
	if (timeRangeSelect) {
		timeRangeSelect.addEventListener('change', async function() {
			currentTimeRange = this.value;
			
			// Show/hide custom date inputs
			const customDates = document.getElementById('customDateRange');
			if (customDates) {
				customDates.style.display = this.value === 'custom' ? 'block' : 'none';
			}
			
			if (this.value !== 'custom') {
				await loadSensorDataV2();
			}
		});
	}
	
	// Chart type filter
	const chartTypeSelect = document.getElementById('chartTypeSelect');
	if (chartTypeSelect) {
		chartTypeSelect.addEventListener('change', async function() {
			currentChartType = this.value;
			
			// Save preference per sensor type using JSON structure
			try {
				// Load existing preferences
				const response = await fetch('/api/user_preferences');
				let prefs = {};
				if (response.ok) {
					const data = await response.json();
					const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
					const existing = data.preferences?.[prefKey];
					if (existing) {
						try {
							prefs = JSON.parse(existing);
						} catch (e) {
							console.error('Failed to parse existing preferences:', e);
						}
					}
				}
				
				// Update chart type for current sensor
				if (!prefs.chart_types) prefs.chart_types = {};
				if (currentSensorType) {
					prefs.chart_types[currentSensorType] = currentChartType;
				}
				prefs.saved_at = new Date().toISOString();
				
				// Save back
				const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
				await fetch(`/api/user_preferences/${prefKey}`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ value: JSON.stringify(prefs) })
				});
			} catch (error) {
				console.error('Failed to save chart type preference:', error);
			}
			
			// Re-render chart with new type
			await updateChart();
		});
	}
	
	// Apply custom date range button
	const applyCustomBtn = document.getElementById('applyCustomRange');
	if (applyCustomBtn) {
		applyCustomBtn.addEventListener('click', async function() {
			customStartDate = document.getElementById('customStartDate').value;
			customEndDate = document.getElementById('customEndDate').value;
			await loadSensorDataV2();
		});
	}
	
	// Refresh button
	const refreshBtn = document.getElementById('refreshSensorData');
	if (refreshBtn) {
		refreshBtn.addEventListener('click', async function() {
			await loadSensorDataV2();
		});
	}
	
	// Add sensor data form
	const addForm = document.getElementById('addSensorDataForm');
	if (addForm) {
		addForm.addEventListener('submit', async function(e) {
			e.preventDefault();
			await addSensorReading();
		});
	}
    
	// Edit sensor data form
	const editForm = document.getElementById('editSensorDataForm');
	if (editForm) {
		editForm.addEventListener('submit', async function(e) {
			e.preventDefault();
			await updateSensorReading();
		});
	}
    
	// Source type change
	const addSource = document.getElementById('addSource');
	if (addSource) {
		addSource.addEventListener('change', function() {
			const deviceSection = document.getElementById('deviceSourceSection');
			if (deviceSection) deviceSection.style.display = this.value === 'device' ? 'block' : 'none';
		});
	}
	
	// Modal sensor type change - update chart type dropdown to show saved preference
	const modalSensorTypeSelect = document.getElementById('defaultSensorType');
	if (modalSensorTypeSelect) {
		modalSensorTypeSelect.addEventListener('change', async function() {
			const selectedSensorType = this.value;
			const chartTypeSelect = document.getElementById('defaultChartType');
			
			if (!chartTypeSelect) return;
			
			// Load saved preference for this sensor type from JSON structure
			try {
				const response = await fetch('/api/user_preferences');
				if (response.ok) {
					const data = await response.json();
					const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
					const prefsJson = data.preferences?.[prefKey];
					
					let savedChartType = 'line'; // default
					if (prefsJson) {
						try {
							const prefs = JSON.parse(prefsJson);
							const chartTypes = prefs.chart_types || {};
							savedChartType = chartTypes[selectedSensorType] || 'line';
						} catch (e) {
							console.error('Failed to parse preferences:', e);
						}
					}
					
					chartTypeSelect.value = savedChartType;
				}
			} catch (error) {
				console.error('Failed to load chart type preference:', error);
			}
		});
	}
}

/**
 * Add new sensor reading
 */
async function addSensorReading() {
	try {
		// Get form values
		const sensorType = document.getElementById('addNewSensorType').value || document.getElementById('addSensorType').value;
		const value = document.getElementById('addValue').value;
		const unit = document.getElementById('addUnit').value;
		const timestamp = document.getElementById('addTimestamp').value;
		const source = document.getElementById('addSource').value;
		const deviceId = document.getElementById('addDeviceId').value;
		const notes = document.getElementById('addNotes').value;
        
		if (!sensorType || !value) {
			showNotification('Please fill in all required fields', 'error');
			return;
		}
        
		// Build request payload
		const payload = {
			sensor_type: sensorType,
			value: value,
			unit: unit,
			entry_ids: [window.currentEntryId],
			recorded_at: timestamp || new Date().toISOString(),
			source_type: source,
			source_id: deviceId || null,
			metadata: notes ? { notes: notes } : {}
		};
        
		// Submit to API
		const response = await fetch('/api/shared_sensor_data', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
        
		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to add sensor reading');
		}
        
		// Close modal and refresh
		const addModalEl = document.getElementById('addSensorDataModal');
		if (addModalEl) {
			const addModal = bootstrap.Modal.getInstance(addModalEl) || new bootstrap.Modal(addModalEl);
			addModal.hide();
		}
		const addForm = document.getElementById('addSensorDataForm');
		if (addForm) addForm.reset();
        
		await loadSensorData();
		showBanner('Sensor reading added successfully', 'success');
        
	} catch (error) {
		console.error('Error adding sensor reading:', error);
		showBanner(error.message, 'error');
	}
}

/**
 * Edit sensor reading
 */
async function editSensorReading(id) {
	// Find reading in data
	const reading = filteredData.find(r => r.id === id);
	if (!reading) return;
    
	// Populate edit form
	const editId = document.getElementById('editSensorId');
	if (editId) editId.value = reading.id;
	const editType = document.getElementById('editSensorType');
	if (editType) editType.value = reading.sensor_type;
	const editValue = document.getElementById('editValue');
	if (editValue) editValue.value = reading.value;
	const editUnit = document.getElementById('editUnit');
	if (editUnit) editUnit.value = reading.unit || '';
    
	// Convert timestamp to local datetime format
	const date = new Date(reading.recorded_at);
	const editTimestamp = document.getElementById('editTimestamp');
	if (editTimestamp) editTimestamp.value = date.toISOString().slice(0, 16);
    
	const editNotes = document.getElementById('editNotes');
	if (editNotes) editNotes.value = reading.metadata?.notes || '';
    
	// Show modal
	const editModalEl = document.getElementById('editSensorDataModal');
	if (editModalEl) new bootstrap.Modal(editModalEl).show();
}

/**
 * Update sensor reading
 */
async function updateSensorReading() {
	try {
		const id = document.getElementById('editSensorId').value;
		const value = document.getElementById('editValue').value;
		const unit = document.getElementById('editUnit').value;
		const timestamp = document.getElementById('editTimestamp').value;
		const notes = document.getElementById('editNotes').value;
        
		const payload = {
			value: value,
			unit: unit,
			recorded_at: new Date(timestamp).toISOString(),
			metadata: notes ? { notes: notes } : {}
		};
        
		const response = await fetch(`/api/shared_sensor_data/${id}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
        
		if (!response.ok) throw new Error('Failed to update sensor reading');
        
		// Close modal and refresh
		const editModalEl = document.getElementById('editSensorDataModal');
		if (editModalEl) {
			const editModal = bootstrap.Modal.getInstance(editModalEl);
			if (editModal) editModal.hide();
		}
		await loadSensorData();
		showBanner('Sensor reading updated successfully', 'success');
        
	} catch (error) {
		console.error('Error updating sensor reading:', error);
		showBanner(error.message, 'error');
	}
}

/**
 * Delete sensor reading with confirmation
 */
function deleteSensorReadingConfirm(id) {
	if (confirm('Are you sure you want to delete this sensor reading? This action cannot be undone.')) {
		deleteSensorReading(id);
	}
}

/**
 * Delete sensor reading
 */
async function deleteSensorReading(id = null) {
	try {
		// If no ID provided, get from edit form
		if (!id) {
			id = document.getElementById('editSensorId').value;
		}
        
		// Use V1 API endpoint for delete
		const response = await fetch(`/api/sensor_data/${id}`, {
			method: 'DELETE'
		});
        
		if (!response.ok) throw new Error('Failed to delete sensor reading');
        
		// Close modal if open and refresh
		const editModal = bootstrap.Modal.getInstance(document.getElementById('editSensorDataModal'));
		if (editModal) editModal.hide();
        
		await loadSensorDataV2();
		showBanner('Sensor reading deleted successfully', 'success');
        
	} catch (error) {
		console.error('Error deleting sensor reading:', error);
		showBanner(error.message, 'error');
	}
}

/**
 * Check and enable auto-refresh if configured
 */
function checkAutoRefresh() {
	try {
		// Defaults
		window.itemsPerPage = window.itemsPerPage || 10;
		window.currentPage = window.currentPage || 1;

		const checkbox = document.getElementById('autoRefresh');
		const intervalInput = document.getElementById('autoRefreshInterval');
		let enabled = false;
		let intervalSec = 60; // default

		if (checkbox) enabled = checkbox.checked;
		if (intervalInput && intervalInput.value) intervalSec = parseInt(intervalInput.value, 10) || intervalSec;

		if (autoRefreshInterval) {
			clearInterval(autoRefreshInterval);
			autoRefreshInterval = null;
		}

		if (enabled) {
			autoRefreshInterval = setInterval(() => {
				loadSensorData();
			}, intervalSec * 1000);
		}
	} catch (err) {
		console.error('Error configuring auto-refresh', err);
	}
}

/**
 * Simple notification helper (brief floating message)
 */
function showNotification(message, type = 'info', timeout = 3500) {
	// Create container if missing
	let container = document.getElementById('sensorNotificationContainer');
	if (!container) {
		container = document.createElement('div');
		container.id = 'sensorNotificationContainer';
		container.style.position = 'fixed';
		container.style.top = '20px';
		container.style.right = '20px';
		container.style.zIndex = 2000;
		document.body.appendChild(container);
	}

	const el = document.createElement('div');
	el.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'secondary'} shadow-sm`;
	el.style.marginTop = '8px';
	el.style.minWidth = '200px';
	el.textContent = message;
	container.appendChild(el);

	setTimeout(() => {
		el.classList.add('fade');
		el.style.transition = 'opacity 300ms';
		el.style.opacity = 0;
		setTimeout(() => container.removeChild(el), 350);
	}, timeout);
}

/**
 * Wire up UI controls (called after DOM ready)
 */
function wireUpControls() {
	const sensorSelect = document.getElementById('sensorTypeSelect');
	if (sensorSelect) sensorSelect.addEventListener('change', onSensorTypeChange);

	const timeSelect = document.getElementById('timeRangeSelect');
	if (timeSelect) timeSelect.addEventListener('change', onTimeRangeChange);

	const startDate = document.getElementById('startDate');
	const endDate = document.getElementById('endDate');
	if (startDate) startDate.addEventListener('change', onCustomDateChange);
	if (endDate) endDate.addEventListener('change', onCustomDateChange);

	const refreshBtn = document.getElementById('refreshSensorDataBtn');
	if (refreshBtn) refreshBtn.addEventListener('click', refreshSensorData);

	const toggleTableBtn = document.getElementById('toggleTableBtn');
	if (toggleTableBtn) toggleTableBtn.addEventListener('click', toggleDataTable);

	const autoCheckbox = document.getElementById('autoRefresh');
	const autoInterval = document.getElementById('autoRefreshInterval');
	if (autoCheckbox) autoCheckbox.addEventListener('change', checkAutoRefresh);
	if (autoInterval) autoInterval.addEventListener('change', checkAutoRefresh);
}

// Initialize wiring when this script is loaded (if DOM already ready, run immediately)
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', () => {
		wireUpControls();
	});
} else {
	wireUpControls();
}

/**
 * Load sensor configuration from database (via API)
 * Uses per-entry JSON structure
 */
async function loadSensorConfiguration() {
	try {
		// Fetch all sensor preferences from API
		const response = await fetch('/api/user_preferences');
		const data = await response.json();
		
		if (!data.success) {
			console.error('Failed to load preferences from database');
			return;
		}
		
		const allPrefs = data.preferences || {};
		
		// Load per-entry preferences
		const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
		let prefs = {};
		
		if (allPrefs[prefKey]) {
			try {
				prefs = JSON.parse(allPrefs[prefKey]);
			} catch (e) {
				console.error('Failed to parse sensor preferences:', e);
				// Fall back to empty preferences
				prefs = {};
			}
		}
		
		// Load auto-refresh setting
		const autoRefresh = prefs.auto_refresh === true;
		const autoRefreshCheckbox = document.getElementById('autoRefresh');
		if (autoRefreshCheckbox) {
			autoRefreshCheckbox.checked = autoRefresh;
		}
		
		// Load show table setting (default to false/hidden)
		const showTableValue = prefs.show_table === true;
		const showTableCheckbox = document.getElementById('showDataTable');
		if (showTableCheckbox) {
			showTableCheckbox.checked = showTableValue;
		}
		
		// Load default sensor type
		const defaultSensorType = prefs.default_sensor_type || '';
		const sensorTypeConfigSelect = document.getElementById('defaultSensorType');
		if (sensorTypeConfigSelect) {
			sensorTypeConfigSelect.value = defaultSensorType;
		}
		// Apply the default sensor type to the main sensor type selector and global state
		const mainSensorTypeSelect = document.getElementById('sensorTypeSelect');
		if (mainSensorTypeSelect) {
			mainSensorTypeSelect.value = defaultSensorType;
		}
		// Always update the global currentSensorType variable
		currentSensorType = defaultSensorType;
		console.log('🔧 loadSensorConfiguration: Set currentSensorType to', currentSensorType);
		
		// Load default chart type - check for per-sensor preference first
		const chartTypes = prefs.chart_types || {};
		const defaultChartType = chartTypes[defaultSensorType] || 'line';
		
		const chartTypeConfigSelect = document.getElementById('defaultChartType');
		if (chartTypeConfigSelect) {
			chartTypeConfigSelect.value = defaultChartType;
		}
		// Apply the default chart type to the main chart type selector and global state
		const mainChartTypeSelect = document.getElementById('chartTypeSelect');
		if (mainChartTypeSelect) {
			mainChartTypeSelect.value = defaultChartType;
		}
		// Always update the global currentChartType variable
		currentChartType = defaultChartType;
		
		// Load default time range
		const defaultTimeRange = prefs.default_time_range || '7d';
		const timeRangeSelect = document.getElementById('defaultTimeRange');
		if (timeRangeSelect) {
			timeRangeSelect.value = defaultTimeRange;
		}
		// Apply the default time range to the main time range selector and global state
		const mainTimeRangeSelect = document.getElementById('timeRangeSelect');
		if (mainTimeRangeSelect) {
			mainTimeRangeSelect.value = defaultTimeRange;
		}
		// Always update the global currentTimeRange variable
		currentTimeRange = defaultTimeRange;
		
		// Apply table visibility with new structure
		const tableSection = document.getElementById('sensorDataTableSection');
		const showButton = document.getElementById('showTableButton');
		if (tableSection && showButton) {
			if (showTableValue) {
				tableSection.style.display = 'block';
				showButton.style.display = 'none';
			} else {
				tableSection.style.display = 'none';
				showButton.style.display = 'block';
			}
		}
	} catch (error) {
		console.error('Error loading sensor configuration:', error);
	}
}

/**
 * Populate the Enabled Types tab in the configuration modal
 */
async function populateEnabledSensorTypes() {
	const container = document.getElementById('enabledSensorTypesList');
	if (!container) return;
	
	try {
		// Show loading state
		container.innerHTML = '<div class="text-center p-3"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
		
		// Fetch all available sensor types from system
		const systemParamsResponse = await fetch('/api/system_params');
		if (!systemParamsResponse.ok) throw new Error('Failed to load system parameters');
		const systemParams = await systemParamsResponse.json();
		
		const sensorTypesString = systemParams.sensor_types || '';
		const availableSensorTypes = sensorTypesString.split(',')
			.map(type => type.trim())
			.filter(type => type !== '');
		
		if (availableSensorTypes.length === 0) {
			container.innerHTML = `
				<div class="text-center text-muted p-3">
					<i class="fas fa-robot fa-2x mb-2 d-block"></i>
					<p>No sensor types discovered yet.</p>
					<p class="small">Sensor types are automatically discovered when devices are added to the system.</p>
				</div>
			`;
			return;
		}
		
		// Fetch current entry's entry type and enabled sensor types
		const entryResponse = await fetch(`/api/entries/${window.currentEntryId}`);
		if (!entryResponse.ok) throw new Error('Failed to load entry data');
		const entryData = await entryResponse.json();
		
		const enabledTypes = entryData.enabled_sensor_types 
			? entryData.enabled_sensor_types.split(',').map(t => t.trim()).filter(t => t !== '')
			: [];
		
		// Build checkboxes HTML
		let html = '<div class="p-2">';
		html += '<p class="text-muted small mb-3">Select which sensor types are available for entries of this type:</p>';
		
		availableSensorTypes.forEach(sensorType => {
			const isChecked = enabledTypes.includes(sensorType);
			const checkboxId = `enabledType_${sensorType.replace(/\s+/g, '_')}`;
			
			html += `
				<div class="form-check mb-2">
					<input class="form-check-input enabled-sensor-type-checkbox" 
						   type="checkbox" 
						   value="${sensorType}" 
						   id="${checkboxId}"
						   ${isChecked ? 'checked' : ''}>
					<label class="form-check-label" for="${checkboxId}">
						${sensorType}
					</label>
				</div>
			`;
		});
		
		html += '</div>';
		html += `
			<div class="border-top pt-3 px-2">
				<button type="button" class="btn btn-sm btn-success w-100" onclick="saveEnabledSensorTypes()">
					<i class="fas fa-save me-1"></i>Save Enabled Types
				</button>
			</div>
		`;
		
		container.innerHTML = html;
		
	} catch (error) {
		console.error('Error loading enabled sensor types:', error);
		container.innerHTML = `
			<div class="alert alert-danger m-2">
				<i class="fas fa-exclamation-triangle me-1"></i>
				Failed to load sensor types: ${error.message}
			</div>
		`;
	}
}

/**
 * Save enabled sensor types for the entry's entry type
 */
async function saveEnabledSensorTypes() {
	try {
		// Get selected sensor types
		const checkboxes = document.querySelectorAll('.enabled-sensor-type-checkbox:checked');
		const selectedTypes = Array.from(checkboxes).map(cb => cb.value);
		
		// Get the entry's entry type ID
		const entryResponse = await fetch(`/api/entries/${window.currentEntryId}`);
		if (!entryResponse.ok) throw new Error('Failed to load entry data');
		const entryData = await entryResponse.json();
		const entryTypeId = entryData.entry_type_id;
		
		// Update the entry type's enabled sensor types
		const updateResponse = await fetch(`/api/entry_types/${entryTypeId}`, {
			method: 'PATCH',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				enabled_sensor_types: selectedTypes.join(',')
			})
		});
		
		if (!updateResponse.ok) {
			const errorData = await updateResponse.json();
			throw new Error(errorData.error || 'Failed to update sensor types');
		}
		
		showBanner('Enabled sensor types updated successfully', 'success');
		
		// Reload sensor types for this entry to reflect changes
		await loadSensorTypes();
		
		// Reload sensor data to apply any filtering based on new enabled types
		await loadSensorDataV2();
		
	} catch (error) {
		console.error('Error saving enabled sensor types:', error);
		showNotification('Failed to save enabled sensor types: ' + error.message, 'error');
	}
}

/**
 * Populate the Alerts & Thresholds tab in the configuration modal
 */
async function populateSensorAlerts() {
	const container = document.getElementById('alertConfigList');
	if (!container) return;
	
	try {
		// Show loading state
		container.innerHTML = '<div class="text-center p-3"><i class="fas fa-spinner fa-spin"></i> Loading alarms...</div>';
		
		// Get current entry's entry type
		const entryResponse = await fetch(`/api/entries/${window.currentEntryId}`);
		if (!entryResponse.ok) throw new Error('Failed to load entry data');
		const entryData = await entryResponse.json();
		const entryTypeId = entryData.entry_type_id;
		const entryTypeName = entryData.entry_type_label;
		
		// Fetch all notification rules
		const rulesResponse = await fetch('/api/notification_rules');
		if (!rulesResponse.ok) throw new Error('Failed to load notification rules');
		const allRules = await rulesResponse.json();
		
		// Filter rules relevant to this entry (by entry type or specific entry)
		const relevantRules = allRules.filter(rule => 
			rule.entry_type_id === entryTypeId || rule.entry_id === window.currentEntryId
		);
		
		if (relevantRules.length === 0) {
			container.innerHTML = `
				<div class="text-center text-muted p-3">
					<i class="fas fa-bell-slash fa-2x mb-2 d-block"></i>
					<p>No sensor alarms configured for this entry type yet.</p>
					<p class="small">Sensor alarms trigger notifications when readings cross defined thresholds.</p>
					<button class="btn btn-sm btn-success mt-2" onclick="openCreateAlarmModal()">
						<i class="fas fa-plus me-1"></i>Create First Alarm
					</button>
				</div>
			`;
			return;
		}
		
		// Build alarms list
		let html = '<div class="list-group">';
		
		relevantRules.forEach(rule => {
			const isActive = rule.is_active !== 0;
			const priorityClass = `priority-${rule.priority}`;
			const scopeText = rule.entry_id ? 'This entry only' : `All ${entryTypeName}`;
			
			// Format condition
			let conditionText = '';
			if (rule.condition_type === 'greater_than') {
				conditionText = `> ${rule.threshold_value}`;
			} else if (rule.condition_type === 'less_than') {
				conditionText = `< ${rule.threshold_value}`;
			} else if (rule.condition_type === 'equals') {
				conditionText = `= ${rule.threshold_value}`;
			} else if (rule.condition_type === 'between') {
				conditionText = `${rule.threshold_value} - ${rule.threshold_value_secondary || '?'}`;
			}
			if (rule.threshold_unit) {
				conditionText += ` ${rule.threshold_unit}`;
			}
			
			html += `
				<div class="list-group-item ${priorityClass}" style="border-left-width: 4px;">
					<div class="d-flex justify-content-between align-items-start">
						<div class="flex-grow-1">
							<div class="d-flex align-items-center mb-1">
								<h6 class="mb-0 me-2">${rule.name}</h6>
								<span class="badge bg-${isActive ? 'success' : 'secondary'} me-2">
									${isActive ? 'Active' : 'Inactive'}
								</span>
								<span class="badge bg-${getPriorityBadgeColor(rule.priority)}">
									${rule.priority.toUpperCase()}
								</span>
							</div>
							${rule.description ? `<p class="text-muted small mb-1">${rule.description}</p>` : ''}
							<div class="small">
								<strong>${rule.sensor_type}</strong> ${conditionText}
								<span class="text-muted ms-2">• ${scopeText}</span>
								<span class="text-muted ms-2">• Cooldown: ${rule.cooldown_minutes}min</span>
							</div>
						</div>
						<div class="btn-group btn-group-sm ms-2">
							<button class="btn btn-outline-primary" onclick="toggleAlarmStatus(${rule.id}, ${!isActive})" title="${isActive ? 'Deactivate' : 'Activate'}">
								<i class="fas fa-${isActive ? 'pause' : 'play'}"></i>
							</button>
							<button class="btn btn-outline-danger" onclick="deleteAlarm(${rule.id})" title="Delete">
								<i class="fas fa-trash"></i>
							</button>
						</div>
					</div>
				</div>
			`;
		});
		
		html += '</div>';
		html += `
			<div class="mt-3 d-grid">
				<button class="btn btn-success" onclick="openCreateAlarmModal()">
					<i class="fas fa-plus me-1"></i>Create New Alarm
				</button>
			</div>
		`;
		
		container.innerHTML = html;
		
	} catch (error) {
		console.error('Error loading sensor alarms:', error);
		container.innerHTML = `
			<div class="alert alert-danger m-2">
				<i class="fas fa-exclamation-triangle me-1"></i>
				Failed to load sensor alarms: ${error.message}
			</div>
		`;
	}
}

/**
 * Get bootstrap color class for priority badge
 */
function getPriorityBadgeColor(priority) {
	const colors = {
		'low': 'info',
		'medium': 'warning',
		'high': 'danger',
		'critical': 'danger'
	};
	return colors[priority] || 'secondary';
}

/**
 * Toggle alarm active status
 */
async function toggleAlarmStatus(ruleId, activate) {
	try {
		const response = await fetch(`/api/notification_rules/${ruleId}`, {
			method: 'PATCH',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				is_active: activate ? 1 : 0
			})
		});
		
		if (!response.ok) {
			throw new Error('Failed to update alarm status');
		}
		
		showBanner(`Alarm ${activate ? 'activated' : 'deactivated'} successfully`, 'success');
		
		// Reload alerts
		await populateSensorAlerts();
		
	} catch (error) {
		console.error('Error toggling alarm status:', error);
		showNotification('Failed to update alarm status: ' + error.message, 'error');
	}
}

/**
 * Delete an alarm
 */
async function deleteAlarm(ruleId) {
	if (!confirm('Are you sure you want to delete this alarm? This action cannot be undone.')) {
		return;
	}
	
	try {
		const response = await fetch(`/api/notification_rules/${ruleId}`, {
			method: 'DELETE'
		});
		
		if (!response.ok) {
			throw new Error('Failed to delete alarm');
		}
		
		showBanner('Alarm deleted successfully', 'success');
		
		// Reload alerts
		await populateSensorAlerts();
		
	} catch (error) {
		console.error('Error deleting alarm:', error);
		showNotification('Failed to delete alarm: ' + error.message, 'error');
	}
}

/**
 * Open the create alarm modal (redirects to manage sensor alarms page)
 */
function openCreateAlarmModal() {
	// Navigate to the full sensor alarms management page
	window.location.href = '/manage_sensor_alarms';
}

/**
 * Populate the Devices & Sources tab in the configuration modal
 */
async function populateDevices() {
	const container = document.getElementById('deviceListModal');
	if (!container) return;
	
	try {
		// Show loading state
		container.innerHTML = '<div class="text-center p-3"><i class="fas fa-spinner fa-spin"></i> Loading devices...</div>';
		
		// Get linked devices for this entry
		const devicesResponse = await fetch(`/api/entries/${entryId}/linked-devices`);
		if (!devicesResponse.ok) throw new Error('Failed to load linked devices');
		
		const devicesData = await devicesResponse.json();
		const linkedDevices = devicesData.linked_devices || [];
		
		// Get sensor data statistics for each device
		// Match by device_id (the string identifier like "ESP32-001") not the database ID
		const deviceStats = {};
		sensorData.forEach(reading => {
			// source_id from SharedSensorData contains the device_id string
			const deviceId = reading.source_id;
			if (deviceId && reading.source_type === 'device') {
				if (!deviceStats[deviceId]) {
					deviceStats[deviceId] = {
						sensorTypes: new Set(),
						count: 0,
						lastSeen: reading.recorded_at
					};
				}
				deviceStats[deviceId].count++;
				deviceStats[deviceId].sensorTypes.add(reading.sensor_type);
				if (new Date(reading.recorded_at) > new Date(deviceStats[deviceId].lastSeen)) {
					deviceStats[deviceId].lastSeen = reading.recorded_at;
				}
			}
		});
		
		// Build device cards HTML
		if (linkedDevices.length === 0) {
			container.innerHTML = `
				<div class="text-center text-muted p-4">
					<i class="fas fa-robot fa-3x mb-3 opacity-50"></i>
					<p class="mb-0">No devices linked to this entry.</p>
					<p class="small">Link devices from the <a href="/manage_devices" class="alert-link">Device Management</a> page.</p>
				</div>
			`;
			return;
		}
		
		let html = '<div class="list-group">';
		
		linkedDevices.forEach(device => {
			// Get stats for this device
			const stats = deviceStats[device.device_id] || { sensorTypes: new Set(), count: 0, lastSeen: null };
			const sensorTypesArray = Array.from(stats.sensorTypes);
			const sensorTypesList = sensorTypesArray.length > 0 ? sensorTypesArray.join(', ') : 'No data yet';
			
			// Determine status
			let statusBadge = '';
			let statusIcon = 'microchip';
			if (device.status === 'online') {
				statusBadge = '<span class="badge bg-success ms-2">Online</span>';
				statusIcon = 'microchip text-success';
			} else if (device.status === 'offline') {
				statusBadge = '<span class="badge bg-danger ms-2">Offline</span>';
				statusIcon = 'microchip text-danger';
			} else if (device.status === 'disabled') {
				statusBadge = '<span class="badge bg-secondary ms-2">Disabled</span>';
				statusIcon = 'microchip text-muted';
			}
			
			html += `
				<div class="list-group-item">
					<div class="d-flex justify-content-between align-items-start">
						<div class="flex-grow-1">
							<div class="d-flex align-items-center mb-2">
								<i class="fas fa-${statusIcon} me-2"></i>
								<h6 class="mb-0">${device.device_name}</h6>
								${statusBadge}
								<span class="badge bg-info ms-2">${device.device_type}</span>
							</div>
							<div class="small text-muted mb-1">
								<i class="fas fa-network-wired me-1"></i>
								<a href="http://${device.ip}" target="_blank" class="text-decoration-none">
									${device.ip} <i class="fas fa-external-link-alt ms-1"></i>
								</a>
							</div>
							<div class="small text-muted mb-1">
								<strong>Device ID:</strong> ${device.device_id}
							</div>
						</div>
					</div>
				</div>
			`;
		});
		
		html += '</div>';
		container.innerHTML = html;
		
	} catch (error) {
		console.error('Error loading devices:', error);
		container.innerHTML = `
			<div class="alert alert-danger m-2">
				<i class="fas fa-exclamation-triangle me-1"></i>
				Failed to load devices: ${error.message}
			</div>
		`;
	}
}

/**
 * Save sensor configuration to database via API
 * Uses per-entry JSON structure for better organization
 */
async function saveSensorConfiguration() {
	try {
		// Get configuration values
		const autoRefresh = document.getElementById('autoRefresh')?.checked || false;
		const showDataTable = document.getElementById('showDataTable')?.checked || false;
		const defaultSensorType = document.getElementById('defaultSensorType')?.value || '';
		const defaultChartType = document.getElementById('defaultChartType')?.value || 'line';
		const defaultTimeRange = document.getElementById('defaultTimeRange')?.value || '7d';
		
		// Load existing preferences to preserve chart types for other sensors
		const response = await fetch('/api/user_preferences');
		let existingPrefs = {};
		if (response.ok) {
			const data = await response.json();
			const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
			const existing = data.preferences?.[prefKey];
			if (existing) {
				try {
					existingPrefs = JSON.parse(existing);
				} catch (e) {
					console.error('Failed to parse existing preferences:', e);
				}
			}
		}
		
		// Build preference object with chart types preserved
		const chartTypes = existingPrefs.chart_types || {};
		if (defaultSensorType) {
			chartTypes[defaultSensorType] = defaultChartType;
		}
		
		const preferences = {
			auto_refresh: autoRefresh,
			show_table: showDataTable,
			default_sensor_type: defaultSensorType,
			default_time_range: defaultTimeRange,
			chart_types: chartTypes,
			saved_at: new Date().toISOString()
		};
		
		// Save as single JSON object per entry
		const prefKey = `sensor_preferences_entry_${window.currentEntryId}`;
		const saveResponse = await fetch(`/api/user_preferences/${prefKey}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ value: JSON.stringify(preferences) })
		});
		
		if (!saveResponse.ok) {
			throw new Error('Failed to save preferences');
		}
		
		// Apply settings
		if (autoRefresh) {
			checkAutoRefresh();
		} else {
			if (autoRefreshInterval) {
				clearInterval(autoRefreshInterval);
				autoRefreshInterval = null;
			}
		}
		
		// Toggle table visibility with new structure
		const tableSection = document.getElementById('sensorDataTableSection');
		const showButton = document.getElementById('showTableButton');
		if (tableSection && showButton) {
			if (showDataTable) {
				tableSection.style.display = 'block';
				showButton.style.display = 'none';
			} else {
				tableSection.style.display = 'none';
				showButton.style.display = 'block';
			}
		}
		
		// Apply default sensor type to main selector
		const mainSensorTypeSelect = document.getElementById('sensorTypeSelect');
		if (mainSensorTypeSelect && mainSensorTypeSelect.value !== defaultSensorType) {
			mainSensorTypeSelect.value = defaultSensorType;
			currentSensorType = defaultSensorType;
		}
		
		// Apply default time range to main selector
		const mainTimeRangeSelect = document.getElementById('timeRangeSelect');
		if (mainTimeRangeSelect && mainTimeRangeSelect.value !== defaultTimeRange) {
			mainTimeRangeSelect.value = defaultTimeRange;
			currentTimeRange = defaultTimeRange;
		}
		
		// Reload data with new settings
		if (mainSensorTypeSelect?.value !== defaultSensorType || mainTimeRangeSelect?.value !== defaultTimeRange) {
			loadSensorDataV2();
		}
		
		// Close modal (fixed modal ID)
		const modal = bootstrap.Modal.getInstance(document.getElementById('configureSensorsModal'));
		if (modal) modal.hide();
		
		showBanner('Configuration saved successfully to database', 'success');
	} catch (error) {
		console.error('Error saving sensor configuration:', error);
		showBanner('Failed to save configuration', 'error');
	}
}

// Expose main functions to global scope so template buttons can call them
window.initializeSensorSection = initializeSensorSection;
window.refreshSensorData = refreshSensorData;
window.editSensorReading = editSensorReading;
window.deleteSensorReadingConfirm = deleteSensorReadingConfirm;
window.changePage = changePage;
window.toggleDataTable = toggleDataTable;
window.showNotification = showNotification;
window.loadSensorConfiguration = loadSensorConfiguration;
window.saveSensorConfiguration = saveSensorConfiguration;
window.populateEnabledSensorTypes = populateEnabledSensorTypes;
window.saveEnabledSensorTypes = saveEnabledSensorTypes;
window.populateSensorAlerts = populateSensorAlerts;
window.toggleAlarmStatus = toggleAlarmStatus;
window.deleteAlarm = deleteAlarm;
window.openCreateAlarmModal = openCreateAlarmModal;
window.populateDevices = populateDevices;

