// Animate floating "Be" between target words
(function() {
  const floating = document.getElementById('hero-be');
  if (!floating) return;

  const targets = Array.from(document.querySelectorAll('[data-hero-target]'));
  if (targets.length === 0) return;

  function moveTo(el) {
    const rect = el.getBoundingClientRect();
    const parent = el.offsetParent || document.body;
    const parentRect = parent.getBoundingClientRect();
    const x = rect.left - parentRect.left;
    const y = rect.top - parentRect.top;
    floating.style.transform = `translate(${x}px, ${y}px)`;
  }

  // initial position
  moveTo(targets[0]);

  let idx = 1;
  setInterval(() => {
    moveTo(targets[idx]);
    idx = (idx + 1) % targets.length;
  }, 1800);
})();


