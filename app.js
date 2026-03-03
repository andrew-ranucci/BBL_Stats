let players = [];
let teams = [];
let playerSort = { key: null, dir: "desc" };
let teamSort = { key: null, dir: "desc" };

function isNumber(v) {
  return typeof v === "number" && !Number.isNaN(v);
}

function compare(a, b, dir) {
  if (a == null) a = "";
  if (b == null) b = "";

  // numeric sort if both are numbers
  if (isNumber(a) && isNumber(b)) {
    return dir === "asc" ? a - b : b - a;
  }

  // otherwise string sort
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

/* --- League leaders helpers --- */
function toNumber(v) {
  if (v == null) return null;
  if (typeof v === "number") return Number.isNaN(v) ? null : v;

  // handle strings like "66.67%" or " 66.67 % "
  const s = String(v).trim();
  if (!s) return null;

  const pct = s.endsWith("%");
  const num = parseFloat(pct ? s.slice(0, -1) : s);
  return Number.isNaN(num) ? null : num;
}

function getLeader(rows, statKey) {
  let best = null;
  let bestVal = -Infinity;

  for (const r of rows) {
    const val = toNumber(r[statKey]);
    if (val == null) continue;
    if (val > bestVal) {
      bestVal = val;
      best = r;
    }
  }

  if (!best) return null;
  return { row: best, value: bestVal };
}

function fmtStat(key, value) {
  const isPct = String(key).includes("%");
  if (typeof value !== "number") return String(value ?? "");
  if (isPct) return value.toFixed(2) + "%";
  if (!Number.isInteger(value)) return value.toFixed(2);
  return String(value);
}

function renderLeaders() {
  const leadersEl = document.getElementById("leaders");
  leadersEl.innerHTML = "";

  // These keys MUST match your JSON column names exactly.
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
    const leader = getLeader(players, c.key);

    const card = document.createElement("div");
    card.className = "card";

    if (!leader) {
      card.innerHTML = `
        <div class="label">${c.label}</div>
        <div class="value">—</div>
        <div class="who">No data</div>
      `;
      leadersEl.appendChild(card);
      continue;
    }

    const name = leader.row.Player ?? leader.row.player ?? "Unknown";
    const team = leader.row.Team ?? leader.row.team ?? "";
    const valText = fmtStat(c.key, leader.value);

    card.innerHTML = `
      <div class="label">${c.label}</div>
      <div class="value">${valText}</div>
      <div class="who">
        ${name}
        ${team ? `<span class="team">(${team})</span>` : ""}
      </div>
      <div class="sub">Click table headers to sort</div>
    `;

    leadersEl.appendChild(card);
  }
}

/* --- Table rendering --- */
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

    // show sort indicator
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

      // pretty print floats
      if (isNumber(val) && !Number.isInteger(val)) {
        td.textContent = val.toFixed(2);
      } else {
        td.textContent = val ?? "";
      }

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

function renderMVP(data) {
  const container = document.getElementById("mvp-ladder");
  if (!container) return;

  container.innerHTML = data.map(row => `
    <div class="mvp-card rank-${row.Rank}">
      <div class="mvp-rank">#${row.Rank}</div>
      <div class="mvp-player">${row.Player}</div>
      <div class="mvp-team">${row.Team}</div>
    </div>
  `).join("");
}

async function main() {
    // last updated (cache-busted)
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

  // load data (cache-busted using v)
  const p = await fetch(`data/season_stats.json?v=${v}`);
  players = await p.json();

  const t = await fetch(`data/team_stats.json?v=${v}`);
  teams = await t.json();

  const a = await fetch(`data/awards.json?v=${v}`);
  const awards = await a.json();
  renderMVP(awards);

  // leaders + tables
  renderLeaders();

  document.getElementById("player-search").addEventListener("input", renderPlayers);
  renderPlayers();
  renderTeams();
}

main();