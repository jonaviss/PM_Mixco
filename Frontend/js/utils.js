/**
 * @file utils.js
 * @description Funciones compartidas de formato y utilería para todo el sistema.
 * @module Utils
 */

function formatearMoneda(valor) {
    return 'Q' + parseFloat(valor || 0).toLocaleString('es-GT', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatearFechaHora(fechaISO) {
    if (!fechaISO) return '—';
    return new Date(fechaISO).toLocaleString('es-GT', {
        timeZone: 'America/Guatemala',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatearFecha(fechaISO) {
    if (!fechaISO) return '—';
    return new Date(fechaISO).toLocaleString('es-GT', {
        timeZone: 'America/Guatemala',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function badgeEstado(estado) {
    const estilos = { pagado: 'bg-green-100 text-green-700', pendiente: 'bg-red-100 text-red-700', parcial: 'bg-amber-100 text-amber-700' };
    const etiquetas = { pagado: 'Pagado', pendiente: 'Pendiente', parcial: 'Parcial' };
    return `<span class="px-2 py-0.5 rounded-full text-xs font-bold ${estilos[estado] || 'bg-surface-container text-secondary'}">${etiquetas[estado] || estado}</span>`;
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay || 300);
    };
}
