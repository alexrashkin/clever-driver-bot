// Animate floating "Be" between target words
(function() {
  const floating = document.getElementById('hero-be');
  if (!floating) return;

  const targets = Array.from(document.querySelectorAll('[data-hero-target]'));
  if (targets.length === 0) return;

  function moveTo(el) {
    // Align left edge of "Be" to left of target, vertically center to target baseline area
    const rect = el.getBoundingClientRect();
    const beRect = floating.getBoundingClientRect();
    const parent = el.offsetParent || document.body;
    const parentRect = parent.getBoundingClientRect();

    // Adaptive horizontal gap: tighter on small screens
    const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const gap = vw < 480 ? 8 : 12;

    const x = rect.left - parentRect.left - (beRect.width + gap);
    const y = rect.top - parentRect.top + Math.max(0, (rect.height - beRect.height) / 2);
    floating.style.transform = `translate(${x}px, ${y}px)`;
  }

  // initial position
  moveTo(targets[0]);

  let idx = 0;
  setInterval(() => {
    moveTo(targets[idx]);
    idx = (idx + 1) % targets.length;
  }, 1800);
})();


