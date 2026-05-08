const state = { samples: [], config: {}, plot: { energy: [], sample: [], reference: [] } };
const $ = (id) => document.getElementById(id);
const EDGE_PRESETS = [
  ["V", "K", 5.465], ["Cr", "K", 5.989], ["Mn", "K", 6.539], ["Fe", "K", 7.112],
  ["Co", "K", 7.709], ["Ni", "K", 8.333], ["Cu", "K", 8.979], ["Zn", "K", 9.659], ["Se", "K", 12.658],
];

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function init() {
  const [config, samples, status, plot] = await Promise.all([api("/api/config"), api("/api/samples"), api("/api/status"), api("/api/plot")]);
  renderConfig(config); state.samples = samples; renderSamples(); renderStatus(status); state.plot = plot; drawPlot();
}

function renderConfig(config) {
  state.config = config;
  $("outputPath").value = config.output_path || "";
  $("repeatQueue").value = config.repeat_queue || 1;
  $("bothDirections").checked = !!config.both_directions;
  $("checkPitch").checked = !!config.check_pitch;
  $("acquisitionMode").value = config.acquisition_mode || "transmission";
  $("dataSource").textContent = config.data_source || "-";
  $("outputFormat").textContent = config.output_format || "-";
}

function collectConfig() {
  return {
    output_path: $("outputPath").value,
    repeat_queue: Number($("repeatQueue").value || 1),
    both_directions: $("bothDirections").checked,
    check_pitch: $("checkPitch").checked,
    acquisition_mode: $("acquisitionMode").value,
  };
}

