// Smart Waste Management System - Client-Side JavaScript

// ============== FORM SUBMISSION HANDLING ==============
document.addEventListener('DOMContentLoaded', function() {
    const reportForm = document.getElementById('reportForm');
    const formResult = document.getElementById('formResult');
    
    if (reportForm) {
        reportForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Simulate user trust score check
    checkUserTrustScore();
});

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formResult = document.getElementById('formResult');
    const submitButton = event.target.querySelector('.submit-button');
    
    // Get form data
    const containerID = document.getElementById('containerID').value;
    const fillLevel = document.getElementById('fillLevel').value;
    const description = document.getElementById('description').value;
    const photoFile = document.getElementById('photoUpload').files[0];
    
    // Validate required fields
    if (!containerID || !fillLevel) {
        showFormResult('error', 'Lütfen tüm zorunlu alanları doldurunuz.');
        return;
    }
    
    // Show loading state
    submitButton.disabled = true;
    submitButton.textContent = 'Gönderiliyor...';
    
    try {
        // Simulate API call to backend
        const reportData = {
            container_id: containerID,
            reported_status: fillLevel,
            description: description,
            photo: photoFile ? await convertFileToBase64(photoFile) : null,
            timestamp: new Date().toISOString()
        };
        
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Simulate validation response
        const validationResult = simulateValidation(fillLevel);
        
        if (validationResult.status === 'accepted') {
            showFormResult('success', 
                `✓ Bildiriminiz başarıyla kaydedildi! ${validationResult.message}`);
            
            // Update user stats (simulated)
            updateUserStats(true);
            
            // Reset form
            document.getElementById('reportForm').reset();
            
        } else if (validationResult.status === 'rejected') {
            showFormResult('error', 
                `✗ Bildiriminiz doğrulanamadı. ${validationResult.message}`);
            
            updateUserStats(false);
            
        } else {
            showFormResult('success', 
                `⏳ Bildiriminiz inceleme için gönderildi. ${validationResult.message}`);
        }
        
    } catch (error) {
        showFormResult('error', 'Bir hata oluştu. Lütfen tekrar deneyin.');
        console.error('Form submission error:', error);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Bildirimi Gönder';
    }
}

function showFormResult(type, message) {
    const formResult = document.getElementById('formResult');
    formResult.className = `form-result ${type}`;
    formResult.textContent = message;
    formResult.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        formResult.style.display = 'none';
    }, 5000);
}

// ============== VALIDATION SIMULATION ==============
function simulateValidation(reportedStatus) {
    // Simulate AI model prediction
    const modelPrediction = Math.random(); // 0-1 probability
    
    // Map reported status to expected range
    const thresholds = {
        'empty': { min: 0.0, max: 0.25 },
        'half': { min: 0.25, max: 0.75 },
        'full': { min: 0.75, max: 0.90 },
        'overflowing': { min: 0.90, max: 1.0 }
    };
    
    const expected = thresholds[reportedStatus];
    
    if (modelPrediction >= expected.min && modelPrediction <= expected.max) {
        // Report matches prediction
        return {
            status: 'accepted',
            message: 'Model tahminlerimizle uyumlu. Güven puanınız arttı.'
        };
    } else {
        const deviation = Math.abs(modelPrediction - (expected.min + expected.max) / 2);
        
        if (deviation < 0.20) {
            return {
                status: 'review',
                message: 'Küçük bir farklılık tespit edildi. Yetkili incelemesi yapılacak.'
            };
        } else {
            return {
                status: 'rejected',
                message: 'Model tahminleriyle uyumsuz. Konteyner kodunu kontrol edin.'
            };
        }
    }
}

