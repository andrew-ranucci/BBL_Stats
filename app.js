let players = [];
let teams = [];
let awards = [];

let playerSort = { key: null, dir: "desc" };
let teamSort = { key: null, dir: "desc" };

function isNumber(v) {
  return typeof v === "number" && !Number.isNaN(v);
}

function compare(a, b, dir) {
  if (a == null) a = "";
  if (b == null) b = "";

  if (isNumber(a) && isNumber(b)) {
    return dir === "asc" ? a - b : b - a;
  }

  const sa = String(a).toLowerCase();
  const sb = String(b).toLowerCase();
  if (sa < sb) return dir === "asc" ? -1 : 1;
  if (sa > sb) return dir === "asc" ? 1 : -1;
  return 0;
}

function sortData(data, sortState) {
  if (!sortState.key) return data;
  const { key, dir } = sortState;
  return [...data].sort((r1, r2) => compare(r1[key], r2[key], dir));
}

function toNumber(v) {
  if (v == null) return null;
  if (typeof v === "number") return Number.isNaN(v) ? null : v;

  const s = String(v).trim();
  if (!s) return null;

  const pct = s.endsWith("%");
  const num = parseFloat(pct ? s.slice(0, -1) : s);
  return Number.isNaN(num) ? null : num;
}

function fmtStat(key, value) {
  const isPct = String(key).includes("%");
  if (typeof value !== "number") return String(value ?? "");
  if (isPct) return value.toFixed(2) + "%";
  if (!Number.isInteger(value)) return value.toFixed(2);
  return String(value);
}

function getTopN(rows, statKey, n = 3) {
  const scored = [];

  for (const r of rows) {
    const val = toNumber(r[statKey]);
    if (val == null) continue;
    scored.push({ row: r, value: val });
  }

  scored.sort((a, b) => b.value - a.value);

  const seen = new Set();
  const out = [];
  for (const item of scored) {
    const name = String(item.row.Player ?? item.row.player ?? "").trim();
    if (!name || seen.has(name)) continue;
    seen.add(name);
    out.push(item);
    if (out.length >= n) break;
  }
  return out;
}

function renderLeaders() {
  const leadersEl = document.getElementById("leaders");
  leadersEl.innerHTML = "";

  const categories = [
    { key: "PPG", label: "Points Per Game" },
    { key: "RPG", label: "Rebounds Per Game" },
    { key: "APG", label: "Assists Per Game" },
    { key: "SPG", label: "Steals Per Game" },
    { key: "BPG", label: "Blocks Per Game" },
    { key: "3PM", label: "3s Made" },
    { key: "3PT%", label: "3PT%" },
    { key: "FG%", label: "FG%" }
  ];

  for (const c of categories) {
    const top = getTopN(players, c.key, 3);

    const card = document.createElement("div");
    card.className = "card";

    const rowsHtml = top.length
      ? top.map((item, idx) => {
          const name = item.row.Player ?? item.row.player ?? "Unknown";
          const team = item.row.Team ?? item.row.team ?? "";
          const valText = fmtStat(c.key, item.value);
          return `
            <div class="leader-row">
              <div class="leader-rank">${idx + 1}</div>
              <div class="leader-name">
                ${name} ${team ? `<span class="leader-team">${team}</span>` : ""}
              </div>
              <div class="leader-val">${valText}</div>
            </div>
          `;
        }).join("")
      : `<div class="leader-empty">No data</div>`;

    card.innerHTML = `
      <div class="label">${c.label}</div>
      <div class="leader-list">${rowsHtml}</div>
    `;

    leadersEl.appendChild(card);
  }
}

function renderMVPLadder(rows) {
  const el = document.getElementById("mvp-ladder");
  if (!el) return;

  const medal = (r) => (r === 1 ? "👑" : r === 2 ? "🥈" : "🥉");

  const data = [...rows]
    .filter(r => r.Rank != null)
    .sort((a, b) => Number(a.Rank) - Number(b.Rank))
    .slice(0, 3);

  el.innerHTML = data.map(r => {
    const rank = Number(r.Rank);
    const player = r.Player ?? "";
    const team = r.Team ?? "";
    return `
      <div class="mvp-card rank-${rank}">
        <div class="mvp-top">
          <div class="mvp-rank">#${rank}</div>
          <div class="mvp-emoji">${medal(rank)}</div>
        </div>
        <div class="mvp-player">${player}</div>
        <div class="mvp-team">${team}</div>
      </div>
    `;
  }).join("");
}

function makeTable(containerId, data, sortState, setSortState) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  if (!data.length) {
    container.textContent = "No data.";
    return;
  }

  const columns = Object.keys(data[0]);

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");

  for (const col of columns) {
    const th = document.createElement("th");
    const isSorted = sortState.key === col;
    const arrow = isSorted ? (sortState.dir === "asc" ? " ▲" : " ▼") : "";
    th.textContent = col + arrow;

    th.addEventListener("click", () => {
      const nextDir =
        sortState.key === col ? (sortState.dir === "asc" ? "desc" : "asc") : "desc";
      setSortState({ key: col, dir: nextDir });
    });

    trh.appendChild(th);
  }

  thead.appendChild(trh);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const row of data) {
    const tr = document.createElement("tr");
    for (const col of columns) {
      const td = document.createElement("td");
      const val = row[col];

      if (isNumber(val) && !Number.isInteger(val)) td.textContent = val.toFixed(2);
      else td.textContent = val ?? "";

      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }

  table.appendChild(tbody);
  container.appendChild(table);
}

function renderPlayers() {
  const q = document.getElementById("player-search").value.trim().toLowerCase();
  const filtered = q
    ? players.filter((p) => String(p.Player ?? "").toLowerCase().includes(q))
    : players;

  const sorted = sortData(filtered, playerSort);
  makeTable("players-table", sorted, playerSort, (s) => {
    playerSort = s;
    renderPlayers();
  });
}

function renderTeams() {
  const sorted = sortData(teams, teamSort);
  makeTable("teams-table", sorted, teamSort, (s) => {
    teamSort = s;
    renderTeams();
  });
}

async function main() {
  let v = Date.now();

  try {
    const u = await fetch("data/last_updated.json?v=" + Date.now());
    const uj = await u.json();
    v = encodeURIComponent(uj.last_updated ?? Date.now());
    document.getElementById("last-updated").textContent =
      `Last updated: ${uj.last_updated ?? "Unknown"}`;
  } catch {
    document.getElementById("last-updated").textContent = "Last updated: Unknown";
  }

  const p = await fetch(`data/season_stats.json?v=${v}`);
  players = await p.json();

  const t = await fetch(`data/team_stats.json?v=${v}`);
  teams = await t.json();

  try {
    const a = await fetch(`data/awards.json?v=${v}`);
    awards = await a.json();
    renderMVPLadder(awards);
  } catch {
    renderMVPLadder([]);
  }

  renderLeaders();

  document.getElementById("player-search").addEventListener("input", renderPlayers);
  renderPlayers();
  renderTeams();
}

main();