/* ── API Client ─────────────────────────────────────────────── */
const API = {
  base: '',
  async get(path) {
    const r = await fetch(this.base + path);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },
  async del(path) {
    const r = await fetch(this.base + path, { method: 'DELETE' });
    return r.json();
  },
};

/* ── Toast ──────────────────────────────────────────────────── */
function toast(msg, type = 'info') {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => {
    el.style.animation = 'toastOut .25s ease forwards';
    setTimeout(() => el.remove(), 250);
  }, 3000);
}

/* ── Modal helpers ──────────────────────────────────────────── */
function openModal(id) {
  document.getElementById(id).classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}
function closeAllModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAllModals(); });
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => { if (e.target === overlay) closeAllModals(); });
});

/* ── Navigation ─────────────────────────────────────────────── */
function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.querySelector(`.nav-item[data-page="${page}"]`).classList.add('active');
  document.getElementById('topbar-title').textContent = {
    dashboard: 'Dashboard',
    vehicles:  'Vehículos',
    customers: 'Clientes',
    rentals:   'Reservas',
  }[page];
  if (page === 'dashboard') loadDashboard();
  if (page === 'vehicles')  loadVehicles();
  if (page === 'customers') loadCustomers();
  if (page === 'rentals')   loadRentals();
}
document.querySelectorAll('.nav-item[data-page]').forEach(item => {
  item.addEventListener('click', () => navigate(item.dataset.page));
});

/* ── Helpers ────────────────────────────────────────────────── */
const fmt = n => '$' + Number(n).toLocaleString('es-GT', { minimumFractionDigits: 2 });
function typePill(type) {
  const map = { 'Automóvil': 'car', 'Camioneta': 'truck', 'SUV': 'suv' };
  const cls = map[type] || 'car';
  return `<span class="type-pill type-${cls}">${type}</span>`;
}
function statusBadge(status) {
  const map = { 'Activa': 'badge-yellow', 'Completada': 'badge-green', 'Cancelada': 'badge-red' };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}
function availBadge(available) {
  return available
    ? `<span class="badge badge-green">Disponible</span>`
    : `<span class="badge badge-red">Ocupado</span>`;
}

/* ── Sort state ─────────────────────────────────────────────── */
const sortState = { vehicles: { col: null, dir: 1 }, customers: { col: null, dir: 1 }, rentals: { col: null, dir: 1 } };

function sortData(arr, col, dir) {
  return [...arr].sort((a, b) => {
    let va = col.split('.').reduce((o, k) => o?.[k], a);
    let vb = col.split('.').reduce((o, k) => o?.[k], b);
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    return va < vb ? -dir : va > vb ? dir : 0;
  });
}

/* ── Pagination ─────────────────────────────────────────────── */
const PAGE_SIZE = 10;
const pageState = { vehicles: 1, customers: 1, rentals: 1 };

function renderPagination(containerId, total, current, section) {
  const pages = Math.ceil(total / PAGE_SIZE);
  const c = document.getElementById(containerId);
  if (!c) return;
  const start = (current - 1) * PAGE_SIZE + 1;
  const end   = Math.min(current * PAGE_SIZE, total);
  c.innerHTML = `
    <span>${total ? `${start}–${end} de ${total}` : '0 registros'}</span>
    <div class="page-btns">
      <button class="page-btn" onclick="changePage('${section}', ${current - 1})" ${current <= 1 ? 'disabled' : ''}>‹</button>
      ${Array.from({ length: Math.min(pages, 5) }, (_, i) => {
        const p = i + 1;
        return `<button class="page-btn ${p === current ? 'active' : ''}" onclick="changePage('${section}', ${p})">${p}</button>`;
      }).join('')}
      <button class="page-btn" onclick="changePage('${section}', ${current + 1})" ${current >= pages ? 'disabled' : ''}>›</button>
    </div>`;
}

function changePage(section, page) {
  pageState[section] = page;
  if (section === 'vehicles')  renderVehiclesTable(window._vehicles);
  if (section === 'customers') renderCustomersTable(window._customers);
  if (section === 'rentals')   renderRentalsTable(window._rentals);
}

