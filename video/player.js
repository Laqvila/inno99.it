/* Player HLS di Inno99: carica hls.js solo quando si preme play. */
(function () {
  var HLS_SRC = "/lib/hls.light.min.js";

  function loadHls(cb) {
    if (window.Hls) return cb();
    var s = document.createElement("script");
    s.src = HLS_SRC;
    s.onload = function () { cb(); };
    s.onerror = function () { cb(new Error("hls.js non caricato")); };
    document.head.appendChild(s);
  }

  function start(box) {
    var v = box.querySelector("video");
    var src = box.getAttribute("data-hls");
    if (box.getAttribute("data-ready")) { v.play(); return; }
    box.setAttribute("data-ready", "1");
    box.classList.add("is-loading");

    function go() {
      box.classList.remove("is-loading");
      box.classList.add("is-playing");
      v.setAttribute("controls", "");
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    }
    function fail() {
      box.classList.remove("is-loading");
      box.classList.add("is-error");
    }

    if (v.canPlayType("application/vnd.apple.mpegurl")) {
      v.src = src;
      go();
      return;
    }
    loadHls(function (err) {
      if (err || !window.Hls || !window.Hls.isSupported()) return fail();
      var hls = new window.Hls({ enableWorker: false, capLevelToPlayerSize: true });
      hls.loadSource(src);
      hls.attachMedia(v);
      hls.on(window.Hls.Events.MANIFEST_PARSED, go);
      hls.on(window.Hls.Events.ERROR, function (e, d) {
        if (!d.fatal) return;
        if (d.type === window.Hls.ErrorTypes.NETWORK_ERROR) hls.startLoad();
        else if (d.type === window.Hls.ErrorTypes.MEDIA_ERROR) hls.recoverMediaError();
        else fail();
      });
    });
  }

  var boxes = document.querySelectorAll("[data-hls]");
  for (var i = 0; i < boxes.length; i++) {
    (function (box) {
      var btn = box.querySelector(".hls-play");
      if (btn) btn.addEventListener("click", function () { start(box); });
    })(boxes[i]);
  }
})();