// ============== USER STATS UPDATE ==============
function updateUserStats(accepted) {
    const trustScoreValue = document.querySelector('.stat-value');
    const trustScoreFill = document.querySelector('.trust-score-fill');
    const totalReportsValue = document.querySelectorAll('.stat-value')[1];
    const acceptedReportsValue = document.querySelectorAll('.stat-value')[2];
    const accuracyValue = document.querySelectorAll('.stat-value')[3];
    
    // Parse current values
    let currentScore = parseInt(trustScoreValue.textContent.split('/')[0]);
    let totalReports = parseInt(totalReportsValue.textContent);
    let acceptedReports = parseInt(acceptedReportsValue.textContent);
    
    // Update values
    totalReports++;
    
    if (accepted) {
        currentScore = Math.min(currentScore + 2, 100);
        acceptedReports++;
    } else {
        currentScore = Math.max(currentScore - 5, 0);
    }
    
    const accuracy = ((acceptedReports / totalReports) * 100).toFixed(1);
    
    // Update DOM
    trustScoreValue.textContent = `${currentScore} / 100`;
    trustScoreFill.style.width = `${currentScore}%`;
    totalReportsValue.textContent = totalReports;
    acceptedReportsValue.textContent = acceptedReports;
    accuracyValue.textContent = `${accuracy}%`;
    
    // Check if photo requirement should be removed
    checkUserTrustScore();
}

function checkUserTrustScore() {
    const trustScoreValue = document.querySelector('.stat-value');
    const photoUploadGroup = document.getElementById('photoUploadGroup');
    const requiredNotice = document.querySelector('.required-notice');
    
    if (trustScoreValue && photoUploadGroup) {
        const currentScore = parseInt(trustScoreValue.textContent.split('/')[0]);
        
        if (currentScore >= 80) {
            // High trust - photo not required
            requiredNotice.textContent = '✓ Güven puanınız yüksek! Fotoğraf zorunluluğu kalktı.';
            requiredNotice.style.color = '#27AE60';
            document.getElementById('photoUpload').removeAttribute('required');
        } else {
            // Low trust - photo required
            requiredNotice.textContent = '⚠️ Güven puanınız 80\'in altında olduğu için fotoğraf zorunludur';
            document.getElementById('photoUpload').setAttribute('required', 'required');
        }
    }
}

// ============== UTILITY FUNCTIONS ==============
async function convertFileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// ============== SEARCH FUNCTIONALITY ==============
const searchInput = document.querySelector('.search-input');
const searchButton = document.querySelector('.search-button');

if (searchButton) {
    searchButton.addEventListener('click', handleSearch);
}

if (searchInput) {
    searchInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            handleSearch();
        }
    });
}

function handleSearch() {
    const query = searchInput.value.trim();
    
    if (query.length > 0) {
        console.log('Searching for:', query);
        // In production, this would navigate to search results page
        // window.location.href = `/search?q=${encodeURIComponent(query)}`;
        alert(`Arama yapılıyor: "${query}"\n(Geliştirme aşamasında)`);
    }
}

// ============== PHOTO UPLOAD PREVIEW ==============
const photoUpload = document.getElementById('photoUpload');

if (photoUpload) {
    photoUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        const uploadLabel = document.querySelector('.upload-label span');
        
        if (file) {
            uploadLabel.textContent = `Seçildi: ${file.name}`;
            
            // Optional: Show image preview
            const reader = new FileReader();
            reader.onload = function(e) {
                console.log('Photo loaded:', file.name);
                // Could display preview here if desired
            };
            reader.readAsDataURL(file);
        }
    });
}

// ============== LEADERBOARD ANIMATION ==============
function animateLeaderboard() {
    const leaderboardRows = document.querySelectorAll('.leaderboard-table tbody tr');
    
    leaderboardRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            row.style.transition = 'all 0.5s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Trigger animation when leaderboard comes into view
const leaderboardSection = document.querySelector('.leaderboard-section');

if (leaderboardSection && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateLeaderboard();
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });
    
    observer.observe(leaderboardSection);
}

// ============== COMPARISON TABLE HIGHLIGHTING ==============
const comparisonRows = document.querySelectorAll('.comparison-table tbody tr');

comparisonRows.forEach(row => {
    row.addEventListener('mouseenter', function() {
        const changeCell = this.querySelector('.positive');
        if (changeCell) {
            changeCell.style.transform = 'scale(1.1)';
            changeCell.style.transition = 'transform 0.2s';
        }
    });
    
    row.addEventListener('mouseleave', function() {
        const changeCell = this.querySelector('.positive');
        if (changeCell) {
            changeCell.style.transform = 'scale(1)';
        }
    });
});

// ============== RESPONSIVE MENU (for mobile - future enhancement) ==============
console.log('Smart Waste Management System initialized');
console.log('Frontend loaded successfully');
