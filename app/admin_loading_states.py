"""
Loading states and UI feedback components for admin interface.
Includes spinners, progress bars, skeleton loaders, and state management.
"""


def get_loading_states_css():
    """Return CSS for loading states and spinners."""
    return """
    <style>
    /* Loading spinners */
    .spinner-border {
        width: 1rem;
        height: 1rem;
        border: 0.25em solid;
        border-radius: 50%;
        border-top-color: currentColor;
        animation: spinner-border 0.75s linear infinite;
    }
    
    @keyframes spinner-border {
        to { transform: rotate(360deg); }
    }
    
    .spinner-grow {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        vertical-align: text-bottom;
        border-radius: 50%;
        animation: spinner-grow 0.75s linear infinite;
        opacity: 0.25;
    }
    
    @keyframes spinner-grow {
        0% { opacity: 0.25; transform: scale(0); }
        50% { opacity: 1; transform: scale(1); }
    }
    
    /* Loading overlay */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    
    .loading-overlay.active {
        display: flex;
    }
    
    .loading-content {
        background: white;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Progress bar */
    .progress {
        height: 1.5rem;
        overflow: hidden;
        border-radius: 0.25rem;
        background-color: #e9ecef;
    }
    
    .progress-bar {
        height: 100%;
        background-color: #007bff;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .progress-bar.bg-success {
        background-color: #28a745 !important;
    }
    
    .progress-bar.bg-warning {
        background-color: #ffc107 !important;
    }
    
    .progress-bar.bg-danger {
        background-color: #dc3545 !important;
    }
    
    /* Skeleton loader */
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 4px;
        height: 1rem;
        margin-bottom: 0.5rem;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .skeleton-avatar {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
    }
    
    .skeleton-text {
        height: 1rem;
    }
    
    .skeleton-title {
        height: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Loading state button */
    .btn.loading {
        pointer-events: none;
        opacity: 0.7;
    }
    
    .btn.loading .btn-text {
        display: none;
    }
    
    .btn.loading .spinner-border {
        display: inline-block;
        margin-right: 0.5rem;
    }
    
    /* Disabled state */
    .btn:disabled,
    .btn.loading {
        cursor: not-allowed;
        opacity: 0.65;
    }
    
    /* Loading toast */
    .toast.loading {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    
    .toast.loading .spinner-border {
        margin-right: 0.5rem;
    }
    </style>
    """


def get_loading_states_js():
    """Return JavaScript for managing loading states."""
    return """
    <script>
    // Loading state manager
    const LoadingStates = {
        // Show full-page loading overlay
        show(message = 'Loading...') {
            let overlay = document.getElementById('loading-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'loading-overlay';
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `
                    <div class="loading-content">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="text-muted" id="loading-message">${message}</p>
                    </div>
                `;
                document.body.appendChild(overlay);
            }
            overlay.classList.add('active');
            return overlay;
        },
        
        // Hide loading overlay
        hide() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.remove('active');
            }
        },
        
        // Set loading message
        setMessage(message) {
            const msgElement = document.getElementById('loading-message');
            if (msgElement) {
                msgElement.textContent = message;
            }
        },
        
        // Add loading state to button
        setButtonLoading(button, loading = true, text = 'Loading...') {
            if (loading) {
                button.disabled = true;
                button.classList.add('loading');
                const originalText = button.textContent;
                button.dataset.originalText = originalText;
                button.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    <span class="btn-text">${text}</span>
                `;
            } else {
                button.disabled = false;
                button.classList.remove('loading');
                button.textContent = button.dataset.originalText || button.textContent;
            }
        },
        
        // Show progress bar
        showProgress(element, currentValue = 0, maxValue = 100, message = '') {
            const progressHtml = `
                <div class="progress" style="height: 24px;">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${(currentValue / maxValue) * 100}%" 
                         aria-valuenow="${currentValue}" 
                         aria-valuemin="0" 
                         aria-valuemax="${maxValue}">
                        ${Math.round((currentValue / maxValue) * 100)}%
                    </div>
                </div>
                ${message ? `<small class="text-muted d-block mt-2">${message}</small>` : ''}
            `;
            element.innerHTML = progressHtml;
        },
        
        // Update progress bar
        updateProgress(element, currentValue, maxValue) {
            const progressBar = element.querySelector('.progress-bar');
            if (progressBar) {
                const percentage = (currentValue / maxValue) * 100;
                progressBar.style.width = percentage + '%';
                progressBar.setAttribute('aria-valuenow', currentValue);
                progressBar.textContent = Math.round(percentage) + '%';
            }
        },
        
        // Create skeleton loader
        createSkeleton(lines = 3) {
            let html = '';
            for (let i = 0; i < lines; i++) {
                html += '<div class="skeleton skeleton-text"></div>';
            }
            return html;
        },
        
        // Add skeleton to element
        showSkeleton(element, lines = 3) {
            element.innerHTML = this.createSkeleton(lines);
        },
        
        // Create table skeleton
        createTableSkeleton(rows = 5, cols = 4) {
            let html = '<tbody>';
            for (let r = 0; r < rows; r++) {
                html += '<tr>';
                for (let c = 0; c < cols; c++) {
                    html += '<td><div class="skeleton skeleton-text"></div></td>';
                }
                html += '</tr>';
            }
            html += '</tbody>';
            return html;
        },
        
        // Show toast notification with loading state
        showToast(message, type = 'info') {
            const toastHtml = `
                <div class="toast show loading" role="alert">
                    <div class="toast-body">
                        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                        ${message}
                    </div>
                </div>
            `;
            
            const container = document.getElementById('toast-container');
            if (!container) {
                const newContainer = document.createElement('div');
                newContainer.id = 'toast-container';
                newContainer.style.position = 'fixed';
                newContainer.style.top = '20px';
                newContainer.style.right = '20px';
                newContainer.style.zIndex = '9999';
                document.body.appendChild(newContainer);
            }
            
            const toastElement = document.createElement('div');
            toastElement.innerHTML = toastHtml;
            document.getElementById('toast-container').appendChild(toastElement);
            
            return toastElement.querySelector('.toast');
        }
    };
    
    // Form submission loading handler
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form[data-show-loading="true"]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitButton = this.querySelector('button[type="submit"]');
                if (submitButton) {
                    LoadingStates.setButtonLoading(submitButton, true);
                }
            });
        });
    });
    
    // AJAX loading handler
    document.addEventListener('DOMContentLoaded', function() {
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-ajax-load]')) {
                LoadingStates.show('Loading...');
            }
        });
    });
    </script>
    """


def get_loading_template_snippet():
    """Return template snippet for loading overlay."""
    return """
    <div id="loading-overlay" class="loading-overlay">
        <div class="loading-content">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted" id="loading-message">Loading...</p>
        </div>
    </div>
    """
