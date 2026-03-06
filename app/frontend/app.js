async function getJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Request failed: ${url}`);
  return await r.json();
}

function fmt(v) {
  return v === null || v === undefined ? '-' : v;
}

function fillTable(tableId, rows, mapRow) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = mapRow(r);
    tbody.appendChild(tr);
  });
}

async function refreshAll() {
  try {
    const [health, metrics, observations, anomalies, summary, advice] = await Promise.all([
      getJson('/health'),
      getJson('/metrics'),
      getJson('/observations?limit=10'),
      getJson('/anomalies?limit=10'),
      getJson('/report/summary'),
      getJson('/report/advice')
    ]);

    document.getElementById('totalObs').textContent = fmt(summary.total_observations);
    document.getElementById('anomalyCount').textContent = fmt(summary.anomalies);
    document.getElementById('anomalyRatio').textContent = `${(summary.anomaly_ratio * 100).toFixed(2)}%`;
    document.getElementById('queueLength').textContent = fmt(health.queue_length);

    document.getElementById('summaryBox').textContent = JSON.stringify(summary, null, 2);
    document.getElementById('metricsBox').textContent = JSON.stringify(metrics, null, 2);
    document.getElementById('adviceBox').textContent = JSON.stringify(advice, null, 2);

    fillTable('obsTable', observations, (r) => `
      <td>${fmt(r.observed_at)}</td>
      <td>${fmt(r.source)}</td>
      <td>${fmt(r.temperature)}</td>
      <td>${fmt(r.humidity)}</td>
      <td>${fmt(r.pm10)}</td>
      <td>${fmt(r.aqi)}</td>
      <td><span class="badge ${r.is_anomaly ? 'alert' : 'ok'}">${r.is_anomaly ? 'ANOMALY' : 'NORMAL'}</span></td>
    `);

    fillTable('anomalyTable', anomalies, (r) => `
      <td>${fmt(r.observed_at)}</td>
      <td>${fmt(r.source)}</td>
      <td>${fmt(r.anomaly_score)}</td>
      <td>${fmt(r.temperature)}</td>
      <td>${fmt(r.pm10)}</td>
      <td>${fmt(r.aqi)}</td>
    `);

    document.getElementById('lastUpdated').textContent = `Last updated: ${new Date().toLocaleString()}`;
  } catch (e) {
    document.getElementById('summaryBox').textContent = `Failed to load dashboard data. ${e.message}`;
    document.getElementById('adviceBox').textContent = `Failed to load AI advice. ${e.message}`;
  }
}

document.getElementById('refreshBtn').addEventListener('click', refreshAll);
refreshAll();
setInterval(refreshAll, 15000);
