'use strict';
const $ = (id) => document.getElementById(id);
let result = null,
  live = false,
  busy = false;
const money = (v) => new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0
}).format(v);
const number = (v) => new Intl.NumberFormat('en-IN', {
  maximumFractionDigits: 0
}).format(v);
const pct = (v) => `${(v*100).toFixed(1)}%`;
const keys = ['demand_mean', 'demand_cv', 'price', 'cost', 'salvage', 'shortage_penalty', 'disruption_probability', 'disrupted_fill', 'demand_supply_correlation', 'risk_weight', 'baseline_order'];
const setStatus = (text, error = false) => {
  $('status').textContent = text;
  $('status').classList.toggle('error', error);
};

function labels() {
  $('cv-label').textContent = pct(+$('demand_cv').value);
  $('disruption-label').textContent = pct(+$('disruption_probability').value);
  $('risk-label').textContent = pct(+$('risk_weight').value);
}

function config() {
  const s = Object.fromEntries(keys.map(k => [k, +$(k).value]));
  s.order_min = Math.round(s.demand_mean * .4);
  s.order_step = Math.max(1, Math.round(s.demand_mean * .025));
  s.order_max = s.order_min + 56 * s.order_step;
  return {
    scenario: s,
    n: +$('n').value,
    method: $('method').value,
    seed: +$('seed').value,
    replicates: 12
  };
}
const svg = (content, width = 680, height = 240) => `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${content}</svg>`;

function frontierChart(r) {
  const rows = r.frontier,
    w = Math.max(280, $('frontier').clientWidth || 680),
    h = Math.max(180, $('frontier').clientHeight || 240),
    L = 52,
    R = 17,
    T = 15,
    B = 30;
  let min = Math.min(...rows.map(x => x.score), ...rows.map(x => x.mean_profit));
  let max = Math.max(...rows.map(x => x.mean_profit));
  const pad = (max - min) * .1 || 1;
  min -= pad;
  max += pad;
  const orderSpan = rows.at(-1).order - rows[0].order || 1;
  const x = (v) => L + (v - rows[0].order) / orderSpan * (w - L - R);
  const y = (v) => h - B - (v - min) / (max - min) * (h - T - B);
  let out = '';
  for (let i = 0; i < 5; i++) {
    const v = min + i * (max - min) / 4;
    out += `<line x1="${L}" y1="${y(v)}" x2="${w-R}" y2="${y(v)}" stroke="#e9eee7" stroke-dasharray="3 4"/><text x="${L-9}" y="${y(v)+3}" text-anchor="end" fill="#89998a" font-size="11">${(v/1000).toFixed(0)}k</text>`;
  }
  for (let i = 0; i < 5; i++) {
    const q = rows[Math.round(i * (rows.length - 1) / 4)].order;
    out += `<text x="${x(q)}" y="${h-7}" text-anchor="middle" fill="#89998a" font-size="11">${number(q)}</text>`;
  }
  out += '<text x="9" y="12" fill="#89998a" font-size="11">₹</text>';
  for (const [key, color] of [
      ['mean_profit', '#087f73'],
      ['score', '#b78c44']
    ]) {
    out += `<polyline points="${rows.map(row=>`${x(row.order)},${y(row[key])}`).join(' ')}" fill="none" stroke="${color}" stroke-width="2.4"/>`;
    for (const row of rows) {
      out += `<circle cx="${x(row.order)}" cy="${y(row[key])}" r="2.5" fill="${color}"><title>${number(row.order)} units · ${key==='score'?'Score':'Mean profit'} ${money(row[key])}</title></circle>`;
    }
  }
  const q = r.selected.order;
  out += `<line x1="${x(q)}" y1="${T}" x2="${x(q)}" y2="${h-B}" stroke="#709987" stroke-dasharray="4 5"/><rect x="${Math.min(w-108,Math.max(L,x(q)-42))}" y="0" width="86" height="20" rx="4" fill="#edf4e9"/><text x="${Math.min(w-65,Math.max(L+43,x(q)+1))}" y="13" text-anchor="middle" fill="#376d51" font-size="11">Selected ${q}</text>`;
  $('frontier').innerHTML = svg(out, w, h);
}

