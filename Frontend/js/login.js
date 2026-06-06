/**
 * @file login.js
 * @description Lógica de autenticación para la pantalla de ingreso.
 */

document.addEventListener('DOMContentLoaded', () => {
    Auth.redirigirSiAutenticado();

    const form     = document.getElementById('loginForm');
    const errorMsg = document.getElementById('error-msg');

    function mostrarError(texto) {
        errorMsg.textContent = texto;
        errorMsg.classList.add('visible');
    }

    function ocultarError() {
        errorMsg.classList.remove('visible');
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        ocultarError();

        const cui = document.getElementById('cui').value.trim();

        try {
            const response = await API.post('/login', {
                cui,
                contrasena: document.getElementById('contrasena').value
            });

            if (response.ok) {
                const data = await response.json();
                // Guardar sesión incluyendo el CUI para uso en dashboards
                Auth.guardarSesion(
                    data.access_token,
                    data.nombre_completo,
                    data.rango,
                    data.modulos,
                    cui
                );
                window.location.href = 'libreria_dashboard.html';
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