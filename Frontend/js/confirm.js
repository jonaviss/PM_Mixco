(function() {
    var modalEl = null;

    function crearModal() {
        if (document.getElementById('confirm-global')) return;
        var div = document.createElement('div');
        div.id = 'confirm-global';
        div.className = 'fixed inset-0 bg-black/50 hidden items-center justify-center z-50 p-4 backdrop-blur-sm';
        div.innerHTML =
            '<div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">' +
            '  <div id="confirm-global-header" class="px-5 py-4 flex justify-between items-center bg-error">' +
            '    <h3 id="confirm-global-titulo" class="text-base font-bold text-white">Confirmar</h3>' +
            '    <button id="confirm-global-cerrar-x" class="text-white/70 hover:text-white"><span class="material-symbols-outlined">close</span></button>' +
            '  </div>' +
            '  <div class="p-5">' +
            '    <p id="confirm-global-mensaje" class="text-sm text-on-surface mb-5"></p>' +
            '    <div class="flex justify-end gap-3">' +
            '      <button id="confirm-global-cancelar" class="px-4 py-2 text-sm font-bold text-secondary border border-outline-variant rounded-lg hover:bg-surface-container transition">Cancelar</button>' +
            '      <button id="confirm-global-aceptar" class="px-4 py-2 text-sm font-bold text-white rounded-lg hover:opacity-90 transition">Aceptar</button>' +
            '    </div>' +
            '  </div>' +
            '</div>';
        document.body.appendChild(div);
        modalEl = div;
        document.getElementById('confirm-global-cerrar-x').onclick = cerrar;
        document.getElementById('confirm-global-cancelar').onclick = cerrar;
        modalEl.addEventListener('click', function(e) { if (e.target === modalEl) cerrar(); });
    }

    var callbackFn = null;

    function cerrar() {
        if (modalEl) { modalEl.classList.add('hidden'); modalEl.classList.remove('flex'); }
        callbackFn = null;
    }

    function aceptar() {
        var cb = callbackFn;
        cerrar();
        if (cb) cb();
    }

    window.confirmar = function(mensaje, callback, opciones) {
        crearModal();
        if (typeof opciones === 'string') opciones = { btnAceptar: opciones };
        opciones = opciones || {};
        document.getElementById('confirm-global-mensaje').textContent = mensaje;
        document.getElementById('confirm-global-titulo').textContent = opciones.titulo || 'Confirmar';
        document.getElementById('confirm-global-aceptar').textContent = opciones.btnAceptar || 'Aceptar';
        document.getElementById('confirm-global-aceptar').className = 'px-4 py-2 text-sm font-bold text-white rounded-lg hover:opacity-90 transition ' + (opciones.colorAceptar || 'bg-error');
        document.getElementById('confirm-global-header').className = 'px-5 py-4 flex justify-between items-center ' + (opciones.colorHeader || 'bg-error') + ' text-white';
        document.getElementById('confirm-global-aceptar').onclick = aceptar;
        callbackFn = callback;
        modalEl.classList.remove('hidden');
        modalEl.classList.add('flex');
    };
})();