// Dashboard initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    updateStats();
    loadRecentActivity();
    
    // Update data every 30 seconds
    setInterval(() => {
        updateStats();
        loadRecentActivity();
    }, 30000);
});

// Initialize charts
function initializeCharts() {
    // Content Protection Overview Chart
    const contentCtx = document.getElementById('contentChart').getContext('2d');
    new Chart(contentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Protected', 'Processing', 'Unprotected'],
            datasets: [{
                data: [70, 10, 20],
                backgroundColor: [
                    'rgb(34, 197, 94)',
                    'rgb(59, 130, 246)',
                    'rgb(249, 115, 22)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Detection Activity Chart
    const activityCtx = document.getElementById('activityChart').getContext('2d');
    new Chart(activityCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Violations Detected',
                data: [12, 19, 3, 5, 2, 3],
                borderColor: 'rgb(239, 68, 68)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Update dashboard statistics
async function updateStats() {
    try {
        const response = await fetch('/api/v1/dashboard/stats');
        const data = await response.json();
        
        document.getElementById('totalContent').textContent = data.total_content;
        document.getElementById('protectedContent').textContent = data.protected_content;
        document.getElementById('violations').textContent = data.violations;
        document.getElementById('detectionRate').textContent = `${data.detection_rate}%`;
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/v1/dashboard/activity');
        const activities = await response.json();
        
        const activityList = document.getElementById('activityList');
        activityList.innerHTML = ''; // Clear existing items
        
        activities.forEach(activity => {
            const li = document.createElement('li');
            li.className = 'p-4';
            li.innerHTML = `
                <div class="flex space-x-3">
                    <div class="flex-1 space-y-1">
                        <div class="flex items-center justify-between">
                            <h3 class="text-sm font-medium">${activity.title}</h3>
                            <p class="text-sm text-gray-500">${activity.time}</p>
                        </div>
                        <p class="text-sm text-gray-500">${activity.description}</p>
                    </div>
                </div>
            `;
            activityList.appendChild(li);
        });
    } catch (error) {
        console.error('Failed to load activity:', error);
    }
}

// Handle content upload
async function uploadContent(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/v1/content/register', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            updateStats();
            loadRecentActivity();
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Failed to upload content:', error);
    }
}

// Handle content verification
async function verifyContent(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/v1/content/verify', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    } catch (error) {
        console.error('Failed to verify content:', error);
        return null;
    }
}
