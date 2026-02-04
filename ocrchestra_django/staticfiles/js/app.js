// OCRchestra Django - JavaScript
// Auto-fading messages
document.addEventListener('DOMContentLoaded', function () {
    // Auto-close messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Add close buttons to alerts
    alerts.forEach(alert => {
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = 'float: right; font-size: 24px; cursor: pointer; margin-left: 15px;';
        closeBtn.onclick = () => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        };
        alert.insertBefore(closeBtn, alert.firstChild);
    });
});

// Task status polling (for async processing)
function pollTaskStatus(taskId) {
    const statusInterval = setInterval(() => {
        fetch(`/task/${taskId}/`)
            .then(res => res.json())
            .then(data => {
                console.log('Task status:', data);

                if (data.status === 'COMPLETED') {
                    clearInterval(statusInterval);
                    // Reload page or update UI
                    window.location.reload();
                } else if (data.status === 'FAILED') {
                    clearInterval(statusInterval);
                    alert('İşlem başarısız: ' + data.error);
                }
            })
            .catch(err => {
                console.error('Status check failed:', err);
            });
    }, 3000); // Poll every 3 seconds
}

// Export helper
function exportDocument(docId, format) {
    window.location.href = `/export/${docId}/?format=${format}`;
}

// Search debouncing
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
