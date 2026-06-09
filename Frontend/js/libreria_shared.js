/**
 * @file libreria_shared.js
 * @description Funciones y componentes compartidos entre las páginas del módulo de librería.
 * Incluye el modal de detalle de venta reutilizable en cobros y clientes.
 * @module LibreriaShared
 */

/**
 * Formatea un valor numérico como moneda en Quetzales.
 * @param {number} valor
 * @returns {string}
 */
function formatearMoneda(valor) {
    return 'Q' + parseFloat(valor || 0).toLocaleString('es-GT', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Formatea una fecha ISO al formato DD/MM/YYYY HH:MM zona Guatemala.
 * @param {string} fechaISO
 * @returns {string}
 */
function formatearFechaHora(fechaISO) {
    if (!fechaISO) return '—';
    return new Date(fechaISO).toLocaleString('es-GT', {
        timeZone: 'America/Guatemala',
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

/**
 * Inyecta el HTML del modal de detalle de venta en el documento.
 * Debe llamarse antes de usar abrirDetalleVenta().
 */
function inyectarModalDetalle() {
    if (document.getElementById('modal-detalle')) return;

    const modal = document.createElement('div');
    modal.id = 'modal-detalle';
    modal.className = 'fixed inset-0 bg-black/50 hidden items-center justify-center z-50 p-4 backdrop-blur-sm';
    modal.innerHTML = `
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">

            <div class="bg-primary px-5 py-4 flex justify-between items-center flex-shrink-0" style="background-color: #755b00;">
                <div>
                    <h3 class="text-base font-bold text-white">Detalle de Transacción</h3>
                    <p id="modal-venta-id" class="text-xs font-mono text-white/70 mt-0.5"></p>
                </div>
                <button onclick="cerrarDetalleVenta()" class="text-white/70 hover:text-white transition">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="overflow-y-auto flex-1 p-5 space-y-5">

                <!-- Resumen -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <p class="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Total Venta</p>
                        <p id="modal-total-venta" class="text-base font-bold font-mono text-gray-800">—</p>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <p class="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Total Pagado</p>
                        <p id="modal-total-pagado" class="text-base font-bold font-mono text-gray-800">—</p>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <p class="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Saldo Pendiente</p>
                        <p id="modal-saldo" class="text-base font-bold font-mono">—</p>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <p class="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Registrado por</p>
                        <p id="modal-operador" class="text-sm font-bold text-gray-800">—</p>
                    </div>
                </div>

                <!-- Deuda total del hermano -->
                <div id="modal-deuda-container" class="hidden bg-red-50 border border-red-200 rounded-xl p-4">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="material-symbols-outlined text-red-600 text-[18px]">warning</span>
                        <p class="text-xs font-mono font-bold text-red-600 uppercase tracking-wider">Estado de Cuenta del Hermano</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <p class="text-xs text-red-500 mb-0.5">Deuda Total</p>
                            <p id="modal-deuda-total" class="text-lg font-bold text-red-700 font-mono">—</p>
                        </div>
                        <div>
                            <p class="text-xs text-red-500 mb-0.5">Ventas Pendientes</p>
                            <p id="modal-deuda-cantidad" class="text-lg font-bold text-red-700">—</p>
                        </div>
                    </div>
                </div>

                <!-- Productos -->
                <div>
                    <h4 class="text-xs font-mono font-bold text-gray-500 uppercase tracking-wider mb-2">Productos Comprados</h4>
                    <div class="border border-gray-200 rounded-xl overflow-hidden">
                        <table class="w-full text-left">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase">Producto</th>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase text-center">Cant.</th>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase text-right">Precio Unit.</th>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase text-right">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody id="modal-productos" class="divide-y divide-gray-100 text-sm"></tbody>
                        </table>
                    </div>
                </div>

                <!-- Pagos -->
                <div>
                    <h4 class="text-xs font-mono font-bold text-gray-500 uppercase tracking-wider mb-2">Pagos Registrados</h4>
                    <div class="border border-gray-200 rounded-xl overflow-hidden">
                        <table class="w-full text-left">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase">Fecha / Hora</th>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase">Cobrado por</th>
                                    <th class="px-4 py-2 text-xs font-mono font-bold text-gray-500 uppercase text-right">Monto</th>
                                </tr>
                            </thead>
                            <tbody id="modal-pagos" class="divide-y divide-gray-100 text-sm"></tbody>
                        </table>
                    </div>
                </div>

            </div>

            <div class="px-5 py-3 border-t border-gray-200 bg-gray-50 flex-shrink-0">
                <button onclick="cerrarDetalleVenta()" class="px-5 py-2 text-sm font-bold text-gray-500 hover:bg-gray-200 rounded-lg transition">
                    Cerrar
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Abre el modal con el detalle completo de una venta.
 * @async
 * @param {string} ventaId - UUID de la venta
 */
async function abrirDetalleVenta(ventaId) {
    inyectarModalDetalle();

    const modal = document.getElementById('modal-detalle');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    document.getElementById('modal-venta-id').textContent = `ID: ${ventaId}`;
    document.getElementById('modal-productos').innerHTML =
        '<tr><td colspan="4" class="text-center py-4 text-gray-500 text-sm">Cargando...</td></tr>';
    document.getElementById('modal-pagos').innerHTML =
        '<tr><td colspan="3" class="text-center py-4 text-gray-500 text-sm">Cargando...</td></tr>';
    document.getElementById('modal-deuda-container').classList.add('hidden');

    try {
        const res = await API.get(`/libreria/ventas/${ventaId}/detalle`, true);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const v = data.venta;

        document.getElementById('modal-total-venta').textContent = formatearMoneda(v.total_venta);
        document.getElementById('modal-total-pagado').textContent = formatearMoneda(v.total_pagado);
        document.getElementById('modal-operador').textContent = v.operador || '—';

        const saldoEl = document.getElementById('modal-saldo');
        saldoEl.textContent = formatearMoneda(v.saldo_pendiente);
        saldoEl.className = `text-base font-bold font-mono ${v.saldo_pendiente > 0 ? 'text-red-600' : 'text-green-600'}`;

        // Mostrar deuda total del hermano si tiene saldo pendiente
        if (data.deuda_hermano && data.deuda_hermano.total > 0) {
            document.getElementById('modal-deuda-total').textContent = formatearMoneda(data.deuda_hermano.total);
            document.getElementById('modal-deuda-cantidad').textContent =
                `${data.deuda_hermano.cantidad} venta(s)`;
            document.getElementById('modal-deuda-container').classList.remove('hidden');
        }

        // Renderizar productos
        const tbodyProductos = document.getElementById('modal-productos');
        if (!data.productos || data.productos.length === 0) {
            tbodyProductos.innerHTML =
                '<tr><td colspan="4" class="text-center py-4 text-gray-500 text-sm">Sin detalle de productos.</td></tr>';
        } else {
            tbodyProductos.innerHTML = '';
            data.productos.forEach(p => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50 transition-colors';
                tr.innerHTML = `
                    <td class="px-4 py-2.5">
                        <p class="font-bold text-gray-800 text-sm">${p.nombre}</p>
                        <p class="text-xs text-gray-500 font-mono">${p.tipo_producto}</p>
                    </td>
                    <td class="px-4 py-2.5 text-center font-mono text-sm">${p.cantidad}</td>
                    <td class="px-4 py-2.5 text-right font-mono text-sm">${formatearMoneda(p.precio_unitario)}</td>
                    <td class="px-4 py-2.5 text-right font-mono font-bold text-sm">${formatearMoneda(p.subtotal)}</td>
                `;
                tbodyProductos.appendChild(tr);
            });
        }

        // Renderizar pagos
        const tbodyPagos = document.getElementById('modal-pagos');
        if (!data.pagos || data.pagos.length === 0) {
            tbodyPagos.innerHTML =
                '<tr><td colspan="3" class="text-center py-4 text-gray-500 text-sm">Sin pagos registrados.</td></tr>';
        } else {
            tbodyPagos.innerHTML = '';
            data.pagos.forEach(p => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50 transition-colors';
                tr.innerHTML = `
                    <td class="px-4 py-2.5 text-sm">${formatearFechaHora(p.fecha_pago)}</td>
                    <td class="px-4 py-2.5 text-sm text-gray-500">${p.operador}</td>
                    <td class="px-4 py-2.5 text-right font-mono font-bold text-sm text-green-700">${formatearMoneda(p.monto_abonado)}</td>
                `;
                tbodyPagos.appendChild(tr);
            });
        }

    } catch (err) {
        console.error('[Detalle] Error:', err);
        document.getElementById('modal-productos').innerHTML =
            '<tr><td colspan="4" class="text-center py-4 text-red-500 text-sm">Error al cargar el detalle.</td></tr>';
    }
}

/**
 * Cierra el modal de detalle de venta.
 */
function cerrarDetalleVenta() {
    const modal = document.getElementById('modal-detalle');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}