function histogram(r) {
  const {
    counts,
    edges
  } = r.histogram, w = Math.max(280, $('histogram').clientWidth || 480), h = Math.max(160, $('histogram').clientHeight || 180), L = 44, R = 18, T = 12, B = 28, max = Math.max(...counts) * 1.1;
  const x = (i) => L + i / counts.length * (w - L - R);
  const y = v => h - B - v / max * (h - T - B);
  const bar = (w - L - R) / counts.length;
  let out = '';
  for (let i = 0; i < 4; i++) {
    const v = max * i / 3;
    out += `<line x1="${L}" y1="${y(v)}" x2="${w-R}" y2="${y(v)}" stroke="#edf1e8"/><text x="${L-7}" y="${y(v)+3}" text-anchor="end" font-size="10" fill="#8b998b">${number(v)}</text>`;
  }
  counts.forEach((c, i) => {
    out += `<rect x="${x(i)+1}" y="${y(c)}" width="${Math.max(1,bar-2)}" height="${h-B-y(c)}" rx="1.5" fill="${(edges[i]+edges[i+1])/2<0?'#cf755f':'#7da695'}"><title>${money(edges[i])} to ${money(edges[i+1])}: ${c} worlds</title></rect>`;
  });
  for (let i = 0; i < 4; i++) {
    const index = Math.round(i * counts.length / 3);
    out += `<text x="${x(index)}" y="${h-7}" text-anchor="middle" font-size="10" fill="#8b998b">${(edges[index]/1000).toFixed(0)}k</text>`;
  }
  $('histogram').innerHTML = svg(out, w, h);
}

