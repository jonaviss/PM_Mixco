// Frontend/js/libreria.js

let cacheInventario = [];
let cacheClientes = []; // Almacena el listado de hermanos

document.addEventListener('DOMContentLoaded', async () => {
    Auth.requerirAutenticacion();
    
    const operador = localStorage.getItem('usuario') || 'Operador';
    document.getElementById('user-info').innerText = operador;
    document.getElementById('btnSalir').onclick = () => Auth.cerrarSesion();

    await cargarInventario();
    await cargarClientes(); // Cargamos a los hermanos al iniciar
    
    configurarBuscadorProductos();
    configurarBuscadorClientes();
});

// --- LÓGICA DE PESTAÑAS (SPA) ---
function cambiarVista(vistaTarget) {
    const vistas = ['inventario', 'pos', 'abonos'];
    
    vistas.forEach(v => {
        document.getElementById(`vista-${v}`).classList.add('hidden');
        const tab = document.getElementById(`tab-${v}`);
        tab.classList.remove('border-blue-600', 'font-bold', 'text-blue-800');
        tab.classList.add('border-transparent', 'text-gray-500');
    });

    document.getElementById(`vista-${vistaTarget}`).classList.remove('hidden');
    const tabActivo = document.getElementById(`tab-${vistaTarget}`);
    tabActivo.classList.remove('border-transparent', 'text-gray-500');
    tabActivo.classList.add('border-blue-600', 'font-bold', 'text-blue-800');
}

// --- DESCARGA DE DATOS AL CACHÉ ---
async function cargarInventario() {
    const tbody = document.getElementById('tabla-productos');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-10 text-slate-500 font-medium">Cargando...</td></tr>';
    
    try {
        const req = await API.get('/libreria/productos', true);
        if (!req.ok) throw new Error(`HTTP ${req.status}`);

        cacheInventario = await req.json(); 
        
        if (cacheInventario.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-10 text-slate-500">No hay productos en el catálogo.</td></tr>';
            return;
        }

        tbody.innerHTML = ''; 
        cacheInventario.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-blue-50 transition-colors duration-150';
            
            const claseStock = item.stock < 5 ? 'text-red-600 font-black bg-red-100 py-1 px-2 rounded' : 'text-slate-700 font-bold';
            const idCorto = item.id.substring(0, 8) + '...';

            row.innerHTML = `
                <td class="py-4 px-6 text-slate-500 font-mono text-xs" title="${item.id}">${idCorto}</td>
                <td class="py-4 px-6 font-bold text-blue-900">${item.nombre}</td>
                <td class="py-4 px-6 text-slate-600"><span class="bg-slate-200 px-2 py-1 rounded text-xs">${item.tipo_producto}</span></td>
                <td class="py-4 px-6 font-medium">Q${item.precio.toFixed(2)}</td>
                <td class="py-4 px-6 text-center"><span class="${claseStock}">${item.stock}</span></td>
            `;
            tbody.appendChild(row);
        });

    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-10 text-red-500 font-bold">Error al conectar con la base de datos</td></tr>';
    }
}

async function cargarClientes() {
    try {
        const req = await API.get('/libreria/clientes', true);
        if (req.ok) {
            cacheClientes = await req.json();
        }
    } catch (err) {
        console.error("No se pudo cargar el listado de hermanos.", err);
    }
}

// --- LÓGICA DEL MODAL (NUEVO PRODUCTO) ---
function abrirModalProducto() {
    document.getElementById('modal-producto').classList.remove('hidden');
    document.getElementById('msg-modal').classList.add('hidden');
}

function cerrarModalProducto() {
    document.getElementById('modal-producto').classList.add('hidden');
    document.getElementById('prod-nombre').value = '';
    document.getElementById('prod-desc').value = '';
    document.getElementById('prod-precio').value = '';
    document.getElementById('prod-stock').value = ''; 
}

