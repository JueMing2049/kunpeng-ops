/* ============================================================
   KunPeng Report Kit · kit.js
   零依赖 · 原生 API
   ============================================================ */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. 主题 ---------- */
  function initTheme() {
    var root = document.documentElement;
    var saved = null;
    try { saved = localStorage.getItem('kit-theme'); } catch (e) {}
    if (saved) root.setAttribute('data-theme', saved);
    $$('[data-theme-toggle]').forEach(function (btn) {
      var set = function () { btn.textContent = root.getAttribute('data-theme') === 'dark' ? '☾' : '☀'; };
      set();
      btn.addEventListener('click', function () {
        var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem('kit-theme', next); } catch (e) {}
        set();
      });
    });
  }

  /* ---------- 1b. 语调切换（专业 / 通俗） ---------- */
  function initTone() {
    var root = document.documentElement;
    var btns = $$('[data-tone-toggle]');
    if (!btns.length) return;
    var saved = null;
    try { saved = localStorage.getItem('kit-tone'); } catch (e) {}
    if (saved) root.setAttribute('data-tone', saved);
    btns.forEach(function (btn) {
      function paint() {
        var plain = root.getAttribute('data-tone') === 'plain';
        btn.textContent = plain ? '切回专业版' : '通俗版';
        btn.setAttribute('aria-pressed', plain ? 'true' : 'false');
        btn.setAttribute('title', plain ? '当前为通俗表达，点击切回专业表达' : '当前为专业表达，点击切换为通俗表达');
      }
      paint();
      btn.addEventListener('click', function () {
        var next = root.getAttribute('data-tone') === 'plain' ? 'pro' : 'plain';
        root.setAttribute('data-tone', next);
        try { localStorage.setItem('kit-tone', next); } catch (e) {}
        paint();
      });
    });
  }

  /* ---------- 2. 滚动进度条 ---------- */
  function initProgress() {
    if ($('.sdp')) return;
    var d = document.createElement('div');
    d.className = 'sdp';
    document.body.appendChild(d);
  }

  /* ---------- 3. 渐入（失败安全：宁可不动效，不可让内容消失） ---------- */
  function show(el) {
    el.classList.add('in');
    if (el.classList.contains('reveal')) { countUp(el); growBars(el); }
  }

  function initReveal() {
    var els = $$('.reveal, .sda, .sda-par, [data-count]');
    if (!els.length) return;

    if (RM || !('IntersectionObserver' in window)) {
      els.forEach(show);
      countUp(document);
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        try {
          show(e.target);
          if (e.target.hasAttribute('data-count') && !e.target.closest('.reveal')) {
            countUp(e.target.parentNode || e.target);
          }
        } catch (err) { /* 单条失败不拖累其余 */ }
        io.unobserve(e.target);
      });
    }, { threshold: 0.06, rootMargin: '0px 0px -6% 0px' });
    els.forEach(function (el) { io.observe(el); });

    // 兜底：若观察器未按期回调，强制显示首屏范围内的内容
    setTimeout(function () {
      var vh = window.innerHeight || 800;
      $$('.reveal:not(.in)').forEach(function (el) {
        if (el.getBoundingClientRect().top < vh * 1.05) show(el);
      });
      countUp(document);
    }, 1600);
  }

  function trigger(el) {
    countUp(el);
    growBars(el);
  }

  /* ---------- 4. 数字滚动 ---------- */
  function countUp(scope) {
    $$('[data-count]', scope).forEach(function (el) {
      if (el.dataset.done) return;
      el.dataset.done = '1';
      var target = parseFloat(el.getAttribute('data-count'));
      var dec = parseInt(el.getAttribute('data-dec') || '0', 10);
      var pre = el.getAttribute('data-pre') || '';
      var suf = el.getAttribute('data-suf') || '';
      if (RM) { el.textContent = pre + target.toFixed(dec) + suf; return; }
      var t0 = null, dur = 1100, done = false;
      var safety = setTimeout(finish, dur + 400);
      function finish() {
        if (done) return;
        done = true;
        clearTimeout(safety);
        el.textContent = pre + target.toFixed(dec) + suf;
      }
      function tick(ts) {
        if (done) return;
        if (!t0) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1);
        var e = 1 - Math.pow(1 - p, 3);
        el.textContent = pre + (target * e).toFixed(dec) + suf;
        if (p < 1) requestAnimationFrame(tick);
        else finish();
      }
      requestAnimationFrame(tick);
    });
  }

  /* ---------- 5. 条形生长 ---------- */
  function growBars(scope) {
    $$('.bar', scope).forEach(function (b) { b.classList.add('in'); });
  }

  /* ---------- 6. 标签页 ---------- */
  function initTabs() {
    $$('[data-tabs]').forEach(function (group) {
      var btns = $$('[role="tab"]', group);
      var panes = $$('.tabpane', group);
      btns.forEach(function (btn, i) {
        btn.addEventListener('click', function () {
          btns.forEach(function (b) { b.setAttribute('aria-selected', 'false'); });
          panes.forEach(function (p) { p.classList.remove('on'); });
          btn.setAttribute('aria-selected', 'true');
          if (panes[i]) panes[i].classList.add('on');
        });
        btn.addEventListener('keydown', function (e) {
          var n = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
          if (!n) return;
          e.preventDefault();
          var t = btns[(i + n + btns.length) % btns.length];
          t.focus(); t.click();
        });
      });
      if (btns[0]) btns[0].setAttribute('aria-selected', 'true');
      if (panes[0]) panes[0].classList.add('on');
    });
  }

  /* ---------- 7. 筛选 ---------- */
  function initFilter() {
    $$('[data-filter]').forEach(function (wrap) {
      var chips = $$('.chip', wrap);
      var items = $$('[data-tags]', document);
      chips.forEach(function (chip) {
        chip.addEventListener('click', function () {
          chips.forEach(function (c) { c.classList.remove('on'); });
          chip.classList.add('on');
          var k = chip.getAttribute('data-k');
          items.forEach(function (it) {
            var show = k === 'all' || (it.getAttribute('data-tags') || '').split(' ').indexOf(k) > -1;
            it.style.display = show ? '' : 'none';
          });
        });
      });
    });
  }

  /* ---------- 8. 对比滑块 ---------- */
  function initCompare() {
    $$('.cmp').forEach(function (el) {
      var h = $('.cmp__h', el);
      if (!h) return;
      var drag = false;
      function set(clientX) {
        var r = el.getBoundingClientRect();
        var p = Math.max(2, Math.min(98, ((clientX - r.left) / r.width) * 100));
        el.style.setProperty('--cut', p + '%');
      }
      h.addEventListener('pointerdown', function (e) { drag = true; h.setPointerCapture(e.pointerId); });
      h.addEventListener('pointermove', function (e) { if (drag) set(e.clientX); });
      h.addEventListener('pointerup', function () { drag = false; });
      h.addEventListener('pointercancel', function () { drag = false; });
      el.addEventListener('pointerdown', function (e) { if (e.target === el) set(e.clientX); });
    });
  }

  /* ---------- 9. 决策卡 ---------- */
  var DECISIONS = {};
  function initDecisions() {
    $$('.dcard').forEach(function (card) {
      var id = card.getAttribute('data-id') || 'D';
      var opts = $$('.dopt', card);
      opts.forEach(function (opt) {
        opt.addEventListener('click', function () {
          opts.forEach(function (o) { o.classList.remove('sel'); });
          opt.classList.add('sel');
        });
      });
      var okBtn = $('[data-act="confirm"]', card);
      var out = $('.dcard__out', card);
      if (okBtn) okBtn.addEventListener('click', function () {
        var sel = opts.filter(function (o) { return o.classList.contains('sel'); })[0];
        var noteEl = $('[data-note]', card);
        DECISIONS[id] = {
          id: id,
          title: card.getAttribute('data-title') || '',
          choice: sel ? sel.getAttribute('data-key') : null,
          label: sel ? sel.textContent.trim().slice(0, 40) : null,
          note: noteEl ? noteEl.value || null : null,
          at: new Date().toISOString()
        };
        if (out) out.textContent = '已记 ' + Object.keys(DECISIONS).length + ' 项';
        card.style.borderColor = 'var(--jade)';
      });
    });
    var dump = $('[data-act="export"]');
    if (dump) dump.addEventListener('click', function () {
      var data = { decisions: DECISIONS, exportedAt: new Date().toISOString() };
      copy(JSON.stringify(data, null, 2));
      var t = dump.textContent; dump.textContent = '✓ 已复制 JSON';
      setTimeout(function () { dump.textContent = t; }, 1600);
    });
  }

  /* ---------- 10. 批注锚点 ---------- */
  function initAnno() {
    $$('[data-block]').forEach(function (blk) {
      if (blk.querySelector(':scope > .annotools')) return;
      var tools = document.createElement('div');
      tools.className = 'annotools';
      var id = blk.getAttribute('data-block');
      tools.innerHTML = '<button class="anno__btn" type="button">⌖ 复制锚点</button>';
      tools.querySelector('button').addEventListener('click', function () {
        copy('[data-block="' + id + '"]');
        var b = tools.querySelector('button'), t = b.textContent;
        b.textContent = '✓ 已复制';
        setTimeout(function () { b.textContent = t; }, 1400);
        blk.classList.add('flash');
        setTimeout(function () { blk.classList.remove('flash'); }, 900);
      });
      if (getComputedStyle(blk).position === 'static') blk.style.position = 'relative';
      blk.appendChild(tools);
    });
  }

  /* ---------- 11. 目录 scrollspy ---------- */
  /* ---------- 10b. 就地批注：选中即批 ---------- */
  function initAnnotation() {
    if (!document.body.hasAttribute('data-annotate')) return;

    var TYPES = [['agree','认可'],['reject','否决'],['hold','悬置'],['delegate','代议'],['note','补充']];
    var items = [];
    var cur = null;
    var typeEl = null;

    var pop = document.createElement('div');
    pop.className = 'anno-pop';
    pop.innerHTML = '<button type="button">＋ 批注</button>';

    var form = document.createElement('div');
    form.className = 'anno-form';
    form.innerHTML =
      '<div class="anno-form__q"></div>' +
      '<div class="anno-types">' + TYPES.map(function (t) {
        return '<button class="anno-type" type="button" data-t="' + t[0] + '">' + t[1] + '</button>';
      }).join('') + '</div>' +
      '<textarea rows="3" placeholder="写一句…（Ctrl+Enter 加入）"></textarea>' +
      '<div class="anno-form__f">' +
        '<button class="btn" type="button" data-a="cancel">取消</button>' +
        '<button class="btn pri" type="button" data-a="save">加入批注</button>' +
      '</div>';

    var basket = document.createElement('div');
    basket.className = 'anno-basket';
    basket.innerHTML =
      '<div class="anno-basket__h">✎ 批注 <b>0</b> 条 <i>展开 ▸</i></div>' +
      '<div class="anno-basket__b"></div>' +
      '<div class="anno-basket__f">' +
        '<button class="btn pri" type="button" data-a="export">导出 JSON</button>' +
        '<button class="btn" type="button" data-a="text">复制为文本</button>' +
      '</div>';

    document.body.appendChild(pop);
    document.body.appendChild(form);
    document.body.appendChild(basket);

    var qEl = $('.anno-form__q', form);
    var taEl = $('textarea', form);

    function hidePop() { pop.classList.remove('on'); }
    function hideForm() { form.classList.remove('on'); }

    document.addEventListener('mouseup', function (e) {
      if (form.contains(e.target) || pop.contains(e.target) || basket.contains(e.target)) return;
      setTimeout(function () {
        var sel = window.getSelection();
        if (!sel || sel.isCollapsed || sel.rangeCount === 0) { hidePop(); return; }
        var txt = String(sel).replace(/\s+/g, ' ').trim();
        if (txt.length < 2) { hidePop(); return; }
        var range = sel.getRangeAt(0);
        var node = range.commonAncestorContainer;
        if (node.nodeType === 3) node = node.parentNode;
        var blk = node.closest ? node.closest('[data-block]') : null;
        if (!blk) { hidePop(); return; }
        var r = range.getBoundingClientRect();
        if (!r || (!r.width && !r.height)) { hidePop(); return; }
        cur = {
          block: blk.getAttribute('data-block'),
          quote: txt.slice(0, 90),
          rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]
        };
        pop.style.left = (window.scrollX + r.left + Math.max(0, r.width / 2 - 36)) + 'px';
        pop.style.top = (window.scrollY + r.bottom + 7) + 'px';
        pop.classList.add('on');
        hideForm();
      }, 12);
    });

    pop.addEventListener('click', function () {
      if (!cur) return;
      qEl.textContent = '「' + cur.quote + '」';
      taEl.value = '';
      typeEl = null;
      $$('.anno-type', form).forEach(function (b) { b.classList.remove('on'); });
      var pr = pop.getBoundingClientRect();
      var maxL = window.scrollX + document.documentElement.clientWidth - 330;
      form.style.left = Math.min(window.scrollX + pr.left, maxL) + 'px';
      form.style.top = (window.scrollY + pr.bottom + 6) + 'px';
      hidePop();
      form.classList.add('on');
      taEl.focus();
    });

    function save() {
      var note = taEl.value.trim();
      if (!note) { taEl.focus(); return; }
      items.push({
        id: 'A-' + (items.length + 1),
        block: cur.block,
        quote: cur.quote,
        type: typeEl || 'note',
        note: note,
        rect: cur.rect,
        at: new Date().toISOString()
      });
      taEl.value = '';
      hideForm();
      render();
      basket.classList.add('open');
    }

    function labelOf(t) {
      var hit = TYPES.filter(function (x) { return x[0] === t; })[0];
      return hit ? hit[1] : '补充';
    }
    function esc(v) {
      return String(v).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }
    function flashBtn(b, txt) {
      var old = b.textContent;
      b.textContent = txt;
      setTimeout(function () { b.textContent = old; }, 1500);
    }

    function render() {
      $('.anno-basket__h b', basket).textContent = items.length;
      $('.anno-basket__h i', basket).textContent = basket.classList.contains('open') ? '收起 ▾' : '展开 ▸';
      var body = $('.anno-basket__b', basket);
      body.innerHTML = items.map(function (it, i) {
        return '<div class="anno-item">' +
          '<div class="anno-item__m"><span class="anno-t" data-t="' + it.type + '">' + labelOf(it.type) + '</span>' +
          '<span>' + esc(it.block) + '</span></div>' +
          '<div class="anno-item__q">「' + esc(it.quote) + '」</div>' +
          '<div class="anno-item__n">' + esc(it.note) + '</div>' +
          '<button class="anno-item__x" type="button" data-i="' + i + '">×</button></div>';
      }).join('') || '<div class="anno-item" style="color:var(--txt3)">还没有批注。选中页面上任意一句，点「＋ 批注」。</div>';
    }

    form.addEventListener('click', function (e) {
      var t = e.target.closest('.anno-type');
      if (t) {
        $$('.anno-type', form).forEach(function (b) { b.classList.remove('on'); });
        t.classList.add('on');
        typeEl = t.getAttribute('data-t');
        return;
      }
      var a = e.target.closest('[data-a]');
      if (!a) return;
      if (a.getAttribute('data-a') === 'cancel') hideForm();
      else save();
    });

    basket.addEventListener('click', function (e) {
      var x = e.target.closest('.anno-item__x');
      if (x) { items.splice(+x.getAttribute('data-i'), 1); render(); return; }
      var a = e.target.closest('[data-a]');
      if (!a) {
        if (e.target.closest('.anno-basket__h')) {
          basket.classList.toggle('open');
          $('.anno-basket__h i', basket).textContent = basket.classList.contains('open') ? '收起 ▾' : '展开 ▸';
        }
        return;
      }
      if (a.getAttribute('data-a') === 'export') {
        copy(JSON.stringify({ doc: document.title, annotations: items, exportedAt: new Date().toISOString() }, null, 2));
        flashBtn(a, '✓ 已复制 JSON');
      } else {
        copy(items.map(function (it, i) {
          return (i + 1) + '. [' + labelOf(it.type) + '][' + it.block + '] 「' + it.quote + '」→ ' + it.note;
        }).join('\n') || '（无批注）');
        flashBtn(a, '✓ 已复制文本');
      }
    });

    taEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); save(); }
      if (e.key === 'Escape') hideForm();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { hidePop(); hideForm(); }
    });

    window.KitAnnotations = function () { return items; };
  }

  function initToc() {
    var links = $$('.toc a[href^="#"]');
    if (!links.length) return;
    var secs = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    var navs = $$('.kit-nav a[href^="#"]');
    var navSecs = navs.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    function onScroll() {
      var y = window.scrollY + 150, idx = 0;
      for (var i = 0; i < secs.length; i++) { if (secs[i] && secs[i].offsetTop <= y) idx = i; }
      links.forEach(function (a, i) { a.classList.toggle('on', i === idx); });
      var ni = 0;
      for (var j = 0; j < navSecs.length; j++) { if (navSecs[j] && navSecs[j].offsetTop <= y) ni = j; }
      navs.forEach(function (a, i) { a.classList.toggle('on', i === ni); });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- 12. 滚动叙事 ---------- */
  function initScrolly() {
    $$('.scrolly').forEach(function (sc) {
      var steps = $$('.stepc', sc);
      var graphic = $('.scrolly__g', sc);
      if (!steps.length || !graphic) return;
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting) {
            var i = steps.indexOf(e.target);
            steps.forEach(function (s) { s.classList.remove('on'); });
            e.target.classList.add('on');
            graphic.setAttribute('data-state', i + 1);
            $$('[data-fig]', graphic).forEach(function (f) {
              f.style.display = f.getAttribute('data-fig') === String(i + 1) ? '' : 'none';
            });
          }
        });
      }, { rootMargin: '-45% 0px -45% 0px' });
      steps.forEach(function (s) { io.observe(s); });
    });
  }

  /* ---------- 13. 时间轴高亮 ---------- */
  function initTimeline() {
    $$('.tl__i').forEach(function (it) {
      if (RM) { it.classList.add('on'); return; }
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) it.classList.add('on'); });
      }, { rootMargin: '-30% 0px -40% 0px' });
      io.observe(it);
    });
  }

  /* ---------- 14. 复制为 Markdown ---------- */
  function initCopyMd() {
    $$('[data-act="copy-md"]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var root = $('#md-source') || $('main') || document.body;
        copy(toMd(root));
        var t = btn.textContent; btn.textContent = '✓ 已复制 Markdown';
        setTimeout(function () { btn.textContent = t; }, 1700);
      });
    });
  }

  function toMd(root) {
    var out = [];
    var nodes = root.querySelectorAll('h1,h2,h3,h4,p,li,figcaption,.quote p,.stat,.kpi,.tbl table,pre');
    nodes.forEach(function (n) {
      if (n.closest('.annotools')) return;
      var tag = n.tagName.toLowerCase();
      var txt = (n.textContent || '').replace(/\s+/g, ' ').trim();
      if (!txt) return;
      if (tag === 'h1') out.push('# ' + txt);
      else if (tag === 'h2') out.push('\n## ' + txt);
      else if (tag === 'h3') out.push('\n### ' + txt);
      else if (tag === 'h4') out.push('\n#### ' + txt);
      else if (tag === 'li') out.push('- ' + txt);
      else if (tag === 'figcaption') out.push('> ' + txt);
      else if (tag === 'pre') out.push('```\n' + n.textContent.trim() + '\n```');
      else if (tag === 'table') out.push(mdTable(n));
      else if (n.classList.contains('stat') || n.classList.contains('kpi')) out.push('- ' + txt);
      else out.push(txt);
    });
    return out.join('\n').replace(/\n{3,}/g, '\n\n');
  }

  function mdTable(t) {
    var rows = $$('tr', t);
    if (!rows.length) return '';
    var lines = rows.map(function (r) {
      return '| ' + $$('th,td', r).map(function (c) {
        return (c.textContent || '').replace(/\s+/g, ' ').trim();
      }).join(' | ') + ' |';
    });
    lines.splice(1, 0, '|' + $$('th', rows[0]).map(function () { return ' --- '; }).join('|') + '|');
    return lines.join('\n');
  }

  /* ---------- 工具 ---------- */
  function copy(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).catch(function () { fallback(txt); });
    } else fallback(txt);
  }
  function fallback(txt) {
    var ta = document.createElement('textarea');
    ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  /* ---------- 启动 ---------- */
  function boot() {
    initTheme(); initTone(); initProgress();
    initTabs(); initFilter(); initCompare();
    initDecisions(); initAnno(); initToc();
    initScrolly(); initTimeline(); initCopyMd(); initAnnotation();
    initReveal();
    // 首屏前几段无需等滚动，避免闪一下
    setTimeout(function () {
      $$('.reveal').slice(0, 3).forEach(function (el) {
        el.classList.add('in'); countUp(el); growBars(el);
      });
    }, 60);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.Kit = { copy: copy, decisions: function () { return DECISIONS; } };
})();
