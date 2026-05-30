// Frontend/js/login.js
document.addEventListener('DOMContentLoaded', () => {
    Auth.redirigirSiAutenticado();
    const form = document.getElementById('loginForm');
    const errorMsg = document.getElementById('error-msg');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorMsg.classList.add('hidden');

        try {
            const response = await API.post('/login', { 
                cui: document.getElementById('cui').value, 
                contrasena: document.getElementById('contrasena').value 
            });

            if (response.ok) {
                const data = await response.json();
                Auth.guardarSesion(data.access_token, data.nombre_completo, data.rango, data.modulos);
                window.location.href = 'libreria.html';
            } else {
                errorMsg.classList.remove('hidden');
            }
        } catch (error) {
            errorMsg.textContent = "Error al conectar con el servidor.";
            errorMsg.classList.remove('hidden');
        }
    });
});