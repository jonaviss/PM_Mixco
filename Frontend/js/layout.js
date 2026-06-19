/**
 * @file layout.js
 * @description Inyección dinámica del sidebar unificado en todas las páginas del módulo librería.
 */

async function cargarLayout() {
    console.log('[Layout] v2 con filtro admin cargado');
    if (document.getElementById('sidebar-dinamico')) return;

    const rango = localStorage.getItem('rango');
    const esAdmin = rango === 'administrador' || rango === 'super_admin';
    const esCliente = rango === 'cliente';

    const sidebarHTML = `
        <aside id="sidebar-dinamico" class="fixed left-0 top-0 h-full w-sidebar bg-surface-container-lowest border-r border-outline-variant flex flex-col z-40">
            <div class="px-5 py-5 border-b border-outline-variant">
                <h1 class="text-lg font-bold text-primary leading-none">Palabra Miel Mixco</h1>
                <p class="text-xs text-secondary mt-1 font-mono uppercase tracking-wider">${esCliente ? 'Portal del Cliente' : 'Módulo Librería'}</p>
            </div>
            <nav class="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto" id="nav-links">
            </nav>
            <div class="px-2 py-3 border-t border-outline-variant space-y-0.5">
                <a href="mi_perfil.html" class="nav-item"><span class="material-symbols-outlined text-[20px]">person</span>Mi Perfil</a>
                <a href="index.html" id="btnCerrarSesion" class="nav-item danger"><span class="material-symbols-outlined text-[20px]">logout</span>Cerrar Sesión</a>
            </div>
        </aside>
    `;

    document.body.insertAdjacentHTML('afterbegin', sidebarHTML);

    const nav = document.getElementById('nav-links');

    if (esCliente) {
        const paginasCliente = [
            { href: "cliente_mis_compras.html", icono: "receipt_long", texto: "Mis Compras" }
        ];
        const paginaActual = window.location.pathname.split('/').pop();
        paginasCliente.forEach(p => {
            const a = document.createElement('a');
            a.href = p.href;
            a.className = `nav-item ${paginaActual === p.href ? 'active' : ''}`;
            a.innerHTML = `<span class="material-symbols-outlined text-[20px]">${p.icono}</span>${p.texto}`;
            nav.appendChild(a);
        });
    } else {
        const paginas = [
            { href: "libreria_dashboard.html", icono: "dashboard", texto: "Dashboard" },
            { href: "libreria_inventario.html", icono: "inventory_2", texto: "Inventario" },
            { href: "libreria_ventas.html", icono: "point_of_sale", texto: "Ventas" },
            { href: "libreria_cobros.html", icono: "payments", texto: "Cobros" },
            { href: "libreria_clientes.html", icono: "group", texto: "Clientes" },
            { href: "cliente_mis_compras.html", icono: "receipt_long", texto: "Mis Compras" },
            { href: "proveedores.html", icono: "local_shipping", texto: "Proveedores" },
            { href: "compras.html", icono: "receipt", texto: "Registrar Compra" },
            { href: "pagos_proveedores.html", icono: "payments", texto: "Pagos a Proveedores" },
            { href: "reporte_lotes.html", icono: "inventory", texto: "Lotes Pendientes" },
            { href: "libreria_reportes_ventas.html", icono: "assessment", texto: "Reportes de Ventas" },
            { href: "admin_usuarios.html", icono: "admin_panel_settings", texto: "Usuarios", admin: true }
        ];
        const paginaActual = window.location.pathname.split('/').pop();
        paginas.forEach(p => {
            if (p.admin && !esAdmin) return;
            const a = document.createElement('a');
            a.href = p.href;
            a.className = `nav-item ${paginaActual === p.href ? 'active' : ''}`;
            a.innerHTML = `<span class="material-symbols-outlined text-[20px]">${p.icono}</span>${p.texto}`;
            nav.appendChild(a);
        });
    }

    document.getElementById('btnCerrarSesion')?.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.clear();
        window.location.href = 'index.html';
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', cargarLayout);
} else {
    cargarLayout();
}