/**
 * @file table.js
 * @description Tabla reutilizable con paginación y ordenamiento por columna.
 * Uso: Table.init('tbody-id', { columns, data, pageSize, onRow, paginationEl, infoEl })
 */

const Table = (() => {
  const _instances = {};

  function renderPagination(inst) {
    const { page, pageSize, data, paginationEl, infoEl, filtered } = inst;
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
    const start = (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, filtered.length);

    if (paginationEl) {
      paginationEl.innerHTML = `
        <span class="text-xs font-mono text-secondary">${start}-${end} de ${filtered.length}</span>
        <div class="flex gap-2 items-center">
          <button data-page="prev" class="p-1.5 hover:bg-surface-container rounded transition-colors text-secondary" ${page <= 1 ? 'disabled' : ''}>
            <span class="material-symbols-outlined text-[18px]">chevron_left</span>
          </button>
          <span class="text-xs font-mono text-secondary px-2">Pág. ${page} de ${totalPages}</span>
          <button data-page="next" class="p-1.5 hover:bg-surface-container rounded transition-colors text-secondary" ${page >= totalPages ? 'disabled' : ''}>
            <span class="material-symbols-outlined text-[18px]">chevron_right</span>
          </button>
        </div>
      `;
      paginationEl.querySelector('[data-page="prev"]')?.addEventListener('click', () => {
        if (inst.page > 1) { inst.page--; renderTable(inst); }
      });
      paginationEl.querySelector('[data-page="next"]')?.addEventListener('click', () => {
        if (inst.page < totalPages) { inst.page++; renderTable(inst); }
      });
    }
    if (infoEl) {
      infoEl.textContent = `${filtered.length} registro(s)`;
    }
  }

  function renderTable(inst) {
    const { tbody, columns, pageSize, onRow, sortBy, data, filtered } = inst;
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
    if (inst.page > totalPages) inst.page = 1;
    const start = (inst.page - 1) * pageSize;
    const pageData = filtered.slice(start, start + pageSize);

    tbody.innerHTML = '';
    if (pageData.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${columns.length}" class="text-center py-8 text-secondary text-sm">No se encontraron registros.</td></tr>`;
      renderPagination(inst);
      return;
    }

    pageData.forEach((item, idx) => {
      const tr = document.createElement('tr');
      tr.className = 'table-row transition-colors';
      tr.innerHTML = onRow(item, start + idx);
      tbody.appendChild(tr);
    });

    renderPagination(inst);
    if (inst.onRender) inst.onRender();
  }

  function buildHeader(inst) {
    const { thead, columns, sortBy } = inst;
    thead.innerHTML = '';
    const tr = document.createElement('tr');
    columns.forEach(col => {
      const th = document.createElement('th');
      th.className = `px-4 py-3 text-xs font-mono font-bold text-secondary uppercase tracking-wider ${col.class || ''}`;
      if (col.sortable) {
        const active = sortBy.key === col.key;
        const dir = active ? sortBy.dir : 'none';
        const arrow = active ? (dir === 'asc' ? 'arrow_upward' : 'arrow_downward') : 'unfold_more';
        th.innerHTML = `${col.label} <span class="material-symbols-outlined text-[14px] align-middle ${active ? 'text-primary' : 'text-outline-variant'}">${arrow}</span>`;
        th.style.cursor = 'pointer';
        th.style.userSelect = 'none';
        th.addEventListener('click', () => {
          if (sortBy.key === col.key) {
            inst.sortBy.dir = sortBy.dir === 'asc' ? 'desc' : 'asc';
          } else {
            inst.sortBy.key = col.key;
            inst.sortBy.dir = 'asc';
          }
          inst.filtered = sortData(inst.data, inst.sortBy, inst.searchQuery, inst.filterFn);
          inst.page = 1;
          buildHeader(inst);
          renderTable(inst);
        });
      } else {
        th.textContent = col.label;
      }
      tr.appendChild(th);
    });
    thead.appendChild(tr);
  }

  function sortData(data, sortBy, searchQuery, filterFn) {
    let filtered = data;
    if (searchQuery && filterFn) {
      filtered = data.filter(item => filterFn(item, searchQuery));
    }
    if (sortBy.key) {
      filtered = [...filtered].sort((a, b) => {
        const va = a[sortBy.key];
        const vb = b[sortBy.key];
        if (va == null) return 1;
        if (vb == null) return -1;
        const cmp = typeof va === 'number' && typeof vb === 'number' ? va - vb : String(va).localeCompare(String(vb), 'es', { numeric: true });
        return sortBy.dir === 'desc' ? -cmp : cmp;
      });
    }
    return filtered;
  }

  return {
    init(tbodyId, opts = {}) {
      if (_instances[tbodyId]) {
        if (opts.data) _instances[tbodyId].data = opts.data;
        if (opts.pageSize) _instances[tbodyId].pageSize = opts.pageSize;
        if (opts.onRow) _instances[tbodyId].onRow = opts.onRow;
        if (opts.columns) {
          _instances[tbodyId].columns = opts.columns;
          buildHeader(_instances[tbodyId]);
        }
        if (opts.paginationEl) _instances[tbodyId].paginationEl = typeof opts.paginationEl === 'string' ? document.querySelector(opts.paginationEl) : opts.paginationEl;
        _instances[tbodyId].filtered = sortData(_instances[tbodyId].data, _instances[tbodyId].sortBy, '', _instances[tbodyId].filterFn);
        _instances[tbodyId].page = 1;
        renderTable(_instances[tbodyId]);
        return;
      }

      const tbody = document.getElementById(tbodyId);
      if (!tbody) return;
      const table = tbody.closest('table');
      if (!table) return;

      const columns = opts.columns || [];
      const pageSize = opts.pageSize || 10;
      const sortBy = opts.sortBy || { key: '', dir: 'asc' };

      let thead = table.querySelector('thead');
      if (!thead) {
        thead = document.createElement('thead');
        thead.className = 'bg-surface-container-low/50';
        table.insertBefore(thead, tbody);
      }

      const inst = {
        tbody,
        thead,
        columns,
        pageSize,
        sortBy: { ...sortBy },
        data: opts.data || [],
        filtered: [],
        page: 1,
        onRow: opts.onRow || (() => ''),
        paginationEl: typeof opts.paginationEl === 'string' ? document.querySelector(opts.paginationEl) : opts.paginationEl || null,
        infoEl: typeof opts.infoEl === 'string' ? document.querySelector(opts.infoEl) : opts.infoEl || null,
        filterFn: opts.filter || null,
        searchQuery: '',
        onRender: opts.onRender || null,
      };

      _instances[tbodyId] = inst;
      buildHeader(inst);
      inst.filtered = sortData(inst.data, inst.sortBy, '', inst.filterFn);
      renderTable(inst);
    },

    setData(tbodyId, data) {
      const inst = _instances[tbodyId];
      if (!inst) return;
      inst.data = data || [];
      inst.filtered = sortData(inst.data, inst.sortBy, inst.searchQuery, inst.filterFn);
      inst.page = 1;
      renderTable(inst);
    },

    setSearch(tbodyId, query) {
      const inst = _instances[tbodyId];
      if (!inst) return;
      inst.searchQuery = (query || '').toLowerCase().trim();
      inst.filtered = sortData(inst.data, inst.sortBy, inst.searchQuery, inst.filterFn);
      inst.page = 1;
      renderTable(inst);
    },

    getFiltered(tbodyId) {
      const inst = _instances[tbodyId];
      return inst ? inst.filtered : [];
    },

    render(tbodyId) {
      const inst = _instances[tbodyId];
      if (inst) renderTable(inst);
    },

    destroy(tbodyId) {
      delete _instances[tbodyId];
    }
  };
})();
