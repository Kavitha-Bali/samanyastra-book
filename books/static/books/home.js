function toggleSearch() {
  var box = document.getElementById('mobileSearch');
  var trigger = document.querySelector('.hamburger');
  var open = box.classList.toggle('open');
  if (trigger) trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
  if (open) {
    var input = box.querySelector('input');
    if (input) input.focus();
  }
}

(function mobileSearchDismiss() {
  var box = document.getElementById('mobileSearch');
  var trigger = document.querySelector('.hamburger');
  if (!box || !trigger) return;

  document.addEventListener('click', function (e) {
    if (!box.classList.contains('open')) return;
    if (box.contains(e.target) || trigger.contains(e.target)) return;
    box.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && box.classList.contains('open')) {
      box.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
      trigger.focus();
    }
  });
})();

(function navMenu() {
  var trigger = document.getElementById('navMenuTrigger');
  var panel = document.getElementById('navMenuPanel');
  if (!trigger || !panel) return;

  function close() {
    panel.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
  }

  trigger.addEventListener('click', function () {
    var open = panel.classList.toggle('open');
    trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  document.addEventListener('click', function (e) {
    if (!panel.classList.contains('open')) return;
    if (panel.contains(e.target) || trigger.contains(e.target)) return;
    close();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel.classList.contains('open')) {
      close();
      trigger.focus();
    }
  });
})();

/* ── Star-rating fill (avoids Django tags inside style attrs) ── */
(function starRatings() {
  Array.prototype.forEach.call(document.querySelectorAll('.stars-fg[data-pct]'), function (el) {
    el.style.width = el.getAttribute('data-pct') + '%';
  });
})();

(function typeTerminal() {
  var el = document.getElementById('termLines');
  if (!el) return;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fullText = el.textContent;

  var cursor = document.createElement('span');
  cursor.className = 'term-cursor';

  if (reduceMotion) {
    el.appendChild(cursor);
    return;
  }

  el.textContent = '';
  var i = 0;
  var speed = 18;

  function step() {
    if (i < fullText.length) {
      el.textContent = fullText.slice(0, i + 1);
      el.appendChild(cursor);
      i++;
      var ch = fullText[i - 1];
      window.setTimeout(step, ch === '\n' ? speed * 6 : speed);
    } else {
      el.appendChild(cursor);
    }
  }
  window.setTimeout(step, 400);
})();

/* ── Nav scroll state ── */
(function navScrollState() {
  var nav = document.querySelector('nav');
  if (!nav) return;
  function update() {
    nav.classList.toggle('is-scrolled', window.scrollY > 8);
  }
  update();
  window.addEventListener('scroll', update, { passive: true });
})();

/* ── Toasts ── */
(function toasts() {
  var stack = document.getElementById('toastStack');
  if (!stack) return;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function dismiss(toast) {
    if (reduceMotion) {
      toast.remove();
      return;
    }
    toast.classList.add('is-leaving');
    toast.addEventListener('animationend', function () { toast.remove(); }, { once: true });
  }

  Array.prototype.forEach.call(stack.querySelectorAll('.toast-msg'), function (toast) {
    var closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) closeBtn.addEventListener('click', function () { dismiss(toast); });
    window.setTimeout(function () { dismiss(toast); }, 4500);
  });
})();

/* ── Back to top ── */
(function backToTop() {
  var btn = document.getElementById('backToTop');
  if (!btn) return;
  function update() {
    btn.classList.toggle('is-visible', window.scrollY > 600);
  }
  update();
  window.addEventListener('scroll', update, { passive: true });
  btn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  });
})();

/* ── Cart / buy button loading state ── */
(function buttonLoadingState() {
  Array.prototype.forEach.call(document.querySelectorAll('.card-actions form.btn-form'), function (form) {
    form.addEventListener('submit', function () {
      var btn = form.querySelector('button[type="submit"]');
      if (!btn || btn.classList.contains('is-loading')) return;
      btn.classList.add('is-loading');
      btn.disabled = true;
    });
  });
})();

/* ── Scroll reveal for book cards ── */
(function scrollReveal() {
  var cards = document.querySelectorAll('.books-grid .card');
  if (!cards.length) return;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || typeof IntersectionObserver === 'undefined') return;

  Array.prototype.forEach.call(cards, function (card) { card.classList.add('reveal'); });

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

  Array.prototype.forEach.call(cards, function (card) { observer.observe(card); });
})();

