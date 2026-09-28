/* ============================================================
   INNO99 · interazioni del sito
   ============================================================ */
(function () {
  "use strict";
  // Riserva: se la pagina arriva in http (Cloudflare senza "Always Use HTTPS"),
  // passa alla versione https, così esiste un solo indirizzo per motori e utenti.
  if (location.protocol === "http:" && /\.(com|it)$/.test(location.hostname)) {
    location.replace("https://" + location.host + location.pathname + location.search + location.hash);
    return;
  }

  // Il vecchio sito era una pagina unica: i link del tipo inno99.it/#stampa
  // portano ora alla pagina giusta.
  const VECCHI = {
    "#prossimo": "/inno-talks/2/",
    "#diretta": "/inno-talks/2/#diretta",
    "#evento": "/inno-talks/1/",
    "#stampa": "/rassegna-stampa/",
    "#podcast": "/inno-podcast/",
    "#progetto": "/chi-siamo/",
    "#faq": "/chi-siamo/#faq",
    "#contatti": "/contatti/",
  };
  if ((location.pathname === "/" || location.pathname === "/index.html") && VECCHI[location.hash]) {
    location.replace(VECCHI[location.hash]);
    return;
  }

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* ---------- intestazione: stato, barra di lettura, torna su ---------- */
  const head = document.getElementById("site-head");
  const bar = head && head.querySelector(".progress span");
  const toTop = document.querySelector(".to-top");
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    if (head) head.classList.toggle("scrolled", y > 20);
    if (bar) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.transform = "scaleX(" + (h > 0 ? Math.min(y / h, 1) : 0) + ")";
    }
    if (toTop) toTop.classList.toggle("show", y > 700);
    ticking = false;
  };
  window.addEventListener("scroll", () => {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" }));

  /* ---------- menu a tendina degli Inno Talks ---------- */
  document.querySelectorAll(".has-mega").forEach((li) => {
    const btn = li.querySelector(".mega-toggle");
    if (!btn) return;
    let timer = null;
    const set = (open) => {
      li.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    };
    btn.addEventListener("click", (e) => { e.stopPropagation(); set(!li.classList.contains("open")); });
    if (fine) {
      li.addEventListener("mouseenter", () => { clearTimeout(timer); set(true); });
      li.addEventListener("mouseleave", () => { timer = setTimeout(() => set(false), 180); });
    }
    li.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { set(false); btn.focus(); }
    });
    li.addEventListener("focusout", (e) => { if (!li.contains(e.relatedTarget)) set(false); });
    document.addEventListener("click", (e) => { if (!li.contains(e.target)) set(false); });
  });

  /* ---------- menu mobile ---------- */
  const burger = document.querySelector(".burger");
  const drawer = document.getElementById("drawer");
  if (burger && drawer) {
    const setD = (open) => {
      drawer.classList.toggle("open", open);
      drawer.inert = !open;
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      burger.setAttribute("aria-label", open ? "Chiudi il menu" : "Apri il menu");
      document.body.classList.toggle("no-scroll", open);
    };
    drawer.inert = true;
    burger.addEventListener("click", () => setD(!drawer.classList.contains("open")));
    drawer.addEventListener("click", (e) => { if (e.target.closest("a")) setD(false); });
    window.addEventListener("keydown", (e) => { if (e.key === "Escape" && drawer.classList.contains("open")) { setD(false); burger.focus(); } });
    window.addEventListener("resize", () => { if (window.innerWidth > 980 && drawer.classList.contains("open")) setD(false); });
  }

  /* ---------- comparsa degli elementi durante lo scorrimento ---------- */
  document.querySelectorAll("[data-stagger]").forEach((box) => {
    [...box.querySelectorAll(":scope > .reveal, :scope > * > .reveal")].forEach((el, i) => el.classList.add("d" + Math.min(i, 5)));
  });
  const reveals = document.querySelectorAll(".reveal, .reveal-line");
  if ("IntersectionObserver" in window && !reduce) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("in"); obs.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("in"));
  }

  /* ---------- contatori ---------- */
  const nums = document.querySelectorAll(".stat .num[data-to]");
  const count = (el) => {
    const to = +el.dataset.to, suf = el.dataset.suffix || "";
    if (reduce) { el.textContent = to + suf; return; }
    const t0 = performance.now(), dur = 1500;
    const step = (t) => {
      const p = Math.min((t - t0) / dur, 1);
      el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))) + (p === 1 ? suf : "");
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  if ("IntersectionObserver" in window) {
    const io2 = new IntersectionObserver((entries, obs) => {
      entries.forEach((e) => { if (e.isIntersecting) { count(e.target); obs.unobserve(e.target); } });
    }, { threshold: 0.6 });
    nums.forEach((n) => { n.textContent = "0"; io2.observe(n); });
  }

  /* ---------- luce che segue il puntatore e inclinazione 3D ---------- */
  if (fine && !reduce) {
    document.querySelectorAll(".card").forEach((card) => {
      card.addEventListener("pointermove", (e) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--mx", e.clientX - r.left + "px");
        card.style.setProperty("--my", e.clientY - r.top + "px");
      });
    });
    document.querySelectorAll(".tilt").forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        el.style.setProperty("--ry", (x * 7).toFixed(2) + "deg");
        el.style.setProperty("--rx", (-y * 7).toFixed(2) + "deg");
      });
      el.addEventListener("pointerleave", () => {
        el.style.setProperty("--ry", "0deg");
        el.style.setProperty("--rx", "0deg");
      });
    });
  }

  /* ---------- costellazione della home ---------- */
  const canvas = document.getElementById("constellation");
  if (canvas && !reduce) {
    const ctx = canvas.getContext("2d");
    let w, h, dpr, pts, raf = null;
    const mouse = { x: -999, y: -999 };
    const conf = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.min(Math.floor((w * h) / 13000), 110);
      pts = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.6,
      }));
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const maxD = 130;
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        const mdx = p.x - mouse.x, mdy = p.y - mouse.y, md = Math.hypot(mdx, mdy);
        if (md < 150 && md > 0) { p.x += (mdx / md) * 0.6; p.y += (mdy / md) * 0.6; }
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j], d = Math.hypot(p.x - q.x, p.y - q.y);
          if (d < maxD) {
            ctx.strokeStyle = "rgba(237,125,43," + (1 - d / maxD) * 0.5 + ")";
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
          }
        }
        ctx.fillStyle = "rgba(242,147,63,.9)";
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
      }
      raf = requestAnimationFrame(draw);
    };
    const start = () => { conf(); cancelAnimationFrame(raf); draw(); };
    window.addEventListener("resize", start);
    window.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
    });
    new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) { if (!raf) draw(); } else { cancelAnimationFrame(raf); raf = null; }
    })).observe(canvas);
    start();
  }

  /* ---------- caroselli fotografici ---------- */
  document.querySelectorAll("[data-carousel]").forEach((car) => {
    const track = car.querySelector(".car-track");
    const slides = [...track.children];
    const dotsBox = car.querySelector(".car-dots");
    let current = 0, timer = null;
    const dots = slides.map((_, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("role", "tab");
      b.setAttribute("aria-label", "Foto " + (i + 1) + " di " + slides.length);
      b.addEventListener("click", () => { go(i); stop(); });
      dotsBox.appendChild(b);
      return b;
    });
    const mark = (i) => { current = i; dots.forEach((d, k) => d.setAttribute("aria-selected", k === i ? "true" : "false")); };
    const go = (i) => {
      const n = (i + slides.length) % slides.length;
      track.scrollTo({ left: slides[n].offsetLeft, behavior: reduce ? "auto" : "smooth" });
      mark(n);
    };
    const stop = () => { clearInterval(timer); timer = null; };
    const play = () => { if (!reduce && !timer) timer = setInterval(() => go(current + 1), 5000); };
    car.querySelector(".car-prev").addEventListener("click", () => { go(current - 1); stop(); });
    car.querySelector(".car-next").addEventListener("click", () => { go(current + 1); stop(); });
    track.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { go(current + 1); stop(); }
      if (e.key === "ArrowLeft") { go(current - 1); stop(); }
    });
    let raf = null;
    track.addEventListener("scroll", () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => mark(Math.round(track.scrollLeft / track.clientWidth)));
    }, { passive: true });
    track.addEventListener("pointerdown", stop, { passive: true });
    car.addEventListener("mouseenter", stop);
    car.addEventListener("focusin", stop);
    new IntersectionObserver((es) => es.forEach((e) => (e.isIntersecting ? play() : stop())), { threshold: 0.4 }).observe(car);
    mark(0);
    // nella galleria le foto verticali e orizzontali convivono: dietro ognuna c'è la stessa foto sfocata
    if (car.closest(".gallery")) {
      slides.forEach((s) => {
        const img = s.querySelector("img");
        if (!img) return;
        const set = () => s.style.setProperty("--bg", 'url("' + (img.currentSrc || img.src) + '")');
        if (img.complete && img.naturalWidth) set(); else img.addEventListener("load", set, { once: true });
      });
    }
  });

  /* ---------- filtri della rassegna stampa ---------- */
  const pf = document.querySelector("[data-filters]");
  if (pf) {
    const cards = [...document.querySelectorAll(".press-card[data-evento]")];
    const blocks = [...document.querySelectorAll(".press-block")];
    const counter = pf.querySelector(".pf-count b");
    const empty = document.querySelector(".pf-empty");
    let fe = "*", ft = "*";
    const apply = () => {
      let n = 0;
      cards.forEach((c) => {
        const ok = (fe === "*" || c.dataset.evento === fe) && (ft === "*" || c.dataset.tipo === ft);
        c.hidden = !ok;
        if (ok) { n++; c.classList.add("in"); }
      });
      blocks.forEach((b) => { b.hidden = !b.querySelector(".press-card:not([hidden])"); });
      if (counter) counter.textContent = n;
      if (empty) empty.hidden = n > 0;
    };
    pf.addEventListener("click", (e) => {
      const b = e.target.closest("button.chip");
      if (!b) return;
      b.closest(".pf-group").querySelectorAll(".chip").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
      if (b.dataset.fEvento) {
        fe = b.dataset.fEvento;
        history.replaceState(null, "", fe === "*" ? location.pathname : "?serata=" + fe);
      }
      if (b.dataset.fTipo) ft = b.dataset.fTipo;
      apply();
    });
    const q = new URLSearchParams(location.search).get("serata");
    if (q && /^\d+$/.test(q)) { const b = pf.querySelector('[data-f-evento="' + q + '"]'); if (b) b.click(); }
  }
})();
