// Frontend/js/libreria.js
// --- REVISIÓN: Se añadió el listener para disparar la carga ---
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Verificamos seguridad
    Auth.requerirAutenticacion();
    // 2. Cargamos los datos
    await cargarProductos();
});

async function cargarProductos() {
    const tabla = document.getElementById('tabla-productos');
    
    try {
        // La ruta es correcta según main.py: prefijo /libreria + ruta /productos
        const response = await API.get('/libreria/productos', true);
        
        if (response.ok) {
            const productos = await response.json();
            
            if (!Array.isArray(productos) || productos.length === 0) {
                tabla.innerHTML = '<tr><td colspan="5" class="text-center py-4">No hay productos disponibles.</td></tr>';
                return;
            }

            tabla.innerHTML = ''; 
            
            productos.forEach(p => {
                const nombre = p.nombre || "Sin nombre";
                const precio = typeof p.precio === 'number' ? p.precio.toFixed(2) : "0.00";
                const stock = p.stock !== undefined ? p.stock : 0;
                const idCorto = p.id ? p.id.substring(0, 8) : "N/A";

                const fila = `
                    <tr class="border-b hover:bg-gray-50">
                        <td class="py-3 px-4">${idCorto}...</td>
                        <td class="py-3 px-4 font-medium">${nombre}</td>
                        <td class="py-3 px-4">Q${precio}</td>
                        <td class="py-3 px-4">${stock}</td>
                        <td class="py-3 px-4 text-center">
                            <button class="bg-blue-500 text-white px-3 py-1 rounded text-sm">Vender</button>
                        </td>
                    </tr>
                `;
                tabla.innerHTML += fila;
            });
        } else {
            tabla.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-red-500">Error: ' + response.status + '</td></tr>';
        }
    } catch (e) {
        tabla.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-red-500">Error de conexión</td></tr>';
    }
}