/**
 * @file login.js
 * @description Lógica de autenticación para la pantalla de ingreso.
 * @module Login
 */

document.addEventListener('DOMContentLoaded', () => {
    Auth.redirigirSiAutenticado();

    const form     = document.getElementById('loginForm');
    const errorMsg = document.getElementById('error-msg');

    /**
     * Muestra el mensaje de error en pantalla.
     * @param {string} texto - Mensaje a mostrar al usuario
     */
    function mostrarError(texto) {
        errorMsg.textContent = texto;
        errorMsg.classList.add('visible');
    }

    /**
     * Oculta el mensaje de error.
     */
    function ocultarError() {
        errorMsg.classList.remove('visible');
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        ocultarError();

        try {
            const response = await API.post('/login', {
                cui:       document.getElementById('cui').value.trim(),
                contrasena: document.getElementById('contrasena').value
            });

            if (response.ok) {
                const data = await response.json();
                Auth.guardarSesion(data.access_token, data.nombre_completo, data.rango, data.modulos);
                window.location.href = 'libreria.html';
            } else {
                const data = await response.json();
                mostrarError(data.detail || 'CUI o contraseña incorrectos.');
            }

        } catch (error) {
            console.error('[Login] Error de conexión:', error);
            mostrarError('No se pudo conectar con el servidor. Verifica tu red.');
        }
    });
});