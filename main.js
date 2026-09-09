/* ============================================================
   INNO99 — interactions
   ============================================================ */
(function () {
  "use strict";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- NAV: scroll state + mobile toggle ---------- */
  const nav = document.getElementById("nav");
  const toggle = document.getElementById("navToggle");
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 30);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
  nav.querySelectorAll(".nav-links a").forEach((a) =>
    a.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    })
  );

  /* ---------- REVEAL on scroll ---------- */
  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduce) {
    // stagger siblings inside grids
    document.querySelectorAll(
      ".feature-grid,.speaker-grid,.event-points,.vert-grid"
    ).forEach((grid) => {
      [...grid.querySelectorAll(".reveal")].forEach((el, i) =>
        el.classList.add("d" + Math.min(i, 3))
      );
    });
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
    );
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("in"));
  }

  /* ---------- STAT counters ---------- */
  const nums = document.querySelectorAll(".stat .num");
  const animateNum = (el) => {
    if (el.dataset.static) {
      el.textContent = el.dataset.prefix;
      return;
    }
    const to = +el.dataset.to;
    const dur = 1400;
    const t0 = performance.now();
    const step = (t) => {
      const p = Math.min((t - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * eased);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  if ("IntersectionObserver" in window && !reduce) {
    const io2 = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            animateNum(e.target);
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.6 }
    );
    nums.forEach((n) => io2.observe(n));
  } else {
    nums.forEach((n) =>
      n.dataset.static ? (n.textContent = n.dataset.prefix) : (n.textContent = n.dataset.to)
    );
  }

  /* ---------- CARD pointer glow ---------- */
  if (!reduce) {
    document.querySelectorAll(".card").forEach((card) => {
      card.addEventListener("pointermove", (e) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--mx", e.clientX - r.left + "px");
        card.style.setProperty("--my", e.clientY - r.top + "px");
      });
    });
  }

  /* ---------- COUNTDOWN to 24 September 2026, 18:30 ---------- */
  const clocks = document.querySelectorAll("#countdown, [data-countdown]");
  if (clocks.length) {
    const target = new Date("2026-09-24T18:30:00").getTime();
    const pad = (n) => String(n).padStart(2, "0");
    const tick = () => {
      let diff = target - Date.now();
      const over = diff <= 0;
      const d = over ? 0 : Math.floor(diff / 86400000); if (!over) diff -= d * 86400000;
      const h = over ? 0 : Math.floor(diff / 3600000);  if (!over) diff -= h * 3600000;
      const m = over ? 0 : Math.floor(diff / 60000);    if (!over) diff -= m * 60000;
      const s = over ? 0 : Math.floor(diff / 1000);
      clocks.forEach((cd) => {
        cd.querySelector("[data-d]").textContent = pad(d);
        cd.querySelector("[data-h]").textContent = pad(h);
        cd.querySelector("[data-m]").textContent = pad(m);
        cd.querySelector("[data-s]").textContent = pad(s);
        if (over) cd.classList.add("live-now");
      });
      return !over;
    };
    if (tick()) setInterval(tick, 1000);
  }

  /* ---------- HERO constellation canvas ---------- */
  const canvas = document.getElementById("constellation");
  if (canvas && !reduce) {
    const ctx = canvas.getContext("2d");
    let w, h, dpr, pts, raf;
    const mouse = { x: -999, y: -999 };

    const conf = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(Math.floor((w * h) / 13000), 110);
      pts = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
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

        // mouse parallax pull
        const mdx = p.x - mouse.x, mdy = p.y - mouse.y;
        const md = Math.hypot(mdx, mdy);
        if (md < 150) {
          p.x += (mdx / md) * 0.6;
          p.y += (mdy / md) * 0.6;
        }

        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j];
          const dx = p.x - q.x, dy = p.y - q.y;
          const d = Math.hypot(dx, dy);
          if (d < maxD) {
            const a = (1 - d / maxD) * 0.5;
            ctx.strokeStyle = `rgba(237,125,43,${a})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
        ctx.fillStyle = "rgba(242,147,63,.9)";
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(draw);
    };

    const start = () => { conf(); cancelAnimationFrame(raf); draw(); };
    window.addEventListener("resize", start);
    window.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      mouse.x = e.clientX - r.left;
      mouse.y = e.clientY - r.top;
    });
    window.addEventListener("pointerleave", () => { mouse.x = mouse.y = -999; });
    // pause when hero offscreen
    const heroIO = new IntersectionObserver((es) => {
      es.forEach((e) => {
        if (e.isIntersecting) { if (!raf) draw(); }
        else { cancelAnimationFrame(raf); raf = null; }
      });
    }, { threshold: 0 });
    heroIO.observe(canvas);
    start();
  }
})();