/* ══════════════════════════════════════════════════
   DASHBOARD
══════════════════════════════════════════════════ */
async function loadDashboard() {
  const res = await API.get('/api/dashboard');
  if (!res.ok) return;
  const d = res.data;

  // Stat cards
  document.getElementById('stat-vehicles').textContent    = d.vehicles.total;
  document.getElementById('stat-available').textContent   = d.vehicles.available;
  document.getElementById('stat-customers').textContent   = d.customers.total;
  document.getElementById('stat-revenue').textContent     = fmt(d.revenue);
  document.getElementById('stat-active').textContent      = d.rentals.active;
  document.getElementById('stat-completed').textContent   = d.rentals.completed;
  document.getElementById('stat-strategy').textContent    = d.active_strategy;
  document.getElementById('sidebar-strategy').textContent = d.active_strategy;

  // Donut: estado de vehículos
  const avail     = d.vehicles.available;
  const total_v   = d.vehicles.total;
  const occupied  = total_v - avail;
  renderDonut('donut-vehicles', [
    { value: avail,    color: '#2ecc71', label: 'Disponibles' },
    { value: occupied, color: '#e74c3c', label: 'Ocupados' },
  ], avail, 'Libres');

  // Donut: estado de reservas
  renderDonut('donut-rentals', [
    { value: d.rentals.active,    color: '#f39c12', label: 'Activas' },
    { value: d.rentals.completed, color: '#2ecc71', label: 'Completadas' },
    { value: d.rentals.cancelled, color: '#e74c3c', label: 'Canceladas' },
  ], d.rentals.total, 'Total');

  // Bar chart: tipos de vehículo
  renderBarChart('bar-types', d.vehicles.by_type);

  // Recent rentals
  renderRecentRentals(d.recent_rentals);
}

function renderDonut(id, segments, centerVal, centerLbl) {
  const wrap = document.getElementById(id);
  if (!wrap) return;
  const total  = segments.reduce((s, seg) => s + seg.value, 0) || 1;
  const r      = 38;
  const circ   = 2 * Math.PI * r;
  let offset   = 0;
  const paths  = segments.map(seg => {
    const pct  = seg.value / total;
    const dash = pct * circ;
    const path = `<circle cx="50" cy="50" r="${r}" fill="none" stroke="${seg.color}"
      stroke-width="10" stroke-dasharray="${dash} ${circ - dash}"
      stroke-dashoffset="${-offset}" opacity=".9"/>`;
    offset += dash;
    return path;
  }).join('');
  const legend = segments.map(seg => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${seg.color}"></span>
      <span>${seg.label}: <strong style="color:var(--text)">${seg.value}</strong></span>
    </div>`).join('');
  wrap.innerHTML = `
    <div class="chart-container">
      <div class="donut-wrap">
        <svg viewBox="0 0 100 100">${paths}<circle cx="50" cy="50" r="28" fill="var(--surface)"/></svg>
        <div class="donut-center">
          <span class="dc-val">${centerVal}</span>
          <span class="dc-lbl">${centerLbl}</span>
        </div>
      </div>
      <div class="legend">${legend}</div>
    </div>`;
}

function renderBarChart(id, byType) {
  const wrap = document.getElementById(id);
  if (!wrap) return;
  const colors = { 'Automóvil': '#6ba3ff', 'Camioneta': '#f39c12', 'SUV': '#2ecc71' };
  const max    = Math.max(...Object.values(byType), 1);
  const rows   = Object.entries(byType).map(([type, count]) => `
    <div class="bar-row">
      <span class="bar-label">${type}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width:${(count/max)*100}%;background:${colors[type]||'#4f8ef7'}"></div>
      </div>
      <span class="bar-count">${count}</span>
    </div>`).join('');
  wrap.innerHTML = `<div class="bar-chart">${rows}</div>`;
}

function renderRecentRentals(rentals) {
  const wrap = document.getElementById('recent-rentals');
  if (!wrap) return;
  if (!rentals.length) { wrap.innerHTML = '<div class="empty-state"><div class="es-icon">📋</div><div class="es-text">Sin reservas recientes</div></div>'; return; }
  const icons = { 'Activa': '🟡', 'Completada': '🟢', 'Cancelada': '🔴' };
  wrap.innerHTML = rentals.map(r => `
    <div class="recent-item">
      <div class="ri-icon">${icons[r.status] || '⚪'}</div>
      <div class="ri-info">
        <div class="ri-title">${r.vehicle.model} → ${r.customer.name}</div>
        <div class="ri-sub">${r.days} días · ${r.start_date} · ${r.status}</div>
      </div>
      <div class="ri-amount">${fmt(r.cost)}</div>
    </div>`).join('');
}

/* ══════════════════════════════════════════════════
   VEHICLES
══════════════════════════════════════════════════ */
window._vehicles = [];

async function loadVehicles() {
  const res = await API.get('/api/vehicles');
  if (!res.ok) { toast('Error cargando vehículos', 'error'); return; }
  window._vehicles = res.data;
  renderVehiclesTable(window._vehicles);
  populateVehicleSelect();
}

function filterVehicles() {
  const q      = document.getElementById('v-search').value.toLowerCase();
  const type   = document.getElementById('v-type-filter').value;
  const status = document.getElementById('v-status-filter').value;
  let data = window._vehicles;
  if (q)      data = data.filter(v => v.plate.toLowerCase().includes(q) || v.model.toLowerCase().includes(q));
  if (type)   data = data.filter(v => v.type === type);
  if (status === 'available')   data = data.filter(v => v.available);
  if (status === 'unavailable') data = data.filter(v => !v.available);
  pageState.vehicles = 1;
  renderVehiclesTable(data);
}

function renderVehiclesTable(data) {
  const ss = sortState.vehicles;
  if (ss.col) data = sortData(data, ss.col, ss.dir);
  const start = (pageState.vehicles - 1) * PAGE_SIZE;
  const page  = data.slice(start, start + PAGE_SIZE);
  const tbody = document.querySelector('#vehicles-table tbody');
  if (!page.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="no-results">No se encontraron vehículos</td></tr>`;
  } else {
    tbody.innerHTML = page.map(v => `
      <tr>
        <td class="mono">${v.plate}</td>
        <td><strong style="color:var(--text)">${v.model}</strong></td>
        <td>${v.year}</td>
        <td>${typePill(v.type)}</td>
        <td>${fmt(v.daily_rate)}</td>
        <td>${availBadge(v.available)}</td>
        <td>
          <button class="btn btn-ghost btn-sm" onclick="deleteVehicle('${v.plate}')" title="Eliminar">🗑</button>
        </td>
      </tr>`).join('');
  }
  renderPagination('vehicles-pagination', data.length, pageState.vehicles, 'vehicles');
}

