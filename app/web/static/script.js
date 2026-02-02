// Basic JavaScript for metrics tracker

// Auto-hide messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.3s';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});

// Form validation helper
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.style.borderColor = 'var(--error)';
        } else {
            field.style.borderColor = '';
        }
    });
    
    return isValid;
}

// Clear form validation errors on input
document.addEventListener('input', function(e) {
    if (e.target.hasAttribute('required')) {
        e.target.style.borderColor = '';
    }
});