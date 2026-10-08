/* Human-team connection counts are separate from the agent topology controls. */
(function () {
  const input = document.getElementById('delivery-people');
  if (!input) return;
  const svg = document.getElementById('delivery-team-svg');
  const output = document.getElementById('delivery-count');
  const ns = 'http://www.w3.org/2000/svg';
  function shape(tag, attributes) {
    const element = document.createElementNS(ns, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
  }
  function draw() {
    const n = Number(input.value), links = n * (n - 1) / 2;
    const points = Array.from({length: n}, (_, i) => {
      const angle = -Math.PI / 2 + i * 2 * Math.PI / n;
      return [150 + 80 * Math.cos(angle), 110 + 80 * Math.sin(angle)];
    });
    const group = document.createElementNS(ns, 'g');
    points.forEach(([x, y], i) => points.slice(i + 1).forEach(([bx, by]) => {
      group.append(shape('path', {d: `M${x} ${y}L${bx} ${by}`, fill: 'none', stroke: '#C6C6BF'}));
    }));
    points.forEach(([cx, cy]) => group.append(shape('circle', {cx, cy, r: 7, fill: '#0E1012'})));
    svg.replaceChildren(group);
    svg.setAttribute('aria-label', `${n} people with ${links} possible undirected pairwise connections`);
    output.textContent = `${n} people · ${links} possible pairwise ${links === 1 ? 'connection' : 'connections'}`;
  }
  input.addEventListener('input', draw);
  draw();
})();
