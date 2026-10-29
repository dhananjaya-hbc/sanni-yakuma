/* The masks' eyes follow the viewer: the mouse on a computer, the middle of the screen on a phone. */
(function () {
  var pupils = Array.prototype.slice.call(document.querySelectorAll(".pupil"));
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!pupils.length || still) return;
  var target = null, queued = false;
  function look() {
    queued = false;
    var tx = target ? target.x : window.innerWidth / 2;
    var ty = target ? target.y : window.innerHeight / 2;
    pupils.forEach(function (g) {
      var m = g.parentNode.getScreenCTM && g.parentNode.getScreenCTM();
      if (!m) return;
      var cx = +g.getAttribute("data-cx"), cy = +g.getAttribute("data-cy");
      var sx = m.a * cx + m.c * cy + m.e, sy = m.b * cx + m.d * cy + m.f;
      if (sy < -200 || sy > window.innerHeight + 200) return;  // off screen: let it rest
      var dx = tx - sx, dy = ty - sy, d = Math.sqrt(dx * dx + dy * dy) || 1;
      var reach = Math.min(4.5, d / 40);
      g.style.transform = "translate(" + (dx / d * reach).toFixed(2) + "px," + (dy / d * reach).toFixed(2) + "px)";
    });
  }
  function queue() { if (!queued) { queued = true; window.requestAnimationFrame(look); } }
  window.addEventListener("pointermove", function (e) {
    if (e.pointerType === "mouse") { target = { x: e.clientX, y: e.clientY }; queue(); }
  }, { passive: true });
  window.addEventListener("scroll", queue, { passive: true });
  window.addEventListener("resize", queue);
  queue();
})();