async function deleteVehicle(plate) {
  if (!confirm(`¿Eliminar el vehículo ${plate}?`)) return;
  const res = await API.del(`/api/vehicles/${plate}`);
  if (res.ok) { toast('Vehículo eliminado', 'success'); loadVehicles(); loadDashboard(); }
  else toast(res.error, 'error');
}

async function submitNewVehicle(e) {
  e.preventDefault();
  const body = {
    type:       document.getElementById('nv-type').value,
    plate:      document.getElementById('nv-plate').value,
    model:      document.getElementById('nv-model').value,
    year:       document.getElementById('nv-year').value,
    daily_rate: document.getElementById('nv-rate').value,
  };
  const res = await API.post('/api/vehicles', body);
  if (res.ok) {
    toast('Vehículo registrado', 'success');
    closeModal('modal-vehicle');
    e.target.reset();
    loadVehicles(); loadDashboard();
  } else toast(res.error, 'error');
}

/* ══════════════════════════════════════════════════
   CUSTOMERS
══════════════════════════════════════════════════ */
window._customers = [];

async function loadCustomers() {
  const res = await API.get('/api/customers');
  if (!res.ok) { toast('Error cargando clientes', 'error'); return; }
  window._customers = res.data;
  renderCustomersTable(window._customers);
  populateCustomerSelect();
}

function filterCustomers() {
  const q = document.getElementById('c-search').value.toLowerCase();
  let data = window._customers;
  if (q) data = data.filter(c => c.name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q) || c.id.toLowerCase().includes(q));
  pageState.customers = 1;
  renderCustomersTable(data);
}

