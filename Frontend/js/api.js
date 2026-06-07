/**
 * @file api.js
 * @description Módulo centralizado de comunicación con el backend.
 * Todas las peticiones HTTP pasan por aquí.
 * Maneja automáticamente: token JWT, sesión expirada y errores de red.
 * 
 * Versión dinámica: detecta el entorno (local/producción) sin necesidad de modificar el archivo.
 */

// Función que determina la URL del backend según el dominio actual
function getApiUrl() {
    const hostname = window.location.hostname;
    
    // Si estamos en desarrollo local
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://127.0.0.1:8000';
    }
    
   
    const currentDomain = window.location.hostname;
    if (currentDomain.includes('onrender.com')) {
        // Reemplazar "frontend" por "backend" en el subdominio
        const backendDomain = currentDomain.replace('-frontend', '-backend');
        return `https://${backendDomain}`;
    }
    
    // Fallback: si no se detecta ningún patrón, usa la URL que prefieras (cámbiala si es necesario)
    return 'https://tu-backend.onrender.com';  // <-- Cambia esto por tu URL real de backend en producción si el patrón anterior no funciona
}

// Configuración global
const CONFIG = {
    API_URL: getApiUrl(),
    APP_NOMBRE: "PM Mixco ERP",
    APP_VERSION: "2.0.0"
};

/**
 * Muestra un mensaje de sesión expirada y redirige al login.
 * Se ejecuta automáticamente cuando el backend retorna 401.
 */
function manejarSesionExpirada() {
    localStorage.clear();

    // Crear toast de notificación
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        background: #1c1c1a; color: #fff; padding: 14px 20px;
        border-radius: 10px; font-family: 'Sora', sans-serif;
        font-size: 13px; font-weight: 600; max-width: 320px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        border-left: 4px solid #C9A227;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = 'Su sesión ha expirado. Será redirigido al inicio de sesión.';
    document.body.appendChild(toast);

    setTimeout(() => {
        window.location.href = 'index.html';
    }, 2000);
}

const API = {

    /**
     * Realiza una petición GET al backend.
     * @param {string} endpoint - Ruta del endpoint (ej: '/libreria/productos')
     * @param {boolean} requerirToken - Si true, agrega el token JWT al header
     * @returns {Promise<Response>} Respuesta del servidor
     */
    get: async (endpoint, requerirToken = true) => {
        const headers = {};

        if (requerirToken) {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = 'index.html';
                return;
            }
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
                method: 'GET',
                headers
            });

            if (response.status === 401) {
                manejarSesionExpirada();
                return response;
            }

            return response;

        } catch (err) {
            console.error(`[API] Error de red en GET ${endpoint}:`, err);
            throw new Error('No se pudo conectar con el servidor. Verifica tu red.');
        }
    },

    /**
     * Realiza una petición POST al backend.
     * @param {string} endpoint - Ruta del endpoint
     * @param {Object} datos - Cuerpo de la petición
     * @param {boolean} requerirToken - Si true, agrega el token JWT al header
     * @returns {Promise<Response>} Respuesta del servidor
     */
    post: async (endpoint, datos, requerirToken = false) => {
        const headers = { 'Content-Type': 'application/json' };

        if (requerirToken) {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = 'index.html';
                return;
            }
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
                method: 'POST',
                headers,
                body: JSON.stringify(datos)
            });

            if (response.status === 401 && requerirToken) {
                manejarSesionExpirada();
                return response;
            }

            return response;

        } catch (err) {
            console.error(`[API] Error de red en POST ${endpoint}:`, err);
            throw new Error('No se pudo conectar con el servidor. Verifica tu red.');
        }
    },

    /**
     * Realiza una petición PUT al backend.
     * @param {string} endpoint - Ruta del endpoint
     * @param {Object} datos - Cuerpo de la petición
     * @returns {Promise<Response>} Respuesta del servidor
     */
    put: async (endpoint, datos) => {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('token');

        if (!token) {
            window.location.href = 'index.html';
            return;
        }
        headers['Authorization'] = `Bearer ${token}`;

        try {
            const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
                method: 'PUT',
                headers,
                body: JSON.stringify(datos)
            });

            if (response.status === 401) {
                manejarSesionExpirada();
                return response;
            }

            return response;

        } catch (err) {
            console.error(`[API] Error de red en PUT ${endpoint}:`, err);
            throw new Error('No se pudo conectar con el servidor. Verifica tu red.');
        }
    },

    /**
     * Realiza una petición DELETE al backend.
     * @param {string} endpoint - Ruta del endpoint
     * @returns {Promise<Response>} Respuesta del servidor
     */
    delete: async (endpoint) => {
        const token = localStorage.getItem('token');

        if (!token) {
            window.location.href = 'index.html';
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.status === 401) {
                manejarSesionExpirada();
                return response;
            }

            return response;

        } catch (err) {
            console.error(`[API] Error de red en DELETE ${endpoint}:`, err);
            throw new Error('No se pudo conectar con el servidor. Verifica tu red.');
        }
    },

    /**
     * Formatea un mensaje de error del backend en texto legible.
     * @param {Object} data - Respuesta JSON del backend
     * @returns {string} Mensaje de error formateado
     */
    mensajeError: (data) => {
        if (!data) return 'Error desconocido.';
        if (Array.isArray(data.detail)) return data.detail.map(e => e.msg).join(', ');
        return data.detail || 'Error al procesar la solicitud.';
    }
};