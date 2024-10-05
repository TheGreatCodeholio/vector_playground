function showAlert(message, type) {
    let toast_container = document.getElementById('toastContainer');
    console.log(message)
    const bgClass = {
        success: 'bg-success',
        warning: 'bg-warning',
        info: 'bg-info',
        danger: 'bg-danger'
    };

    const toastHtml = `<div class="toast align-items-center text-white border-0" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">
                                    <div class="d-flex ${bgClass[type] || 'bg-primary'}">
                                      <div class="toast-body">
                                        ${message}
                                      </div>
                                      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                                    </div>
                                  </div>`;

    toast_container.insertAdjacentHTML('beforeend', toastHtml);

    const toastEl = toast_container.lastElementChild;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    // The toast will automatically hide after 5 seconds due to data-bs-autohide and data-bs-delay
}

document.addEventListener('DOMContentLoaded', function () {
    const messages = document.querySelectorAll('.flash-message');
    messages.forEach(message => {
        const category = message.getAttribute('data-category');
        const msg = message.getAttribute('data-message');
        showAlert(msg, category);
    });
});