function renderCustomersTable(data) {
  const ss = sortState.customers;
  if (ss.col) data = sortData(data, ss.col, ss.dir);
  const start = (pageState.customers - 1) * PAGE_SIZE;
  const page  = data.slice(start, start + PAGE_SIZE);
  const tbody = document.querySelector('#customers-table tbody');
  if (!page.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="no-results">No se encontraron clientes</td></tr>`;
  } else {
    tbody.innerHTML = page.map(c => `
      <tr>
        <td class="mono" style="color:var(--accent3)">${c.id}</td>
        <td><strong style="color:var(--text)">${c.name}</strong></td>
        <td>${c.email}</td>
        <td class="mono">${c.license}</td>
      </tr>`).join('');
  }
  renderPagination('customers-pagination', data.length, pageState.customers, 'customers');
}

async function submitNewCustomer(e) {
  e.preventDefault();
  const body = {
    name:    document.getElementById('nc-name').value,
    email:   document.getElementById('nc-email').value,
    license: document.getElementById('nc-license').value,
  };
  const res = await API.post('/api/customers', body);
  if (res.ok) {
    toast('Cliente registrado', 'success');
    closeModal('modal-customer');
    e.target.reset();
    loadCustomers(); loadDashboard();
  } else toast(res.error, 'error');
}

/* ══════════════════════════════════════════════════
   RENTALS
══════════════════════════════════════════════════ */
window._rentals = [];

async function loadRentals() {
  const res = await API.get('/api/rentals');
  if (!res.ok) { toast('Error cargando reservas', 'error'); return; }
  window._rentals = res.data;
  renderRentalsTable(window._rentals);
}

function filterRentals() {
  const q      = document.getElementById('r-search').value.toLowerCase();
  const status = document.getElementById('r-status-filter').value;
  let data = window._rentals;
  if (q)      data = data.filter(r => r.id.toLowerCase().includes(q) || r.vehicle.model.toLowerCase().includes(q) || r.customer.name.toLowerCase().includes(q));
  if (status) data = data.filter(r => r.status === status);
  pageState.rentals = 1;
  renderRentalsTable(data);
}

function renderRentalsTable(data) {
  const ss = sortState.rentals;
  if (ss.col) data = sortData(data, ss.col, ss.dir);
  const start = (pageState.rentals - 1) * PAGE_SIZE;
  const page  = data.slice(start, start + PAGE_SIZE);
  const tbody = document.querySelector('#rentals-table tbody');
  if (!page.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="no-results">No se encontraron reservas</td></tr>`;
  } else {
    tbody.innerHTML = page.map(r => `
      <tr>
        <td class="mono" style="color:var(--accent3)">${r.id}</td>
        <td>${r.vehicle.model}<br><small style="color:var(--text3)">${r.vehicle.plate}</small></td>
        <td>${r.customer.name}</td>
        <td>${r.days}d / ${r.km_estimate}km</td>
        <td><strong style="color:var(--text)">${fmt(r.cost)}</strong></td>
        <td>${statusBadge(r.status)}</td>
        <td style="color:var(--text3);font-size:.78rem">${r.start_date}</td>
        <td>
          ${r.status === 'Activa' ? `
            <button class="btn btn-success btn-sm" onclick="completeRental('${r.id}')" title="Completar">✓</button>
            <button class="btn btn-danger btn-sm"  onclick="cancelRental('${r.id}')"   title="Cancelar">✕</button>
          ` : '—'}
        </td>
      </tr>`).join('');
  }
  renderPagination('rentals-pagination', data.length, pageState.rentals, 'rentals');
}

async function completeRental(id) {
  if (!confirm(`¿Marcar la reserva ${id} como completada?`)) return;
  const res = await API.post(`/api/rentals/${id}/complete`, {});
  if (res.ok) { toast('Reserva completada', 'success'); loadRentals(); loadDashboard(); }
  else toast(res.error, 'error');
}

async function cancelRental(id) {
  if (!confirm(`¿Cancelar la reserva ${id}?`)) return;
  const res = await API.post(`/api/rentals/${id}/cancel`, {});
  if (res.ok) { toast('Reserva cancelada', 'success'); loadRentals(); loadDashboard(); }
  else toast(res.error, 'error');
}

async function updateQuote() {
  const plate = document.getElementById('nr-plate').value;
  const days  = document.getElementById('nr-days').value;
  const km    = document.getElementById('nr-km').value;
  const prev  = document.getElementById('quote-preview');
  if (!plate || !days || !km) { prev.classList.remove('show'); return; }
  const res = await API.get(`/api/rentals/quote?plate=${plate}&days=${days}&km=${km}`);
  if (res.ok) {
    document.getElementById('qp-value').textContent    = fmt(res.data.cost);
    document.getElementById('qp-strategy').textContent = res.data.strategy;
    prev.classList.add('show');
  }
}

async function submitNewRental(e) {
  e.preventDefault();
  const body = {
    plate:       document.getElementById('nr-plate').value,
    customer_id: document.getElementById('nr-customer').value,
    days:        document.getElementById('nr-days').value,
    km_estimate: document.getElementById('nr-km').value,
  };
  const res = await API.post('/api/rentals', body);
  if (res.ok) {
    toast('Reserva creada exitosamente', 'success');
    closeModal('modal-rental');
    e.target.reset();
    document.getElementById('quote-preview').classList.remove('show');
    loadRentals(); loadDashboard();
  } else toast(res.error, 'error');
}

