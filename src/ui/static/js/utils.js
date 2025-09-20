/**
 * LinuxTrainer Utility Functions
 */

/**
 * Format time duration in HH:MM:SS format
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted time string
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format power value with proper units
 * @param {number} power - Power in watts
 * @returns {string} Formatted power string
 */
function formatPower(power) {
    return `${power || 0} W`;
}

/**
 * Format cadence value with proper units
 * @param {number} cadence - Cadence in RPM
 * @returns {string} Formatted cadence string
 */
function formatCadence(cadence) {
    return `${cadence || 0} RPM`;
}

/**
 * Format speed value with proper units
 * @param {number} speed - Speed in km/h
 * @returns {string} Formatted speed string
 */
function formatSpeed(speed) {
    return `${(speed || 0).toFixed(1)} km/h`;
}

/**
 * Show a startup notification
 */

function showStartNotification(message){
    const notification = document.createElement(`div`);
    notification.className = 'startNotification';
    notification.textContent = message;

    document.body.append(notification);
}

/**
 * Show a notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info)
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#00ff88';
            notification.style.color = '#000';
            break;
        case 'error':
            notification.style.backgroundColor = '#ff6b6b';
            break;
        case 'info':
        default:
            notification.style.backgroundColor = '#2a5298';
            break;
    }
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Check if the browser supports required features
 * @returns {boolean} True if all features are supported
 */
function checkBrowserSupport() {
    const features = [
        'fetch' in window,
        'Promise' in window,
        'addEventListener' in window,
        'querySelector' in document
    ];
    
    return features.every(feature => feature);
}

/**
 * Get the current timestamp
 * @returns {string} Current time in HH:MM:SS format
 */
function getCurrentTime() {
    return new Date().toLocaleTimeString();
}

/**
 * Validate power data
 * @param {Object} data - Power data object
 * @returns {boolean} True if data is valid
 */
function validatePowerData(data) {
    return data && 
           typeof data.power === 'number' && 
           data.power >= 0 && 
           data.power <= 2000;
}

/**
 * Calculate average from an array of numbers
 * @param {number[]} numbers - Array of numbers
 * @returns {number} Average value
 */
function calculateAverage(numbers) {
    if (!numbers || numbers.length === 0) return 0;
    return numbers.reduce((sum, num) => sum + num, 0) / numbers.length;
}

/**
 * Calculate maximum from an array of numbers
 * @param {number[]} numbers - Array of numbers
 * @returns {number} Maximum value
 */
function calculateMax(numbers) {
    if (!numbers || numbers.length === 0) return 0;
    return Math.max(...numbers);
}

/**
 * Calculate minimum from an array of numbers
 * @param {number[]} numbers - Array of numbers
 * @returns {number} Minimum value
 */
function calculateMin(numbers) {
    if (!numbers || numbers.length === 0) return 0;
    return Math.min(...numbers);
}

/**
 * Export utility functions for use in other modules
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDuration,
        formatPower,
        formatCadence,
        formatSpeed,
        showNotification,
        debounce,
        checkBrowserSupport,
        getCurrentTime,
        validatePowerData,
        calculateAverage,
        calculateMax,
        calculateMin
    };
}
