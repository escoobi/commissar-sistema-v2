// Main JavaScript for Comissão App

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bulma components
    initializeBulmaComponents();
});

function initializeBulmaComponents() {
    // Close notifications
    document.querySelectorAll('.notification .delete').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.parentElement.removeChild(this.parentElement);
        });
    });
    
    // Mobile navbar toggle
    const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    $navbarBurgers.forEach($el => {
        $el.addEventListener('click', () => {
            const target = $el.dataset.target;
            const $target = document.getElementById(target);
            $el.classList.toggle('is-active');
            $target.classList.toggle('is-active');
        });
    });
}

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification is-${type}`;
    notification.innerHTML = `
        <button class="delete"></button>
        ${message}
    `;
    
    document.body.insertBefore(notification, document.body.firstChild);
    
    notification.querySelector('.delete').addEventListener('click', function() {
        notification.remove();
    });
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'loader';
    loader.id = 'main-loader';
    loader.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('main-loader');
    if (loader) {
        loader.remove();
    }
}
