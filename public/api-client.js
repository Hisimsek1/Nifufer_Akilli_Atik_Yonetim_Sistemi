// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Local Storage Keys
const STORAGE_KEYS = {
    TOKEN: 'auth_token',
    USER: 'user_data'
};

// ============== AUTH HELPERS ==============
function getAuthToken() {
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
}

function setAuthToken(token) {
    localStorage.setItem(STORAGE_KEYS.TOKEN, token);
}

function getUserData() {
    const data = localStorage.getItem(STORAGE_KEYS.USER);
    return data ? JSON.parse(data) : null;
}

function setUserData(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
}

function logout() {
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
    window.location.href = '/';
}

// ============== API CALL HELPER ==============
async function apiCall(endpoint, method = 'GET', data = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (requiresAuth) {
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }
    
    const options = {
        method,
        headers
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Bir hata oluştu');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============== AUTH FUNCTIONS ==============
async function login(email, password) {
    try {
        const result = await apiCall('/auth/login', 'POST', { email, password }, false);
        
        if (result.success) {
            setAuthToken(result.token);
            setUserData(result.user);
            return result.user;
        }
        
        throw new Error('Login failed');
    } catch (error) {
        throw error;
    }
}

async function register(name, email, password, phone) {
    try {
        const result = await apiCall('/auth/register', 'POST', {
            name, email, password, phone
        }, false);
        
        if (result.success) {
            setAuthToken(result.token);
            setUserData(result.user);
            return result.user;
        }
        
        throw new Error('Registration failed');
    } catch (error) {
        throw error;
    }
}

// ============== REPORT FUNCTIONS ==============
async function submitReport(containerID, fillLevel, description, photoFile = null) {
    try {
        // Get current position
        const position = await getCurrentPosition();
        
        let photoUrl = null;
        if (photoFile) {
            // In production, upload to server first
            photoUrl = await convertFileToBase64(photoFile);
        }
        
        const reportData = {
            container_id: parseInt(containerID),
            fill_level_estimate: parseFloat(fillLevel) / 100,
            latitude: position.latitude,
            longitude: position.longitude,
            notes: description,
            photo_url: photoUrl
        };
        
        const result = await apiCall('/reports', 'POST', reportData);
        
        return result;
    } catch (error) {
        throw error;
    }
}

// ============== PREDICTION FUNCTIONS ==============
async function getPrediction(containerID) {
    try {
        const result = await apiCall(`/predict/${containerID}`, 'GET', null, false);
        return result;
    } catch (error) {
        throw error;
    }
}

async function getNeighborhoodPredictions(neighborhoodID) {
    try {
        const result = await apiCall(`/predict/neighborhood/${neighborhoodID}`, 'GET', null, false);
        return result;
    } catch (error) {
        throw error;
    }
}

// ============== DASHBOARD FUNCTIONS ==============
async function getDashboardStats() {
    try {
        const result = await apiCall('/dashboard/stats', 'GET');
        return result;
    } catch (error) {
        throw error;
    }
}

async function getLeaderboard(limit = 10) {
    try {
        const result = await apiCall(`/leaderboard?limit=${limit}`, 'GET');
        return result.leaderboard;
    } catch (error) {
        throw error;
    }
}

// ============== SIMULATION FUNCTIONS ==============
async function runSimulation(scenario) {
    try {
        const result = await apiCall('/simulate', 'POST', { scenario });
        return result.results;
    } catch (error) {
        throw error;
    }
}

// ============== UTILITY FUNCTIONS ==============
function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation not supported'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
            },
            (error) => {
                // Default to Nilüfer center if location denied
                resolve({
                    latitude: 40.1885,
                    longitude: 28.9784
                });
            }
        );
    });
}

function convertFileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// ============== UI HELPERS ==============
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#00A651' : type === 'error' ? '#dc3545' : '#0066B3'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// ============== INIT ==============
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const user = getUserData();
    
    if (user) {
        // Update UI with user data
        updateUserInterface(user);
    } else {
        // Show login/register forms
        showAuthForms();
    }
});

function updateUserInterface(user) {
    const userNameElement = document.querySelector('.user-name');
    if (userNameElement) {
        userNameElement.textContent = user.name;
    }
    
    // Update stats
    if (user.trust_score !== undefined) {
        const trustScoreElement = document.querySelector('.stat-value');
        if (trustScoreElement) {
            trustScoreElement.textContent = Math.round(user.trust_score * 100) + '/100';
        }
    }
    
    // Show main content, hide auth
    const authPanel = document.querySelector('.auth-panel');
    const mainContent = document.querySelector('.main-content');
    
    if (authPanel) authPanel.style.display = 'none';
    if (mainContent) mainContent.style.display = 'block';
}

function showAuthForms() {
    const authPanel = document.querySelector('.auth-panel');
    const mainContent = document.querySelector('.main-content');
    
    if (authPanel) authPanel.style.display = 'block';
    if (mainContent) mainContent.style.display = 'none';
}

// Export functions for use in other scripts
window.WasteManagementAPI = {
    login,
    register,
    logout,
    submitReport,
    getPrediction,
    getNeighborhoodPredictions,
    getDashboardStats,
    getLeaderboard,
    runSimulation,
    showNotification,
    getUserData
};
