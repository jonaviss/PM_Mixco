/**
 * @file notify.js
 * @description Sistema de notificaciones (toasts) estandarizado para todo el sistema.
 */

// Contenedor de toasts (se crea si no existe)
let toastContainer = null;

function obtenerContenedor() {
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
    }
    return toastContainer;
}

/**
 * Muestra una notificación toast.
 * @param {string} mensaje - Texto a mostrar
 * @param {string} tipo - 'success', 'error', 'warning', 'info'
 * @param {number} duracion - Milisegundos (default 4000)
 */
function mostrarToast(mensaje, tipo = 'info', duracion = 4000) {
    const container = obtenerContenedor();
    const toast = document.createElement('div');
    
    // Configurar color y estilo según tipo
    let colorBg, colorBorder, icono;
    switch (tipo) {
        case 'success':
            colorBg = '#10B981';
            colorBorder = '#059669';
            icono = 'check_circle';
            break;
        case 'error':
            colorBg = '#EF4444';
            colorBorder = '#DC2626';
            icono = 'error';
            break;
        case 'warning':
            colorBg = '#F59E0B';
            colorBorder = '#D97706';
            icono = 'warning';
            break;
        default: // info
            colorBg = '#3B82F6';
            colorBorder = '#2563EB';
            icono = 'info';
    }
    
    toast.style.cssText = `
        background: white;
        border-left: 4px solid ${colorBorder};
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 12px 16px;
        min-width: 260px;
        max-width: 350px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: 'Sora', sans-serif;
        font-size: 0.875rem;
        color: #1E293B;
        animation: slideIn 0.3s ease;
        margin-bottom: 8px;
    `;
    
    toast.innerHTML = `
        <span class="material-symbols-outlined" style="color: ${colorBg}; font-size: 22px;">${icono}</span>
        <span style="flex: 1;">${mensaje}</span>
        <button class="toast-close" style="background: none; border: none; cursor: pointer; color: #94A3B8; font-size: 16px; display: flex; align-items: center;">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Botón cerrar
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        toast.remove();
    });
    
    // Auto cierre
    const timeout = setTimeout(() => {
        toast.remove();
    }, duracion);
    
    // Pausar timeout al pasar el mouse
    toast.addEventListener('mouseenter', () => clearTimeout(timeout));
    toast.addEventListener('mouseleave', () => {
        // No se vuelve a poner timeout para evitar acumulación; la notificación se cierra manualmente
    });
}

// Animación CSS
if (!document.querySelector('#toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .toast-close:hover {
            color: #EF4444 !important;
        }
    `;
    document.head.appendChild(style);
}

// Exportar funciones globales
window.notify = {
    success: (msg, duration) => mostrarToast(msg, 'success', duration),
    error: (msg, duration) => mostrarToast(msg, 'error', duration),
    warning: (msg, duration) => mostrarToast(msg, 'warning', duration),
    info: (msg, duration) => mostrarToast(msg, 'info', duration)
};