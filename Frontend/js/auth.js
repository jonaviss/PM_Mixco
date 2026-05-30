// Frontend/js/auth.js
const Auth = {
    guardarSesion: (token, nombre_completo, rango, modulos) => {
        localStorage.setItem('token', token);
        localStorage.setItem('usuario', nombre_completo);
        localStorage.setItem('rango', rango);
        // Guardamos los módulos como un texto JSON
        localStorage.setItem('modulos', JSON.stringify(modulos));
    },

    cerrarSesion: () => {
        localStorage.clear();
        window.location.href = 'index.html';
    },

    requerirAutenticacion: () => {
        if (!localStorage.getItem('token')) {
            window.location.href = 'index.html';
        }
    },

    redirigirSiAutenticado: () => {
        if (localStorage.getItem('token')) {
            window.location.href = 'libreria.html';
        }
    }
};