function render(r) {
  result = r;
  const s = r.selected,
    b = r.baseline,
    ci = r.mean_profit_ci95,
    d = r.paired_delta_ci95;
  $('order').textContent = number(s.order);
  $('order-change').textContent = `${s.order-b.order>=0?'+':''}${number(s.order-b.order)} units vs. baseline`;
  $('profit').textContent = money(s.mean_profit);
  $('profit-ci').textContent = `95% CI: ${money(ci.low)} – ${money(ci.high)}`;
  $('tail').textContent = money(s.tail_profit);
  $('fill').textContent = pct(s.fill_rate);
  $('stockout').textContent = `Stockout chance: ${pct(s.stockout_probability)}`;
  $('delta').textContent = (d.estimate >= 0 ? '+' : '') + money(d.estimate);
  $('delta-ci').textContent = `Paired 95% CI: ${money(d.low)} to ${money(d.high)}`;
  $('brief-title').textContent = d.low > 0 ? 'A stronger average outcome.' : d.high < 0 ? 'Lower average profit; inspect the trade-off.' : 'The average-profit difference is uncertain.';
  $('brief-text').textContent = `Order ${number(s.order)} units under these assumptions. The worst 5% average profit is ${money(s.tail_profit)}, compared with ${money(b.tail_profit)} for the baseline.`;
  $('comparison').replaceChildren();
  for (const [label, row] of [
      ['Selected policy', s],
      ['Baseline', b]
    ]) {
    const tr = document.createElement('tr');
    for (const value of [label, number(row.order), money(row.mean_profit), money(row.tail_profit), pct(row.loss_probability), pct(row.fill_rate)]) {
      const td = document.createElement('td');
      td.textContent = value;
      tr.append(td);
    }
    $('comparison').append(tr);
  }
  frontierChart(r);
  histogram(r);
  $('audit').textContent = `CONFIG ${r.config_id} · ${r.config.method.toUpperCase()} · ${number(r.selection_paths)} selection worlds · ${number(r.evaluation_paths)} evaluation worlds · ${r.candidate_count} candidate orders · seed ${r.config.seed} · ${r.elapsed_seconds}s\n${r.warnings.join(' ')}`;
  $('export-json').disabled = false;
  $('export-csv').disabled = false;
}
async function simulate(event) {
  if (event) event.preventDefault();
  if (busy || !live) return;
  busy = true;
  $('fields').disabled = true;
  $('run-button').textContent = 'Simulating…';
  setStatus('Selecting a policy, then evaluating it on independent worlds…');
  try {
    const response = await fetch('/api/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config())
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Simulation failed');
    render(data);
    setStatus(`✓ Simulation complete · ${number(data.evaluation_paths)} held-out worlds across ${data.config.replicates} independent replicates`);
  } catch (e) {
    setStatus(`Could not run: ${e.message}. Previous results remain unchanged.`, true);
  } finally {
    busy = false;
    $('fields').disabled = false;
    $('run-button').textContent = 'Run simulation ↗';
  }
}

function download(content, name, type) {
  const url = URL.createObjectURL(new Blob([content], {
    type
  }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('export-json').addEventListener('click', () => {
  if (result) download(JSON.stringify(result, null, 2), `stocksense-${result.config_id}.json`, 'application/json');
});
$('export-csv').addEventListener('click', () => {
  if (!result) return;
  const fields = ['order', 'mean_profit', 'tail_profit', 'loss_probability', 'fill_rate'];
  const rows = [
    ['policy', ...fields],
    ['selected', ...fields.map(k => result.selected[k])],
    ['baseline', ...fields.map(k => result.baseline[k])]
  ];
  download(rows.map(row => row.join(',')).join('\n'), `comparison-${result.config_id}.csv`, 'text/csv');
});
$('config-form').addEventListener('submit', simulate);
$('config-form').addEventListener('input', () => {
  labels();
  if (!busy) setStatus('Inputs changed · run the simulation to update the results.');
});
$('preset').addEventListener('change', () => {
  const presets = {
    balanced: {
      demand_mean: 1000,
      demand_cv: .35,
      disruption_probability: .08,
      risk_weight: .2,
      demand_supply_correlation: .25
    },
    volatile: {
      demand_mean: 1400,
      demand_cv: .65,
      disruption_probability: .08,
      risk_weight: .25,
      demand_supply_correlation: .25
    },
    fragile: {
      demand_mean: 1000,
      demand_cv: .4,
      disruption_probability: .25,
      risk_weight: .35,
      demand_supply_correlation: .65
    }
  };
  for (const [k, v] of Object.entries(presets[$('preset').value])) $(k).value = v;
  labels();
  setStatus('Scenario changed · run the simulation to update the results.');
});
async function history() {
  const rows = $('history-rows');
  rows.replaceChildren();
  if (!live) {
    $('history-note').textContent = 'Experiment history is available when running the Python server locally.';
    return;
  }
  try {
    const response = await fetch('/api/history');
    if (!response.ok) throw new Error('Could not load history');
    const runs = await response.json();
    for (const r of runs) {
      const tr = document.createElement('tr');
      for (const v of [r.id, r.created_at.slice(0, 19).replace('T', ' '), r.config_id, r.method, number(r.selected_order), money(r.mean_profit)]) {
        const td = document.createElement('td');
        td.textContent = v;
        tr.append(td);
      }
      rows.append(tr);
    }
    $('history-note').textContent = runs.length ? 'Latest 20 local runs. Full configuration and results are retained in SQLite.' : 'No local runs yet. Run a simulation from the overview.';
  } catch (e) {
    $('history-note').textContent = e.message;
  }
}

function showView() {
  const name = ['overview', 'learn', 'history'].includes(location.hash.slice(1)) ? location.hash.slice(1) : 'overview';
  document.querySelectorAll('.view').forEach(el => el.hidden = el.id !== name);
  document.querySelectorAll('[data-view]').forEach(el => el.classList.toggle('active', el.dataset.view === name));
  if (name === 'history') history();
  if (name === 'overview') redrawCharts();
}
function redrawCharts() {
  if (result && !$('overview').hidden) {
    frontierChart(result);
    histogram(result);
  }
}
window.addEventListener('resize', redrawCharts);
window.addEventListener('hashchange', showView);
$('refresh-history').addEventListener('click', history);
async function boot() {
  labels();
  showView();
  try {
    const health = await fetch('/api/health');
    live = health.ok && (await health.json()).status === 'ok';
  } catch {
    live = false;
  }
  if (live) {
    $('mode').textContent = '● Live Python engine';
    await simulate();
  } else {
    $('mode').textContent = 'Saved experiment preview';
    $('fields').disabled = true;
    $('design-note').textContent = 'Read-only preview. Run python -m stocklab serve to change assumptions and simulate.';
    try {
      const response = await fetch('example.json');
      if (!response.ok) throw new Error('No saved experiment available');
      render(await response.json());
      setStatus('Saved experiment · start the Python server to run new scenarios.');
    } catch (e) {
      setStatus(e.message, true);
    }
  }
}
boot();
