// Frontend/js/libreria.js

let cacheInventario = [];
let cacheClientes = []; 

document.addEventListener('DOMContentLoaded', async () => {
    Auth.requerirAutenticacion();
    
    const operador = localStorage.getItem('usuario') || 'Operador';
    document.getElementById('user-info').innerText = operador;
    document.getElementById('btnSalir').onclick = () => Auth.cerrarSesion();

    await cargarInventario();
    // await cargarClientes(); // Descomenta cuando tengas el módulo de clientes
    
    // configurarBuscadorProductos(); // Descomenta si tienes la función de búsqueda
});

// --- LÓGICA DE PESTAÑAS (SPA) ---
function cambiarVista(vistaTarget) {
    const vistas = ['inventario', 'pos', 'abonos'];
    
    vistas.forEach(v => {
        document.getElementById(`vista-${v}`).classList.add('hidden');
        const tab = document.getElementById(`tab-${v}`);
        tab.classList.remove('border-gold-dark', 'text-brand-text', 'font-semibold');
        tab.classList.add('border-transparent', 'text-brand-muted', 'font-medium');
    });

    document.getElementById(`vista-${vistaTarget}`).classList.remove('hidden');
    const tabActivo = document.getElementById(`tab-${vistaTarget}`);
    tabActivo.classList.remove('border-transparent', 'text-brand-muted', 'font-medium');
    tabActivo.classList.add('border-gold-dark', 'text-brand-text', 'font-semibold');
}

// --- CONEXIÓN AL BACKEND ---
async function cargarInventario() {
    try {
        const req = await API.get('/libreria/inventario', true);
        if (req.ok) {
            const data = await req.json();
            cacheInventario = data.data; // Tu backend devuelve { data: [...] }
            renderizarInventario(cacheInventario);
        } else {
            document.getElementById('inventario-list').innerHTML = '<div class="text-red-500 col-span-full">Error al cargar el inventario.</div>';
        }
    } catch (err) {
        document.getElementById('inventario-list').innerHTML = '<div class="text-red-500 col-span-full">Error de conexión con el servidor.</div>';
    }
}

// --- NUEVO RENDERIZADO DE TARJETAS (MODERNO) ---
function renderizarInventario(productos) {
    const contenedor = document.getElementById('inventario-list');
    contenedor.innerHTML = '';

    if (productos.length === 0) {
        contenedor.innerHTML = `
            <div class="col-span-full bg-brand-card border border-brand-border border-dashed rounded-xl p-10 text-center">
                <i data-lucide="package-open" class="w-10 h-10 text-brand-muted mx-auto mb-3"></i>
                <h3 class="text-lg font-bold text-brand-text mb-1">Inventario Vacío</h3>
                <p class="text-sm text-brand-muted">No hay productos registrados en el sistema actualmente.</p>
            </div>`;
        lucide.createIcons(); // Recargar iconos
        return;
    }

    productos.forEach(prod => {
        // Determinar color de stock
        const stockClass = prod.stock > 5 
            ? 'bg-green-100 text-green-700 border-green-200' 
            : 'bg-red-100 text-red-700 border-red-200';
            
        // Determinar icono según el tipo
        let icono = 'book'; // por defecto
        if(prod.tipo_producto.toLowerCase().includes('biblia')) icono = 'book-open';
        if(prod.tipo_producto.toLowerCase().includes('material')) icono = 'folder-open';

        // Crear la tarjeta HTML
        const cardHTML = `
            <div class="bg-brand-card border border-brand-border rounded-xl p-5 hover:shadow-md hover:border-gold/50 transition-all duration-200 flex flex-col group">
                <div class="flex justify-between items-start mb-4">
                    <div class="p-2.5 bg-brand-bg rounded-lg group-hover:bg-gold/10 transition-colors">
                        <i data-lucide="${icono}" class="w-5 h-5 text-brand-muted group-hover:text-gold-dark transition-colors"></i>
                    </div>
                    <span class="text-xs font-bold px-2.5 py-1 rounded-full border ${stockClass}">
                        Stock: ${prod.stock}
                    </span>
                </div>
                
                <h3 class="font-bold text-brand-text text-lg mb-1 truncate" title="${prod.nombre}">${prod.nombre}</h3>
                <p class="text-xs font-mono text-brand-muted mb-5 uppercase tracking-wider">${prod.tipo_producto}</p>
                
                <div class="mt-auto flex justify-between items-center pt-4 border-t border-brand-border">
                    <span class="text-xl font-bold text-brand-text">Q${Number(prod.precio).toFixed(2)}</span>
                    <button onclick="seleccionarParaPOS('${prod.id}', '${prod.nombre}')" class="w-8 h-8 flex items-center justify-center bg-brand-bg hover:bg-gold hover:text-white rounded text-brand-muted transition-all" title="Enviar al POS">
                        <i data-lucide="shopping-cart" class="w-4 h-4"></i>
                    </button>
                </div>
            </div>
        `;
        contenedor.innerHTML += cardHTML;
    });

    // IMPORTANTE: Decirle a la librería Lucide que dibuje los iconos de las nuevas tarjetas
    lucide.createIcons();
}

// --- FUNCIONES DEL MODAL ---
function abrirModalProducto() {
    document.getElementById('modal-producto').classList.remove('hidden');
}

function cerrarModalProducto() {
    document.getElementById('modal-producto').classList.add('hidden');
    // Limpiar campos
    document.getElementById('prod-nombre').value = '';
    document.getElementById('prod-precio').value = '';
    document.getElementById('prod-stock').value = '';
}

// --- FUNCIÓN DE EJEMPLO PARA ENVIAR AL POS ---
function seleccionarParaPOS(id, nombre) {
    cambiarVista('pos');
    const inputBusqueda = document.getElementById('pos-producto-search');
    if (inputBusqueda) {
        inputBusqueda.value = nombre;
        // Aquí puedes agregar la lógica para añadirlo directamente al carrito
        // agregarAlCarrito(id);
    }
}