async function guardarProducto() {
    const btnGuardar = document.querySelector('#modal-producto button.bg-green-600');
    
    const tipo = document.getElementById('prod-tipo').value;
    const nombre = document.getElementById('prod-nombre').value.trim();
    const desc = document.getElementById('prod-desc').value.trim();
    const precio = parseFloat(document.getElementById('prod-precio').value);
    const stock = parseInt(document.getElementById('prod-stock').value);

    if (!nombre || isNaN(precio) || precio <= 0 || isNaN(stock) || stock < 0) {
        mostrarMsgModal('Por favor, ingresa un nombre, un precio válido mayor a 0 y el stock inicial exacto.', 'error');
        return;
    }

    btnGuardar.disabled = true;
    btnGuardar.innerText = 'Guardando...';

    const payload = {
        tipo_producto: tipo,
        nombre: nombre,
        descripcion: desc,
        precio: precio,
        stock: stock,
        estado: true
    };

    try {
        const req = await API.post('/libreria/productos', payload, true);
        if (req.ok) {
            cerrarModalProducto();
            await cargarInventario(); 
        } else {
            const data = await req.json();
            mostrarMsgModal(`Error: ${data.detail || 'Verifica los campos'}`, 'error');
        }
    } catch (e) {
        mostrarMsgModal('Error de servidor.', 'error');
    } finally {
        btnGuardar.disabled = false;
        btnGuardar.innerText = 'Guardar Producto';
    }
}

