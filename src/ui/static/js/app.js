/**
 * LinuxTrainer Web Application JavaScript
 */

// Global variables
let isConnected = false;
let isTraining = false;
let statusInterval;
let logInterval;
let powerDataHistory = [];



/**
 * Update the status display with current data
 */
function updateStatus() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Validate data
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid data received from server');
            }
            
            // Update connection status
            updateConnectionStatus(data.connected);
            
            // Update training status
            updateTrainingStatus(data.training);
            
            // Update data values
            updateDataValues(data.data);
            
            // Update button states
            updateButtonStates(data.connected, data.training);
            
            // Store power data for statistics
            if (data.data && validatePowerData(data.data)) {
                powerDataHistory.push({
                    timestamp: Date.now(),
                    power: data.data.power,
                    cadence: data.data.cadence,
                    speed: data.data.speed
                });
                
                // Keep only last 100 data points
                if (powerDataHistory.length > 100) {
                    powerDataHistory = powerDataHistory.slice(-100);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            addLogEntry('ERROR', 'Error fetching status: ' + error.message);
            showNotification('Connection error: ' + error.message, 'error');
        });
}

/**
 * Update connection status display
 * @param {boolean} connected - Connection status
 */
function updateConnectionStatus(connected) {
    const connectionStatus = document.getElementById('connectionStatus');
    const connectionText = document.getElementById('connectionText');
    
    if (connected) {
        connectionStatus.classList.add('connected');
        connectionText.textContent = 'Connected';
        isConnected = true;
    } else {
        connectionStatus.classList.remove('connected');
        connectionText.textContent = 'Not Connected';
        isConnected = false;
    }
}

/**
 * Update training status display
 * @param {boolean} training - Training status
 */
function updateTrainingStatus(training) {
    const trainingStatus = document.getElementById('trainingStatus');
    const trainingText = document.getElementById('trainingText');
    
    if (training) {
        trainingStatus.classList.add('training');
        trainingText.textContent = 'Training';
        isTraining = true;
    } else {
        trainingStatus.classList.remove('training');
        trainingText.textContent = 'Not Training';
        isTraining = false;
    }
}

/**
 * Update data values display
 * @param {Object} data - Power data object
 */
function updateDataValues(data) {
    if (!data) return;
    
    document.getElementById('powerValue').textContent = formatPower(data.power);
    document.getElementById('cadenceValue').textContent = formatCadence(data.cadence);
    document.getElementById('speedValue').textContent = formatSpeed(data.speed);
    document.getElementById('durationValue').textContent = data.duration || '00:00:00';
}

/**
 * Update button states
 * @param {boolean} connected - Connection status
 * @param {boolean} training - Training status
 */
function updateButtonStates(connected, training) {
    document.getElementById('connectBtn').textContent = connected ? 'Disconnect' : 'Connect to Kickr';
    document.getElementById('startBtn').disabled = !connected || training;
    document.getElementById('stopBtn').disabled = !training;
    document.getElementById('exportBtn').disabled = !training;
}

/**
 * Update the connection logs display
 */
function updateLogs() {
    fetch('/api/logs')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const connectionLog = document.getElementById('connectionLog');
            if (!connectionLog) return;
            
            connectionLog.innerHTML = '';
            
            // Display logs (most recent first)
            if (data.logs && Array.isArray(data.logs)) {
                data.logs.reverse().forEach(log => {
                    addLogEntryToDOM(log);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
        });
}

/**
 * Add a log entry to the display
 * @param {string} level - Log level (INFO, SUCCESS, ERROR)
 * @param {string} message - Log message
 */
function addLogEntry(level, message) {
    const logEntry = {
        timestamp: getCurrentTime(),
        level: level,
        message: message
    };
    addLogEntryToDOM(logEntry);
}

/**
 * Add a log entry to the DOM
 * @param {Object} log - Log entry object
 */
function addLogEntryToDOM(log) {
    const connectionLog = document.getElementById('connectionLog');
    if (!connectionLog) return;
    
    const logDiv = document.createElement('div');
    logDiv.className = `log-entry ${log.level}`;
    
    logDiv.innerHTML = `
        <span class="log-timestamp">${log.timestamp}</span>
        <span class="log-message">${log.message}</span>
    `;
    
    connectionLog.insertBefore(logDiv, connectionLog.firstChild);
    
    // Keep only last 15 log entries visible
    while (connectionLog.children.length > 15) {
        connectionLog.removeChild(connectionLog.lastChild);
    }
    
    // Auto-scroll to top (newest logs)
    // Do not use for now
    //connectionLog.scrollTop = 1;
}

/**
 * Clear all logs
 */
function clearLogs() {
    fetch('/api/logs/clear', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                document.getElementById('connectionLog').innerHTML = '';
                addLogEntry('INFO', 'System ready');
                showNotification('Logs cleared', 'success');
            } else {
                throw new Error(data.message || 'Failed to clear logs');
            }
        })
        .catch(error => {
            console.error('Error clearing logs:', error);
            addLogEntry('ERROR', 'Error clearing logs: ' + error.message);
            showNotification('Failed to clear logs: ' + error.message, 'error');
        });
}

