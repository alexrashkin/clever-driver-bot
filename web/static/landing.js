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

    const x = rect.left - parentRect.left - (beRect.width + 12); // place "Be" 12px left of target text
    const y = rect.top - parentRect.top + (rect.height - beRect.height) / 2; // vertical centering
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


