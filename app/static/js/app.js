/* ─── Topbar Clock ──────────────────────────────────────────────── */
(function () {
  const el = document.getElementById('topbar-clock');
  if (!el) return;
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  tick();
  setInterval(tick, 10000);
})();

/* ─── Close sidebar on outside click (mobile) ──────────────────── */
document.addEventListener('click', function (e) {
  const sidebar = document.getElementById('sidebar');
  const toggle  = document.querySelector('.sidebar-toggle');
  if (sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  }
});

/* ─── Auto-dismiss alerts after 5 s ────────────────────────────── */
document.querySelectorAll('.alert').forEach(function (el) {
  setTimeout(function () {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(function () { el.remove(); }, 400);
  }, 5000);
});

/* ─── Delete confirmation modal ─────────────────────────────────── */
function openDeleteModal(formId, itemName) {
  const modal = document.getElementById('deleteModal');
  const label = document.getElementById('deleteItemName');
  const form  = document.getElementById('deleteForm');
  if (label) label.textContent = itemName || 'this item';
  if (form)  {
    const src = document.getElementById(formId);
    if (src) form.action = src.action;
  }
  if (modal) modal.classList.add('open');
}

function closeDeleteModal() {
  const modal = document.getElementById('deleteModal');
  if (modal) modal.classList.remove('open');
}

/* Close modal on backdrop click */
document.addEventListener('click', function (e) {
  const modal = document.getElementById('deleteModal');
  if (modal && e.target === modal) closeDeleteModal();
});

/* ─── Sort link helper ──────────────────────────────────────────── */
document.querySelectorAll('th[data-sort]').forEach(function (th) {
  const field   = th.dataset.sort;
  const current = new URLSearchParams(window.location.search).get('sort') || '';
  const a = th.querySelector('a');
  if (!a) return;
  if (current === field)       { a.classList.add('sort-asc');  a.href = sortUrl('-' + field); }
  else if (current === '-'+field) { a.classList.add('sort-desc'); a.href = sortUrl(field); }
  else                         { a.href = sortUrl(field); }
});

function sortUrl(val) {
  const p = new URLSearchParams(window.location.search);
  p.set('sort', val);
  p.delete('page');
  return '?' + p.toString();
}