/**
 * Connect or disconnect from Kickr trainer
 */
function connect() {
    if (isConnected) {
        addLogEntry('INFO', 'Disconnecting from Kickr trainer...');
        
        fetch('/api/disconnect', { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    addLogEntry('SUCCESS', '✅ Disconnected from Kickr trainer');
                    showNotification('Disconnected from Kickr trainer', 'success');
                } else {
                    throw new Error(data.message || 'Failed to disconnect');
                }
            })
            .catch(error => {
                console.error('Error disconnecting:', error);
                addLogEntry('ERROR', '❌ Error disconnecting from Kickr: ' + error.message);
                showNotification('Disconnection failed: ' + error.message, 'error');
            });
    } else {
        addLogEntry('INFO', 'Connecting to Kickr trainer...');
        
        fetch('/api/connect', { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    addLogEntry('SUCCESS', '✅ Connected to Kickr trainer');
                    showNotification('Connected to Kickr trainer', 'success');
                } else {
                    throw new Error(data.message || 'Failed to connect');
                }
            })
            .catch(error => {
                console.error('Error connecting:', error);
                addLogEntry('ERROR', '❌ Error connecting to Kickr: ' + error.message);
                showNotification('Connection failed: ' + error.message, 'error');
            });
    }
}

/**
 * Start training session
 */
function startTraining() {
    addLogEntry('INFO', 'Starting training session...');
    
    fetch('/api/start_training', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                addLogEntry('SUCCESS', '🚴 Training session started');
                showNotification('Training session started', 'success');
                powerDataHistory = []; // Reset data history
            } else {
                throw new Error(data.message || 'Failed to start training');
            }
        })
        .catch(error => {
            console.error('Error starting training:', error);
            addLogEntry('ERROR', '❌ Error starting training: ' + error.message);
            showNotification('Failed to start training: ' + error.message, 'error');
        });
}

/**
 * Stop training session
 */
function stopTraining() {
    addLogEntry('INFO', 'Stopping training session...');
    
    fetch('/api/stop_training', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                addLogEntry('SUCCESS', '⏹️ Training session stopped');
                showNotification('Training session stopped', 'success');
                
                // Show session statistics
                if (powerDataHistory.length > 0) {
                    const powers = powerDataHistory.map(d => d.power);
                    const avgPower = calculateAverage(powers);
                    const maxPower = calculateMax(powers);
                    addLogEntry('INFO', `Session stats - Avg Power: ${avgPower.toFixed(1)}W, Max Power: ${maxPower}W`);
                }
            } else {
                throw new Error(data.message || 'Failed to stop training');
            }
        })
        .catch(error => {
            console.error('Error stopping training:', error);
            addLogEntry('ERROR', '❌ Error stopping training: ' + error.message);
            showNotification('Failed to stop training: ' + error.message, 'error');
        });
}

/**
 * Export training data
 */
function exportData() {
    addLogEntry('INFO', 'Exporting training data...');
    
    fetch('/api/export', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                addLogEntry('SUCCESS', '📁 Data exported successfully');
                showNotification('Data exported successfully', 'success');
                
                // Log export paths
                if (data.paths) {
                    Object.entries(data.paths).forEach(([format, path]) => {
                        addLogEntry('INFO', `Exported ${format.toUpperCase()}: ${path}`);
                    });
                }
            } else {
                throw new Error(data.message || 'Failed to export data');
            }
        })
        .catch(error => {
            console.error('Error exporting data:', error);
            addLogEntry('ERROR', '❌ Error exporting data: ' + error.message);
            showNotification('Export failed: ' + error.message, 'error');
        });
}

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('LinuxTrainer Web App initializing...');
    
    // Check browser support
    if (!checkBrowserSupport()) {
        showNotification('Your browser does not support all required features', 'error');
        addLogEntry('ERROR', 'Browser compatibility check failed');
        return;
    }
    
    // Initialize UI
    addLogEntry('INFO', 'System ready');
    
    // Start status updates with debouncing
    const debouncedUpdateStatus = debounce(updateStatus, 100);
    statusInterval = setInterval(debouncedUpdateStatus, 1000);
    updateStatus(); // Initial update

    // Start log updates
    logInterval = setInterval(updateLogs, 1000);
    updateLogs(); // Initial log update
    
    console.log('LinuxTrainer Web App initialized successfully');
}

/**
 * Cleanup function for when the page is unloaded
 */
function cleanup() {
    console.log('Cleaning up LinuxTrainer Web App...');
    
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    if (logInterval) {
        clearInterval(logInterval);
    }
    
    console.log('LinuxTrainer Web App cleanup complete');
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Cleanup when the page is unloaded
window.addEventListener('beforeunload', cleanup);

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('Page hidden - reducing update frequency');
    } else {
        console.log('Page visible - resuming normal updates');
    }
});
