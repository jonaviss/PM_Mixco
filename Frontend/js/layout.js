/**
 * @file layout.js
 * @description Inyección dinámica del sidebar unificado en todas las páginas del módulo librería.
 */

async function cargarLayout() {
    if (document.getElementById('sidebar-dinamico')) return;

    const sidebarHTML = `
        <aside id="sidebar-dinamico" class="fixed left-0 top-0 h-full w-sidebar bg-surface-container-lowest border-r border-outline-variant flex flex-col z-40">
            <div class="px-5 py-5 border-b border-outline-variant">
                <h1 class="text-lg font-bold text-primary leading-none"><span class="sidebar-text">Palabra Miel Mixco</span></h1>
                <p class="text-xs text-secondary mt-1 font-mono uppercase tracking-wider"><span class="sidebar-text">Módulo Librería</span></p>
            </div>
            <nav class="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto" id="nav-links">
                <!-- Los enlaces se generan dinámicamente -->
            </nav>
            <div class="px-2 py-3 border-t border-outline-variant space-y-0.5">
                <button id="btnColapsarSidebar" class="nav-item w-full text-left justify-center md:justify-start" title="Colapsar sidebar">
                    <span class="material-symbols-outlined text-[20px]">chevron_left</span>
                </button>
                <a href="mi_perfil.html" class="nav-item"><span class="material-symbols-outlined text-[20px]">person</span><span class="sidebar-text">Mi Perfil</span></a>
                <a href="index.html" id="btnCerrarSesion" class="nav-item danger"><span class="material-symbols-outlined text-[20px]">logout</span><span class="sidebar-text">Cerrar Sesión</span></a>
            </div>
        </aside>
    `;

    document.body.insertAdjacentHTML('afterbegin', sidebarHTML);

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
        { href: "cancelar_venta.html", icono: "block", texto: "Cancelar Venta" },
        { href: "admin_configuracion.html", icono: "settings", texto: "Configuración", admin: true }
      
    ];
    const paginaActual = window.location.pathname.split('/').pop();
    const rango = localStorage.getItem('rango');
    const esAdmin = rango === 'administrador' || rango === 'super_admin';
    const nav = document.getElementById('nav-links');
    paginas.forEach(p => {
        if (p.admin && !esAdmin) return;
        const a = document.createElement('a');
        a.href = p.href;
        a.className = `nav-item ${paginaActual === p.href ? 'active' : ''}`;
        a.innerHTML = `<span class="material-symbols-outlined text-[20px]">${p.icono}</span><span class="sidebar-text">${p.texto}</span>`;
        nav.appendChild(a);
    });

    document.getElementById('btnCerrarSesion')?.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.clear();
        window.location.href = 'index.html';
    });

    const avatarContainer = document.getElementById('nombre-usuario')?.closest('.flex.items-center.gap-2');
    if (avatarContainer) {
        const dropdownHTML = `
            <div id="user-dropdown" class="absolute right-0 top-full mt-2 w-48 bg-white border border-outline-variant rounded-xl shadow-xl z-50 hidden overflow-hidden">
                <a href="mi_perfil.html" class="flex items-center gap-2 px-4 py-3 text-sm font-bold text-on-surface hover:bg-surface-container-low transition border-b border-outline-variant">
                    <span class="material-symbols-outlined text-[18px]">person</span> Mi Perfil
                </a>
                <a href="index.html" id="btnLogoutDropdown" class="flex items-center gap-2 px-4 py-3 text-sm font-bold text-error hover:bg-red-50 transition">
                    <span class="material-symbols-outlined text-[18px]">logout</span> Cerrar Sesión
                </a>
            </div>
        `;
        avatarContainer.style.position = 'relative';
        avatarContainer.insertAdjacentHTML('beforeend', dropdownHTML);
        avatarContainer.style.cursor = 'pointer';
        avatarContainer.addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('user-dropdown')?.classList.toggle('hidden');
        });
        document.addEventListener('click', () => {
            document.getElementById('user-dropdown')?.classList.add('hidden');
        });
        document.getElementById('btnLogoutDropdown')?.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = 'index.html';
        });
    }

    const sidebar = document.getElementById('sidebar-dinamico');
    const btnColapsar = document.getElementById('btnColapsarSidebar');
    if (sidebar && btnColapsar) {
        if (localStorage.getItem('sidebar_colapsado') === 'true') {
            sidebar.classList.add('collapsed');
            document.body.classList.add('sidebar-collapsed');
            btnColapsar.querySelector('.material-symbols-outlined').textContent = 'chevron_right';
        }
        btnColapsar.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            document.body.classList.toggle('sidebar-collapsed');
            const colapsado = sidebar.classList.contains('collapsed');
            btnColapsar.querySelector('.material-symbols-outlined').textContent = colapsado ? 'chevron_right' : 'chevron_left';
            localStorage.setItem('sidebar_colapsado', colapsado);
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', cargarLayout);
} else {
    cargarLayout();
}