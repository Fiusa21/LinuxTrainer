/**
 * Startup Screen JavaScript
 * Basic functionality without API connections
 */

// Initialize startup screen
document.addEventListener('DOMContentLoaded', function() {
    console.log('Startup screen loaded');
    
    // Add some interactive effects
    initializeInteractiveElements();
    
    // Simulate system status checks
    simulateSystemChecks();
});

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Add hover effects to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add click effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

/**
 * Simulate system status checks
 */
function simulateSystemChecks() {
    const statusIndicators = document.querySelectorAll('.status-footer .status-indicator');
    const statusTexts = document.querySelectorAll('.status-footer .status-item span');
    
    // Simulate system ready check
    setTimeout(() => {
        statusIndicators[0].classList.add('connected');
        statusTexts[0].textContent = 'System Ready ✓';
    }, 1000);
    
    // Simulate Bluetooth check
    setTimeout(() => {
        statusIndicators[1].classList.add('connected');
        statusTexts[1].textContent = 'Bluetooth Available ✓';
    }, 1500);
    
    // Trainer status remains disconnected
    setTimeout(() => {
        statusIndicators[2].classList.add('training');
        statusTexts[2].textContent = 'No Trainer Connected';
    }, 2000);
}

/**
 * Start training button handler
 * Placeholder for future implementation
 */
function startTraining() {
    console.log('Start training clicked');
    
    // Show loading state
    const startBtn = document.querySelector('.btn-primary');
    const originalText = startBtn.innerHTML;
    
    startBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6V12L16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Connecting...
    `;
    startBtn.disabled = true;
    
    // Simulate connection process
    setTimeout(() => {
        startBtn.innerHTML = originalText;
        startBtn.disabled = false;
        
        // Redirect to the main training screen
        console.log('Redirecting to main training screen');
        window.location.href = '/index';
    }, 3000);
}

/**
 * Settings button handler
 * Placeholder for future implementation
 */
function showSettings() {
    console.log('Settings clicked');
    
    // Create a simple modal for settings
    const modal = document.createElement('div');
    modal.className = 'settings-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Settings</h3>
                <button class="close-btn" onclick="closeSettings()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="setting-item">
                    <label>Rider Weight (kg):</label>
                    <input type="number" value="75" min="40" max="200">
                </div>
                <div class="setting-item">
                    <label>Gradient (%):</label>
                    <input type="number" value="0" min="-20" max="20" step="0.1">
                </div>
                <div class="setting-item">
                    <label>Auto-connect:</label>
                    <input type="checkbox" checked>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeSettings()">Cancel</button>
                <button class="btn btn-primary" onclick="saveSettings()">Save</button>
            </div>
        </div>
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .settings-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }
        
        .modal-content {
            background: rgba(0,0,0,0.9);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 15px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
            animation: slideIn 0.3s ease;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-header h3 {
            color: #00ff88;
            margin: 0;
        }
        
        .close-btn {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .setting-item {
            margin-bottom: 20px;
        }
        
        .setting-item label {
            display: block;
            margin-bottom: 8px;
            color: #00ff88;
        }
        
        .setting-item input {
            width: 100%;
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(0,0,0,0.5);
            color: white;
            font-size: 16px;
        }
        
        .setting-item input:focus {
            outline: none;
            border-color: #00ff88;
            box-shadow: 0 0 10px rgba(0,255,136,0.3);
        }
        
        .modal-footer {
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 30px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
}

/**
 * Close settings modal
 */
function closeSettings() {
    const modal = document.querySelector('.settings-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Save settings
 */
function saveSettings() {
    console.log('Settings saved');
    closeSettings();
    
    // Show success message
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = 'Settings saved successfully!';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(45deg, #00ff88, #00cc6a);
        color: #000;
        padding: 15px 25px;
        border-radius: 25px;
        font-weight: bold;
        z-index: 1001;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
