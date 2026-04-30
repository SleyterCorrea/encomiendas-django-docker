/* ================================================================
   Sistema de Encomiendas — JavaScript principal
   ================================================================ */

document.addEventListener('DOMContentLoaded', function () {

  // ── 1. Auto-dismiss de alertas flash después de 5s ────────────
  const flashMessages = document.querySelectorAll('#flash-messages .alert');
  flashMessages.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });

  // ── 2. Marcar enlace activo en la navbar ─────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar .nav-link').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── 3. Confirmar acciones destructivas ───────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const msg = el.getAttribute('data-confirm');
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  // ── 4. Tooltips de Bootstrap ──────────────────────────────────
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // ── 5. Marcar campos inválidos del formulario Django ──────────
  document.querySelectorAll('.invalid-feedback').forEach(function (el) {
    const input = el.previousElementSibling;
    if (input) input.classList.add('is-invalid');
  });

});