/* ══════════════════════════════════════════════════
   PRICING STRATEGY
══════════════════════════════════════════════════ */
async function openStrategyModal() {
  const res = await API.get('/api/pricing/strategies');
  if (!res.ok) return;
  const list = document.getElementById('strategy-list');
  const current = document.getElementById('sidebar-strategy').textContent;
  list.innerHTML = res.data.map(s => `
    <label style="display:flex;align-items:center;gap:12px;padding:12px;background:var(--bg3);border-radius:var(--radius-sm);cursor:pointer;border:1px solid var(--border);margin-bottom:8px;transition:border-color .18s">
      <input type="radio" name="strategy" value="${s.key}" ${s.description === current ? 'checked' : ''} style="accent-color:var(--accent)">
      <span style="font-size:.875rem;color:var(--text)">${s.description}</span>
    </label>`).join('');
  openModal('modal-strategy');
}

async function submitStrategy(e) {
  e.preventDefault();
  const key = document.querySelector('input[name="strategy"]:checked')?.value;
  if (!key) return;
  const res = await API.post('/api/pricing/strategy', { key });
  if (res.ok) {
    toast('Estrategia actualizada', 'success');
    document.getElementById('sidebar-strategy').textContent  = res.data.active;
    document.getElementById('stat-strategy').textContent     = res.data.active;
    closeModal('modal-strategy');
  } else toast(res.error, 'error');
}

/* ── Select populators ──────────────────────────────────────── */
function populateVehicleSelect() {
  const sel = document.getElementById('nr-plate');
  if (!sel) return;
  const available = window._vehicles.filter(v => v.available);
  sel.innerHTML = '<option value="">Seleccionar vehículo...</option>' +
    available.map(v => `<option value="${v.plate}">${v.plate} – ${v.model} (${fmt(v.daily_rate)}/día)</option>`).join('');
}

function populateCustomerSelect() {
  const sel = document.getElementById('nr-customer');
  if (!sel) return;
  sel.innerHTML = '<option value="">Seleccionar cliente...</option>' +
    window._customers.map(c => `<option value="${c.id}">${c.name} (${c.id})</option>`).join('');
}

/* ── Table sort setup ───────────────────────────────────────── */
function setupSort(tableId, section, cols) {
  const headers = document.querySelectorAll(`#${tableId} thead th[data-col]`);
  headers.forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      const ss  = sortState[section];
      if (ss.col === col) ss.dir *= -1;
      else { ss.col = col; ss.dir = 1; }
      headers.forEach(h => { h.classList.remove('sorted'); h.querySelector('.sort-arrow').textContent = '↕'; });
      th.classList.add('sorted');
      th.querySelector('.sort-arrow').textContent = ss.dir === 1 ? '↑' : '↓';
      if (section === 'vehicles')  renderVehiclesTable(window._vehicles);
      if (section === 'customers') renderCustomersTable(window._customers);
      if (section === 'rentals')   renderRentalsTable(window._rentals);
    });
  });
}

/* ── Init ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setupSort('vehicles-table',  'vehicles',  ['plate','model','year','daily_rate']);
  setupSort('customers-table', 'customers', ['id','name','email']);
  setupSort('rentals-table',   'rentals',   ['id','cost','start_date']);

  // Open modal buttons
  document.getElementById('btn-new-vehicle')?.addEventListener('click',  () => openModal('modal-vehicle'));
  document.getElementById('btn-new-customer')?.addEventListener('click', () => openModal('modal-customer'));
  document.getElementById('btn-new-rental')?.addEventListener('click',   () => {
    populateVehicleSelect();
    populateCustomerSelect();
    openModal('modal-rental');
  });
  document.getElementById('btn-strategy')?.addEventListener('click', openStrategyModal);
  document.querySelector('.strategy-badge')?.addEventListener('click', openStrategyModal);

  // Form submits
  document.getElementById('form-vehicle')?.addEventListener('submit',  submitNewVehicle);
  document.getElementById('form-customer')?.addEventListener('submit', submitNewCustomer);
  document.getElementById('form-rental')?.addEventListener('submit',   submitNewRental);
  document.getElementById('form-strategy')?.addEventListener('submit', submitStrategy);

  // Live quote
  ['nr-plate','nr-days','nr-km'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', updateQuote);
    document.getElementById(id)?.addEventListener('input',  updateQuote);
  });

  // Search / filter live
  document.getElementById('v-search')?.addEventListener('input', filterVehicles);
  document.getElementById('v-type-filter')?.addEventListener('change', filterVehicles);
  document.getElementById('v-status-filter')?.addEventListener('change', filterVehicles);
  document.getElementById('c-search')?.addEventListener('input', filterCustomers);
  document.getElementById('r-search')?.addEventListener('input', filterRentals);
  document.getElementById('r-status-filter')?.addEventListener('change', filterRentals);

  // Load initial page
  navigate('dashboard');
});