function mostrarMsgModal(texto, tipo) {
    const msg = document.getElementById('msg-modal');
    msg.textContent = texto;
    msg.className = `px-4 py-2 rounded mb-4 text-sm font-bold block ${tipo === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
}

// --- BUSCADORES PREDICTIVOS DEL POS ---
function configurarBuscadorProductos() {
    const inputBusqueda = document.getElementById('pos-producto-search');
    const cajaResultados = document.getElementById('pos-producto-results');

    inputBusqueda.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        cajaResultados.innerHTML = '';
        
        if (!query) {
            document.getElementById('pos-producto-id').value = '';
            cajaResultados.classList.add('hidden');
            return;
        }

        const resultados = cacheInventario.filter(p => p.nombre.toLowerCase().includes(query));

        if (resultados.length === 0) {
            cajaResultados.innerHTML = '<div class="p-4 text-slate-500 text-sm text-center">No se encontraron coincidencias.</div>';
        } else {
            resultados.forEach(p => {
                const item = document.createElement('div');
                item.className = 'p-3 cursor-pointer hover:bg-blue-50 transition border-b border-slate-100 last:border-0';
                
                const stockAlert = p.stock <= 0 ? `<span class="text-red-600 text-xs ml-2 font-bold">(Sin Stock)</span>` : '';

                item.innerHTML = `
                    <div class="font-bold text-slate-800">${p.nombre} ${stockAlert}</div>
                    <div class="text-xs text-slate-500 flex justify-between mt-1">
                        <span>Categoría: ${p.tipo_producto}</span>
                        <span class="font-bold text-green-700">Q${p.precio.toFixed(2)}</span>
                    </div>
                `;
                item.onclick = () => {
                    document.getElementById('pos-producto-id').value = p.id;
                    inputBusqueda.value = p.nombre; 
                    cajaResultados.classList.add('hidden');
                };
                cajaResultados.appendChild(item);
            });
        }
        cajaResultados.classList.remove('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!inputBusqueda.contains(e.target) && !cajaResultados.contains(e.target)) {
            cajaResultados.classList.add('hidden');
        }
    });
}

function configurarBuscadorClientes() {
    const inputBusqueda = document.getElementById('pos-cliente-search');
    const cajaResultados = document.getElementById('pos-cliente-results');

    inputBusqueda.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        cajaResultados.innerHTML = '';
        
        if (!query) {
            cajaResultados.classList.add('hidden');
            return;
        }

        // Búsqueda híbrida por CUI o Nombre Completo
        const resultados = cacheClientes.filter(c => {
            const nombre = (c.nombre_completo || c.nombres + ' ' + c.apellidos || '').toLowerCase();
            const cui = (c.cui || '').toLowerCase();
            return nombre.includes(query) || cui.includes(query);
        });

        if (resultados.length === 0) {
            cajaResultados.innerHTML = '<div class="p-4 text-slate-500 text-sm text-center">Hermano no encontrado.</div>';
        } else {
            resultados.forEach(c => {
                const item = document.createElement('div');
                item.className = 'p-3 cursor-pointer hover:bg-blue-50 transition border-b border-slate-100 last:border-0';
                
                const nombreMostrar = c.nombre_completo || c.nombres + ' ' + c.apellidos;

                item.innerHTML = `
                    <div class="font-bold text-slate-800">${nombreMostrar}</div>
                    <div class="text-xs text-slate-500 mt-1">CUI: <span class="font-mono">${c.cui}</span></div>
                `;
                item.onclick = () => {
                    seleccionarCliente(c.cui, nombreMostrar);
                    cajaResultados.classList.add('hidden');
                };
                cajaResultados.appendChild(item);
            });
        }
        cajaResultados.classList.remove('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!inputBusqueda.contains(e.target) && !cajaResultados.contains(e.target)) {
            cajaResultados.classList.add('hidden');
        }
    });
}

// --- CONFIRMACIÓN VISUAL DE HERMANO ---
function seleccionarCliente(cui, nombre) {
    document.getElementById('contenedor-buscador-cliente').classList.add('hidden');
    document.getElementById('pos-cui-hidden').value = cui;
    
    document.getElementById('card-cliente-nombre').innerText = nombre;
    document.getElementById('card-cliente-cui').innerText = `CUI: ${cui}`;
    document.getElementById('pos-cliente-card').classList.remove('hidden');
}

function limpiarCliente() {
    document.getElementById('pos-cui-hidden').value = '';
    document.getElementById('pos-cliente-card').classList.add('hidden');
    
    const buscador = document.getElementById('contenedor-buscador-cliente');
    buscador.classList.remove('hidden');
    
    const input = document.getElementById('pos-cliente-search');
    input.value = '';
    input.focus();
}

// --- LÓGICA DE PROCESAMIENTO (POS) ---
async function procesarVenta(tipoPago) {
    const productoId = document.getElementById('pos-producto-id').value;
    const compradorCui = document.getElementById('pos-cui-hidden').value;
    const cantidad = parseInt(document.getElementById('pos-cantidad').value);

    if (!productoId) {
        mostrarMensajeVenta('Debes buscar y seleccionar un producto de la lista.', 'error');
        return;
    }
    if (!compradorCui) {
        mostrarMensajeVenta('Debes buscar y confirmar al hermano antes de cobrar.', 'error');
        return;
    }
    if (isNaN(cantidad) || cantidad <= 0) {
        mostrarMensajeVenta('Ingresa una cantidad válida mayor a cero.', 'error');
        return;
    }

    const payload = {
        producto_id: productoId,
        comprador_cui: compradorCui,
        cantidad: cantidad,
        tipo_pago: tipoPago
    };

    try {
        const req = await API.post('/libreria/ventas', payload, true);
        const data = await req.json();

        if (req.ok) {
            mostrarMensajeVenta(`✅ Transacción exitosa. Notificación por correo despachada.`, 'success');
            
            document.getElementById('pos-producto-id').value = '';
            document.getElementById('pos-producto-search').value = '';
            document.getElementById('pos-cantidad').value = '1';
            limpiarCliente();
            
            await cargarInventario(); 
        } else {
            // Fix: data.detail puede ser string o lista de errores de Pydantic
            const detalle = Array.isArray(data.detail)
                ? data.detail.map(e => e.msg).join(', ')
                : (data.detail || 'Error desconocido');
            mostrarMensajeVenta(`Error: ${detalle}`, 'error');
        }
    } catch (err) {
        mostrarMensajeVenta('Error de servidor al procesar la venta.', 'error');
    }
}

function mostrarMensajeVenta(mensaje, tipo) {
    const msgBox = document.getElementById('msg-venta');
    msgBox.textContent = mensaje;
    msgBox.className = `px-4 py-3 rounded mb-6 text-sm font-bold shadow-sm block ${tipo === 'error' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`;
    setTimeout(() => { msgBox.classList.add('hidden'); }, 4000);
}