function renderSamples() {
  const body = $("sampleRows"); body.innerHTML = "";
  state.samples.forEach((sample, index) => {
    const [element, edge] = parseElementEdge(sample.element_edge);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><input data-key="name" value="${esc(sample.name)}"></td>
      <td><input data-key="x" type="number" step="0.001" value="${sample.x}"></td>
      <td><input data-key="y" type="number" step="0.001" value="${sample.y}"></td>
      <td><select data-key="element">${EDGE_PRESETS.map(([el]) => `<option value="${el}"${el === element ? " selected" : ""}>${el}</option>`).join("")}</select></td>
      <td><select data-key="edge"><option value="K">K</option></select></td>
      <td><input data-key="edge_energy_kev" type="number" step="0.001" value="${sample.edge_energy_kev}"></td>
      <td><input data-key="acquisition_time_s" type="number" min="1" value="${sample.acquisition_time_s}"></td>
      <td><input data-key="npoints" type="number" min="10" value="${sample.npoints}"></td>
      <td><select data-key="mode"><option value="XANES"${sample.mode === "XANES" ? " selected" : ""}>XANES</option><option value="EXAFS"${sample.mode === "EXAFS" ? " selected" : ""}>EXAFS</option></select></td>
      <td><input data-key="repeat" type="number" min="1" value="${sample.repeat}"></td>
      <td><button class="remove" data-remove>&times;</button></td>`;
    row.querySelectorAll("input, select").forEach((control) => control.addEventListener("change", () => updateSample(index, row, control.dataset.key)));
    row.querySelector("[data-remove]").addEventListener("click", () => { state.samples.splice(index, 1); renderSamples(); });
    body.appendChild(row);
  });
}

function updateSample(index, row, changedKey) {
  const sample = { ...state.samples[index] };
  const element = row.querySelector('[data-key="element"]').value;
  const edge = "K";
  if (changedKey === "element") {
    const preset = EDGE_PRESETS.find(([el]) => el === element);
    if (preset) row.querySelector('[data-key="edge_energy_kev"]').value = preset[2];
  }
  row.querySelectorAll("input, select").forEach((control) => {
    const key = control.dataset.key;
    if (["x", "y", "edge_energy_kev", "acquisition_time_s"].includes(key)) sample[key] = Number(control.value || 0);
    else if (["npoints", "repeat"].includes(key)) sample[key] = parseInt(control.value || "1", 10);
    else if (key === "element" || key === "edge") sample.element_edge = `${element} ${edge}`;
    else sample[key] = control.value;
  });
  state.samples[index] = sample;
}

function renderStatus(status) {
  $("hardwareMode").textContent = status.hardware_mode || "dry-run";
  $("runState").textContent = status.state;
  $("activeSample").textContent = status.active_sample || "-";
  $("message").textContent = status.message || "";
  $("dataSource").textContent = status.data_source || state.config.data_source || "-";
  $("outputFormat").textContent = status.output_format || state.config.output_format || "-";
  $("startScan").disabled = !status.can_start;
}

function addSample() {
  const n = state.samples.length + 1;
  state.samples.push({ name: `Sample ${n}`, x: 0, y: 0, edge_energy_kev: 8.333, element_edge: "Ni K", acquisition_time_s: 30, npoints: 2000, mode: "XANES", repeat: 1 });
  renderSamples();
}

async function refresh() {
  const [status, plot] = await Promise.all([api("/api/status"), api("/api/plot")]);
  renderStatus(status); state.plot = plot; drawPlot();
}

function drawPlot() {
  $("pointCount").textContent = `${state.plot.energy.length} points`;
  const canvas = $("ratioPlot"), ctx = canvas.getContext("2d");
  const ratio = devicePixelRatio || 1, w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== Math.floor(w * ratio) || canvas.height !== Math.floor(h * ratio)) { canvas.width = Math.floor(w * ratio); canvas.height = Math.floor(h * ratio); }
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, w, h); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, w, h);
  const x = state.plot.energy, s = state.plot.sample, r = state.plot.reference;
  const left = 62, top = 22, right = 18, bottom = 42, pw = w - left - right, ph = h - top - bottom;
  ctx.strokeStyle = "#c9d1dc"; ctx.strokeRect(left, top, pw, ph);
  if (!x.length) { ctx.fillStyle = "#667085"; ctx.fillText("Start queue to plot -I0/I1 and -I2/I1", left + 12, top + 24); return; }
  const all = s.concat(r), minX = Math.min(...x), maxX = Math.max(...x), minY = Math.min(...all), maxY = Math.max(...all);
  drawSeries(ctx, x, s, minX, maxX, minY, maxY, left, top, pw, ph, "#1f6feb");
  drawSeries(ctx, x, r, minX, maxX, minY, maxY, left, top, pw, ph, "#2f8f6b");
  ctx.fillStyle = "#364154"; ctx.fillText("Sample -I0/I1", left + 12, top + 18); ctx.fillText("Reference -I2/I1", left + 130, top + 18);
}

function drawSeries(ctx, x, y, minX, maxX, minY, maxY, left, top, pw, ph, color) {
  const sx = maxX - minX || 1, sy = maxY - minY || 1;
  ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 2;
  y.forEach((v, i) => {
    const px = left + ((x[i] - minX) / sx) * pw, py = top + (1 - (v - minY) / sy) * ph;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  });
  ctx.stroke();
}

function parseElementEdge(value) { const parts = String(value || "Ni K").split(/\s+|_/); return [parts[0] || "Ni", parts[1] || "K"]; }
function esc(value) { return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;"); }

$("saveConfig").addEventListener("click", async () => renderConfig(await api("/api/config", { method: "PUT", body: JSON.stringify(collectConfig()) })));
$("saveSamples").addEventListener("click", async () => { state.samples = await api("/api/samples", { method: "PUT", body: JSON.stringify(state.samples) }); renderSamples(); });
$("addSample").addEventListener("click", addSample);
$("startScan").addEventListener("click", async () => renderStatus(await api("/api/scan/start", { method: "POST" })));
$("stopAll").addEventListener("click", async () => renderStatus(await api("/api/scan/stop-all", { method: "POST" })));
init(); setInterval(refresh, 600);