/* ── Cover image fade-in ── */
(function coverFadeIn() {
  var imgs = document.querySelectorAll('.card-thumb');
  Array.prototype.forEach.call(imgs, function (img) {
    if (img.complete && img.naturalWidth > 0) return;
    img.classList.add('card-thumb--loading');
    img.addEventListener('load', function () { img.classList.remove('card-thumb--loading'); });
    img.addEventListener('error', function () { img.classList.remove('card-thumb--loading'); });
  });
})();

/* ── Wishlist (save for later, stored on this device) ── */
(function wishlist() {
  var buttons = document.querySelectorAll('.wishlist-btn');
  if (!buttons.length) return;
  var STORAGE_KEY = 'samanyastra_saved_books';

  function getSaved() {
    try { return JSON.parse(window.localStorage.getItem(STORAGE_KEY)) || []; }
    catch (e) { return []; }
  }
  function setSaved(ids) {
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids)); } catch (e) { /* storage unavailable */ }
  }

  var saved = getSaved();

  Array.prototype.forEach.call(buttons, function (btn) {
    var card = btn.closest('.card');
    var id = card ? card.getAttribute('data-book-id') : null;
    if (!id) return;
    var icon = btn.querySelector('i');

    function paint(isSaved) {
      btn.classList.toggle('is-saved', isSaved);
      btn.setAttribute('aria-pressed', isSaved ? 'true' : 'false');
      if (icon) icon.className = isSaved ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
    }
    paint(saved.indexOf(id) !== -1);

    btn.addEventListener('click', function () {
      saved = getSaved();
      var idx = saved.indexOf(id);
      if (idx === -1) { saved.push(id); paint(true); }
      else { saved.splice(idx, 1); paint(false); }
      setSaved(saved);
    });
  });
})();

/* ── Filter by language + sort ── */
(function booksToolbar() {
  var toolbar = document.getElementById('booksToolbar');
  var grid = document.querySelector('.books-grid');
  if (!toolbar || !grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var chipRow = document.getElementById('langChips');
  var sortSelect = document.getElementById('sortSelect');
  var noMatches = document.getElementById('noFilterMatches');
  var resetBtn = document.getElementById('resetFilters');
  var activeLang = 'all';

  var languages = [];
  cards.forEach(function (card) {
    var lang = card.getAttribute('data-language');
    if (lang && languages.indexOf(lang) === -1) languages.push(lang);
  });

  if (languages.length < 2) {
    toolbar.querySelector('.chip-row').style.display = 'none';
  } else {
    languages.sort().forEach(function (lang) {
      var chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'chip';
      chip.setAttribute('data-lang', lang);
      chip.textContent = lang;
      chipRow.appendChild(chip);
    });
  }

  function applyFilter() {
    var visibleCount = 0;
    cards.forEach(function (card) {
      var match = activeLang === 'all' || card.getAttribute('data-language') === activeLang;
      card.classList.toggle('hidden-by-filter', !match);
      if (match) visibleCount++;
    });
    if (noMatches) noMatches.hidden = visibleCount !== 0;
  }

  function applySort() {
    var mode = sortSelect ? sortSelect.value : 'default';
    var sorted = cards.slice();
    if (mode === 'price-asc') {
      sorted.sort(function (a, b) { return parseFloat(a.getAttribute('data-price')) - parseFloat(b.getAttribute('data-price')); });
    } else if (mode === 'price-desc') {
      sorted.sort(function (a, b) { return parseFloat(b.getAttribute('data-price')) - parseFloat(a.getAttribute('data-price')); });
    } else if (mode === 'rating-desc') {
      sorted.sort(function (a, b) { return parseFloat(b.getAttribute('data-rating')) - parseFloat(a.getAttribute('data-rating')); });
    } else if (mode === 'title-asc') {
      sorted.sort(function (a, b) { return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title')); });
    } else {
      sorted = cards;
    }
    sorted.forEach(function (card) { grid.appendChild(card); });
  }

  chipRow.addEventListener('click', function (e) {
    var chip = e.target.closest('.chip');
    if (!chip) return;
    activeLang = chip.getAttribute('data-lang');
    Array.prototype.forEach.call(chipRow.querySelectorAll('.chip'), function (c) {
      c.classList.toggle('active', c === chip);
    });
    applyFilter();
  });

  if (sortSelect) sortSelect.addEventListener('change', applySort);

  if (resetBtn) {
    resetBtn.addEventListener('click', function () {
      activeLang = 'all';
      Array.prototype.forEach.call(chipRow.querySelectorAll('.chip'), function (c) {
        c.classList.toggle('active', c.getAttribute('data-lang') === 'all');
      });
      applyFilter();
    });
  }
})();
