/* ================================================================
   Sistema de Encomiendas — JavaScript principal
   Sesión 07: WebSockets + UI reactiva
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

  // ══════════════════════════════════════════════════════════════
  // Sesión 07: WebSocket — Dashboard en tiempo real
  // Solo se activa si estamos en el dashboard (elementos presentes)
  // ══════════════════════════════════════════════════════════════

  const statActivas  = document.getElementById('stat-activas');
  const statTransito = document.getElementById('stat-transito');
  const statRetraso  = document.getElementById('stat-retraso');
  const wsStatus     = document.getElementById('ws-status');
  const activityFeed = document.getElementById('activity-feed');
  const feedBadge    = document.getElementById('feed-badge');
  const feedEmpty    = document.getElementById('feed-empty');
  const feedLastUpd  = document.getElementById('feed-last-update');
  const refreshBtn   = document.getElementById('ws-refresh-btn');

  // Solo inicializar en el dashboard
  if (!statActivas) return;

  let feedCount = 0;
  let reconnectTimeout = null;
  let dashboardWs = null;
  let feedWs = null;

  /* ── Helpers ─────────────────────────────────────────────── */

  /**
   * Anima un contador cuando cambia su valor (efecto pulse).
   */
  function animateStat(el, newValue) {
    const oldValue = parseInt(el.textContent, 10);
    if (oldValue === newValue) return;
    el.textContent = newValue;
    el.classList.add('stat-pulse');
    setTimeout(() => el.classList.remove('stat-pulse'), 600);
  }

  /**
   * Formatea una marca de tiempo ISO a hora local corta.
   */
  function formatTime(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  /**
   * Agrega un ítem al feed de actividad.
   */
  function addFeedItem(mensaje, timestamp) {
    if (feedEmpty) feedEmpty.style.display = 'none';

    feedCount++;
    if (feedBadge) feedBadge.textContent = feedCount;

    const item = document.createElement('div');
    item.className = 'feed-item border-bottom px-3 py-2 fade-in';
    item.innerHTML = `
      <div class="d-flex justify-content-between align-items-start">
        <span class="small text-dark">${escapeHtml(mensaje)}</span>
        <span class="text-muted" style="font-size:.7rem;white-space:nowrap;margin-left:8px">${formatTime(timestamp)}</span>
      </div>
    `;

    // Insertar al principio del feed
    activityFeed.insertBefore(item, activityFeed.firstChild);

    // Límite: máximo 50 ítems en el feed
    const items = activityFeed.querySelectorAll('.feed-item');
    if (items.length > 50) items[items.length - 1].remove();

    // Actualizar pie del feed
    if (feedLastUpd) feedLastUpd.textContent = `Última actividad: ${formatTime(timestamp)}`;
  }

  /**
   * Escapa HTML para evitar XSS en el feed.
   */
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  /* ── WebSocket 1: Dashboard Stats ──────────────────────────── */

  function connectDashboard() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/`;

    dashboardWs = new WebSocket(wsUrl);

    dashboardWs.onopen = function () {
      console.log('[WS] Dashboard conectado');
      if (wsStatus) {
        wsStatus.className = 'ms-2 badge bg-success';
        wsStatus.innerHTML = '<i class="fas fa-circle me-1" style="font-size:.55rem"></i>En vivo';
      }
      if (refreshBtn) refreshBtn.style.display = '';
    };

    dashboardWs.onmessage = function (e) {
      const msg = JSON.parse(e.data);

      if (msg.type === 'dashboard_update' && msg.stats) {
        const s = msg.stats;
        animateStat(statActivas,  s.total_activas  ?? 0);
        animateStat(statTransito, s.en_transito     ?? 0);
        animateStat(statRetraso,  s.con_retraso     ?? 0);
        console.log('[WS] Stats actualizadas:', s);
      }
    };

    dashboardWs.onclose = function (e) {
      console.warn('[WS] Dashboard desconectado, reconectando en 5s…', e.code);
      if (wsStatus) {
        wsStatus.className = 'ms-2 badge bg-danger';
        wsStatus.innerHTML = '<i class="fas fa-circle me-1" style="font-size:.55rem"></i>Desconectado';
      }
      if (refreshBtn) refreshBtn.style.display = 'none';
      // Reconexión automática
      reconnectTimeout = setTimeout(connectDashboard, 5000);
    };

    dashboardWs.onerror = function (err) {
      console.error('[WS] Error en Dashboard WebSocket:', err);
      dashboardWs.close();
    };
  }

  /* ── WebSocket 2: Feed de Actividad ────────────────────────── */

  function connectFeed() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/feed/`;

    feedWs = new WebSocket(wsUrl);

    feedWs.onopen = function () {
      console.log('[WS] Activity Feed conectado');
    };

    feedWs.onmessage = function (e) {
      const msg = JSON.parse(e.data);
      if (msg.type === 'activity' && msg.mensaje) {
        addFeedItem(msg.mensaje, msg.timestamp);
      }
    };

    feedWs.onclose = function (e) {
      console.warn('[WS] Feed desconectado, reconectando en 5s…');
      setTimeout(connectFeed, 5000);
    };

    feedWs.onerror = function (err) {
      console.error('[WS] Error en Feed WebSocket:', err);
      feedWs.close();
    };
  }

  /* ── Botón de refresh manual ──────────────────────────────── */

  if (refreshBtn) {
    refreshBtn.addEventListener('click', function () {
      if (dashboardWs && dashboardWs.readyState === WebSocket.OPEN) {
        dashboardWs.send(JSON.stringify({ action: 'refresh' }));
        const icon = refreshBtn.querySelector('i');
        icon.classList.add('fa-spin');
        setTimeout(() => icon.classList.remove('fa-spin'), 1000);
      }
    });
  }

  /* ── Limpiar al salir de la página ──────────────────────────── */

  window.addEventListener('beforeunload', function () {
    clearTimeout(reconnectTimeout);
    if (dashboardWs) dashboardWs.close();
    if (feedWs)      feedWs.close();
  });

  /* ── Iniciar conexiones ──────────────────────────────────────── */
  connectDashboard();
  connectFeed();

});

/* ── Estilos de animación en tiempo real (inyectados por JS) ── */
(function injectRealTimeStyles() {
  const style = document.createElement('style');
  style.textContent = `
    /* Pulso cuando un contador cambia */
    @keyframes statPulse {
      0%   { transform: scale(1);   }
      50%  { transform: scale(1.2); color: #ffc107; }
      100% { transform: scale(1);   }
    }
    .stat-pulse {
      animation: statPulse 0.6s ease;
    }

    /* Fade-in para ítems del feed */
    @keyframes feedFadeIn {
      from { opacity: 0; transform: translateY(-8px); }
      to   { opacity: 1; transform: translateY(0);    }
    }
    .feed-item.fade-in {
      animation: feedFadeIn 0.3s ease;
    }
    .feed-item:hover {
      background-color: rgba(0,0,0,.03);
    }
  `;
  document.head.appendChild(style);
})();
