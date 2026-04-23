// HNSW Graph Animation for Codebase Intelligence
(function() {
  const canvas = document.getElementById('hnsw-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, animFrame, phase = 0, t = 0;

  const CYAN   = { r: 84,  g: 214, b: 221 };
  const AMBER  = { r: 255, g: 196, b: 87  };
  const PURPLE = { r: 162, g: 130, b: 255 };
  const WHITE  = { r: 230, g: 235, b: 255 };

  function rgba(c, a) { return `rgba(${c.r},${c.g},${c.b},${a})`; }

  // Nodes: {x,y} normalized 0-1, layer 0=bottom/dense, 2=top/sparse
  const rawNodes = [
    // Layer 2 (entry points)
    { x: 0.50, y: 0.30, layer: 2 },
    { x: 0.72, y: 0.52, layer: 2 },
    { x: 0.30, y: 0.60, layer: 2 },

    // Layer 1
    { x: 0.38, y: 0.22, layer: 1 },
    { x: 0.62, y: 0.20, layer: 1 },
    { x: 0.80, y: 0.35, layer: 1 },
    { x: 0.85, y: 0.60, layer: 1 },
    { x: 0.65, y: 0.72, layer: 1 },
    { x: 0.42, y: 0.78, layer: 1 },
    { x: 0.20, y: 0.70, layer: 1 },
    { x: 0.18, y: 0.42, layer: 1 },
    { x: 0.32, y: 0.38, layer: 1 },

    // Layer 0 (dense)
    { x: 0.25, y: 0.18, layer: 0 },
    { x: 0.44, y: 0.12, layer: 0 },
    { x: 0.60, y: 0.10, layer: 0 },
    { x: 0.75, y: 0.18, layer: 0 },
    { x: 0.88, y: 0.28, layer: 0 },
    { x: 0.92, y: 0.48, layer: 0 },
    { x: 0.88, y: 0.72, layer: 0 },
    { x: 0.75, y: 0.82, layer: 0 },
    { x: 0.55, y: 0.88, layer: 0 },
    { x: 0.36, y: 0.88, layer: 0 },
    { x: 0.18, y: 0.80, layer: 0 },
    { x: 0.10, y: 0.60, layer: 0 },
    { x: 0.10, y: 0.38, layer: 0 },
    { x: 0.16, y: 0.24, layer: 0 },
    { x: 0.52, y: 0.50, layer: 0 },
    { x: 0.68, y: 0.58, layer: 0 },
    { x: 0.40, y: 0.48, layer: 0 },
  ];

  // Build edges: connect each node to 2-4 nearby nodes in same/lower layer
  function buildEdges(nodes) {
    const edges = [];
    const used = new Set();
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      // Connect to nearest 3 nodes
      const dists = nodes.map((b, j) => ({ j, d: Math.hypot(a.x - b.x, a.y - b.y) }))
        .filter(({j}) => j !== i)
        .sort((a, b) => a.d - b.d)
        .slice(0, 3);
      for (const {j} of dists) {
        const key = [Math.min(i,j), Math.max(i,j)].join('-');
        if (!used.has(key)) {
          used.add(key);
          edges.push([i, j]);
        }
      }
    }
    return edges;
  }

  // Animation sequence: entry → traverse layer2 → layer1 → layer0 → highlight results
  const sequence = [
    { type: 'idle',      dur: 60  },
    { type: 'query',     dur: 40  }, // query node fades in
    { type: 'traverse2', dur: 80  }, // traverse layer 2
    { type: 'traverse1', dur: 100 }, // traverse layer 1
    { type: 'traverse0', dur: 120 }, // traverse layer 0
    { type: 'result',    dur: 100 }, // highlight results
    { type: 'fadeout',   dur: 60  }, // fade query out
  ];

  const totalDur = sequence.reduce((s, p) => s + p.dur, 0);

  // Fixed query position
  const QUERY = { x: 0.58, y: 0.44 };

  // Traversal paths (indices into rawNodes)
  const path2 = [0, 1];
  const path1 = [0, 3, 4, 5, 11];
  const path0 = [0, 12, 26, 27, 28];
  const results = [26, 27, 28, 11, 3];

  let nodes, edges;

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    W = canvas.offsetWidth;
    H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);
    nodes = rawNodes.map(n => ({ ...n, px: n.x * W, py: n.y * H }));
    edges = buildEdges(nodes);
  }

  function getPhaseInfo(frame) {
    let f = frame % totalDur;
    let acc = 0;
    for (const p of sequence) {
      if (f < acc + p.dur) return { type: p.type, progress: (f - acc) / p.dur };
      acc += p.dur;
    }
    return { type: 'idle', progress: 0 };
  }

  function lerp(a, b, t) { return a + (b - a) * t; }
  function ease(t) { return t < 0.5 ? 2*t*t : -1+(4-2*t)*t; }

  function drawGlow(x, y, r, col, alpha) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
    g.addColorStop(0, rgba(col, alpha * 0.9));
    g.addColorStop(0.3, rgba(col, alpha * 0.3));
    g.addColorStop(1, rgba(col, 0));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r * 3, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawEdge(i, j, col, alpha, width = 0.5) {
    const a = nodes[i], b = nodes[j];
    ctx.beginPath();
    ctx.moveTo(a.px, a.py);
    ctx.lineTo(b.px, b.py);
    ctx.strokeStyle = rgba(col, alpha);
    ctx.lineWidth = width;
    ctx.stroke();
  }

  function drawNode(n, col, alpha, r) {
    ctx.beginPath();
    ctx.arc(n.px, n.py, r, 0, Math.PI * 2);
    ctx.fillStyle = rgba(col, alpha);
    ctx.fill();
  }

  function drawAnimEdge(i, j, progress, col, alpha) {
    const a = nodes[i], b = nodes[j];
    const tx = lerp(a.px, b.px, progress);
    const ty = lerp(a.py, b.py, progress);
    ctx.beginPath();
    ctx.moveTo(a.px, a.py);
    ctx.lineTo(tx, ty);
    ctx.strokeStyle = rgba(col, alpha);
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  function draw(frame) {
    ctx.clearRect(0, 0, W, H);

    const { type, progress } = getPhaseInfo(frame);
    const ep = ease(progress);

    // --- Base edges ---
    for (const [i, j] of edges) {
      const layerAvg = (rawNodes[i].layer + rawNodes[j].layer) / 2;
      const alpha = layerAvg === 2 ? 0.18 : layerAvg >= 1 ? 0.10 : 0.06;
      const col = layerAvg === 2 ? PURPLE : layerAvg >= 1 ? CYAN : WHITE;
      drawEdge(i, j, col, alpha, layerAvg === 2 ? 0.8 : 0.5);
    }

    // --- Base nodes ---
    for (const [idx, n] of nodes.entries()) {
      const col = n.layer === 2 ? PURPLE : n.layer === 1 ? CYAN : WHITE;
      const r = n.layer === 2 ? 4 : n.layer === 1 ? 2.5 : 1.8;
      const alpha = n.layer === 2 ? 0.7 : n.layer === 1 ? 0.45 : 0.25;
      drawGlow(n.px, n.py, r, col, alpha * 0.4);
      drawNode(n, col, alpha, r);
    }

    // --- Query node ---
    const qx = QUERY.x * W, qy = QUERY.y * H;
    let queryAlpha = 0;
    if (type === 'query') queryAlpha = ep;
    else if (['traverse2','traverse1','traverse0','result'].includes(type)) queryAlpha = 1;
    else if (type === 'fadeout') queryAlpha = 1 - ep;

    if (queryAlpha > 0) {
      drawGlow(qx, qy, 6, AMBER, queryAlpha * 0.8);
      ctx.beginPath();
      ctx.arc(qx, qy, 5, 0, Math.PI * 2);
      ctx.fillStyle = rgba(AMBER, queryAlpha);
      ctx.fill();
      // Label
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillStyle = rgba(AMBER, queryAlpha * 0.9);
      ctx.fillText('query', qx + 8, qy - 6);
    }

    // --- Traversal animations ---
    if (type === 'traverse2') {
      // Highlight layer 2 path
      const steps = path2.length - 1;
      const totalP = ep * steps;
      for (let s = 0; s < steps; s++) {
        const segP = Math.min(Math.max(totalP - s, 0), 1);
        if (segP > 0) {
          drawAnimEdge(path2[s], path2[s+1], segP, AMBER, 0.8);
          drawGlow(nodes[path2[s]].px, nodes[path2[s]].py, 5, AMBER, 0.5);
          ctx.beginPath(); ctx.arc(nodes[path2[s]].px, nodes[path2[s]].py, 5, 0, Math.PI*2);
          ctx.fillStyle = rgba(AMBER, 0.9); ctx.fill();
        }
      }
    }

    if (type === 'traverse1') {
      // Layer 2 stays lit
      for (const idx of path2) {
        drawGlow(nodes[idx].px, nodes[idx].py, 4, CYAN, 0.3);
      }
      const steps = path1.length - 1;
      const totalP = ep * steps;
      for (let s = 0; s < steps; s++) {
        const segP = Math.min(Math.max(totalP - s, 0), 1);
        if (segP > 0) {
          drawAnimEdge(path1[s], path1[s+1], segP, CYAN, 0.9);
          drawGlow(nodes[path1[s]].px, nodes[path1[s]].py, 4, CYAN, 0.6);
          ctx.beginPath(); ctx.arc(nodes[path1[s]].px, nodes[path1[s]].py, 4, 0, Math.PI*2);
          ctx.fillStyle = rgba(CYAN, 0.95); ctx.fill();
        }
      }
    }

    if (type === 'traverse0') {
      for (const idx of path1) {
        drawGlow(nodes[idx].px, nodes[idx].py, 3, CYAN, 0.25);
      }
      const steps = path0.length - 1;
      const totalP = ep * steps;
      for (let s = 0; s < steps; s++) {
        const segP = Math.min(Math.max(totalP - s, 0), 1);
        if (segP > 0) {
          drawAnimEdge(path0[s], path0[s+1], segP, WHITE, 0.9);
          drawGlow(nodes[path0[s]].px, nodes[path0[s]].py, 3.5, WHITE, 0.5);
          ctx.beginPath(); ctx.arc(nodes[path0[s]].px, nodes[path0[s]].py, 3.5, 0, Math.PI*2);
          ctx.fillStyle = rgba(WHITE, 0.9); ctx.fill();
        }
      }
    }

    if (type === 'result' || type === 'fadeout') {
      const fade = type === 'fadeout' ? 1 - ep : 1;
      for (const [rank, idx] of results.entries()) {
        const delay = rank * 0.15;
        const p = Math.min(Math.max((ep - delay) / (1 - delay * results.length * 0.05), 0), 1);
        const r = 5 + p * 3;
        drawGlow(nodes[idx].px, nodes[idx].py, r, CYAN, p * 0.8 * fade);
        ctx.beginPath(); ctx.arc(nodes[idx].px, nodes[idx].py, r * 0.6, 0, Math.PI*2);
        ctx.fillStyle = rgba(CYAN, p * fade);
        ctx.fill();
        // rank label
        if (p > 0.5) {
          ctx.font = '9px "JetBrains Mono", monospace';
          ctx.fillStyle = rgba(CYAN, p * fade * 0.85);
          ctx.fillText(`#${rank+1}`, nodes[idx].px + 7, nodes[idx].py - 7);
        }
      }
    }
  }

  let frame = 0;
  function tick() {
    draw(frame++);
    animFrame = requestAnimationFrame(tick);
  }

  window.addEventListener('resize', () => { resize(); });
  resize();
  tick();
})();
