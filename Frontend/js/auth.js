/**
 * @file auth.js
 * @description Módulo centralizado de autenticación del frontend.
 * Maneja sesión, redirecciones y cierre de sesión.
 */

const Auth = {

    /**
     * Guarda la sesión del usuario en localStorage.
     * @param {string} token - Token JWT
     * @param {string} nombre_completo - Nombre del usuario
     * @param {string} rango - Rango del usuario
     * @param {Array} modulos - Módulos habilitados
     * @param {string} cui - CUI del usuario
     */
    guardarSesion: (token, nombre_completo, rango, modulos, cui = '') => {
        localStorage.setItem('token', token);
        localStorage.setItem('usuario', nombre_completo);
        localStorage.setItem('rango', rango);
        localStorage.setItem('modulos', JSON.stringify(modulos));
        localStorage.setItem('cui', cui);
    },

    /**
     * Retorna los datos de la sesión activa.
     * @returns {Object|null} Datos de sesión o null si no hay sesión
     */
    getSesion: () => {
        const token = localStorage.getItem('token');
        if (!token) return null;
        return {
            token,
            nombre: localStorage.getItem('usuario'),
            rango: localStorage.getItem('rango'),
            modulos: JSON.parse(localStorage.getItem('modulos') || '[]'),
            cui: localStorage.getItem('cui')
        };
    },

    /**
     * Cierra la sesión y redirige al login.
     */
    cerrarSesion: () => {
        localStorage.clear();
        window.location.href = 'index.html';
    },

    /**
     * Verifica que haya una sesión activa. Si no, redirige al login.
     */
    requerirAutenticacion: () => {
        if (!localStorage.getItem('token')) {
            window.location.href = 'index.html';
        }
    },

    /**
     * Si ya hay sesión activa, redirige al dashboard según el rol.
     */
    redirigirSiAutenticado: () => {
        if (localStorage.getItem('token')) {
            const rango = localStorage.getItem('rango');
            window.location.href = rango === 'cliente' ? 'cliente_mis_compras.html' : 'libreria_dashboard.html';
        }
    }
};