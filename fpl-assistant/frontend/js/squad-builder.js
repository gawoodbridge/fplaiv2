const POSITION_CAPS = { GKP: 2, DEF: 5, MID: 5, FWD: 3 };
const BUDGET = 100.0;
const MAX_PER_TEAM = 3;

let squad = { GKP: [], DEF: [], MID: [], FWD: [] };
let formation = '4-4-2';
let captainId = null;
let viceCaptainId = null;
let allPlayersById = new Map();
let currentSquadId = null;

function allSquadPlayers() {
  return [...squad.GKP, ...squad.DEF, ...squad.MID, ...squad.FWD];
}

function formationCounts() {
  const [d, m, f] = formation.split('-').map(Number);
  return { GKP: 1, DEF: d, MID: m, FWD: f };
}

function totalCost() {
  return allSquadPlayers().reduce((sum, p) => sum + p.nowCost, 0);
}

function teamCounts() {
  const counts = {};
  allSquadPlayers().forEach((p) => { counts[p.team] = (counts[p.team] || 0) + 1; });
  return counts;
}

function canAdd(player) {
  if (allSquadPlayers().some((p) => p.id === player.id)) return 'Already in your squad';
  if (squad[player.position].length >= POSITION_CAPS[player.position]) {
    return `You already have the max ${POSITION_CAPS[player.position]} ${player.position}s`;
  }
  const teams = teamCounts();
  if ((teams[player.team] || 0) >= MAX_PER_TEAM) return `Max ${MAX_PER_TEAM} players from ${player.teamName}`;
  if (totalCost() + player.nowCost > BUDGET) return 'Not enough budget remaining';
  return null;
}

function addPlayer(player) {
  const problem = canAdd(player);
  if (problem) { toast(problem, 'error'); return; }
  squad[player.position].push(player);
  render();
}

function removePlayer(id) {
  for (const pos of Object.keys(squad)) {
    squad[pos] = squad[pos].filter((p) => p.id !== id);
  }
  if (captainId === id) captainId = null;
  if (viceCaptainId === id) viceCaptainId = null;
  render();
}

function chipHtml(player, { isCaptain = false, isVice = false } = {}) {
  if (!player) {
    return `<div class="player-chip empty"><div class="shirt">&nbsp;</div><div class="name">Empty</div></div>`;
  }
  return `
    <div class="player-chip" data-id="${player.id}" title="Click to view options">
      <div class="shirt">${fmt.initials(player.webName)}</div>
      ${isCaptain ? '<div class="cap-badge">C</div>' : isVice ? '<div class="cap-badge" style="background:var(--blue);color:#fff;">V</div>' : ''}
      <div class="name">${player.webName}</div>
      <div class="cost">${fmt.money(player.nowCost)}</div>
    </div>`;
}

function render() {
  const counts = formationCounts();

  const startingByPos = { GKP: squad.GKP.slice(0, 1), DEF: squad.DEF.slice(0, counts.DEF), MID: squad.MID.slice(0, counts.MID), FWD: squad.FWD.slice(0, counts.FWD) };
  const benchByPos = { GKP: squad.GKP.slice(1), DEF: squad.DEF.slice(counts.DEF), MID: squad.MID.slice(counts.MID), FWD: squad.FWD.slice(counts.FWD) };

  const rowHtml = (pos, list, need) => {
    const chips = list.map((p) => chipHtml(p, { isCaptain: p.id === captainId, isVice: p.id === viceCaptainId }));
    while (chips.length < need) chips.push(chipHtml(null));
    return chips.join('');
  };

  document.getElementById('row-fwd').innerHTML = rowHtml('FWD', startingByPos.FWD, counts.FWD);
  document.getElementById('row-mid').innerHTML = rowHtml('MID', startingByPos.MID, counts.MID);
  document.getElementById('row-def').innerHTML = rowHtml('DEF', startingByPos.DEF, counts.DEF);
  document.getElementById('row-gkp').innerHTML = rowHtml('GKP', startingByPos.GKP, 1);

  const bench = [...benchByPos.GKP, ...benchByPos.DEF, ...benchByPos.MID, ...benchByPos.FWD];
  document.getElementById('bench-row').innerHTML = bench.length
    ? bench.map((p) => chipHtml(p)).join('')
    : `<div class="sub" style="width:100%;text-align:center;">Bench players will appear here</div>`;

  document.querySelectorAll('.player-chip[data-id]').forEach((el) => {
    el.addEventListener('click', () => openPlayerMenu(Number(el.dataset.id)));
  });

  const cost = totalCost();
  document.getElementById('budget-label').textContent = `${fmt.money(cost)} / ${fmt.money(BUDGET)}`;
  const fillPct = Math.min(100, (cost / BUDGET) * 100);
  const fillEl = document.getElementById('budget-fill');
  fillEl.style.width = `${fillPct}%`;
  fillEl.classList.toggle('over', cost > BUDGET);

  const warnings = [];
  const total = allSquadPlayers().length;
  if (total < 15) warnings.push(`${15 - total} slot${15 - total > 1 ? 's' : ''} still open`);
  document.getElementById('rule-warnings').textContent = warnings.join(' &middot; ').replace('&middot;', '·');

  updateRating();
}

function openPlayerMenu(playerId) {
  const player = allSquadPlayers().find((p) => p.id === playerId);
  if (!player) return;
  const action = prompt(
    `${player.webName}\nType: "captain", "vice", or "remove"`,
    ''
  );
  if (!action) return;
  const val = action.trim().toLowerCase();
  if (val === 'captain') { captainId = playerId; if (viceCaptainId === playerId) viceCaptainId = null; render(); }
  else if (val === 'vice') { viceCaptainId = playerId; if (captainId === playerId) captainId = null; render(); }
  else if (val === 'remove') removePlayer(playerId);
}

async function updateRating() {
  const ids = allSquadPlayers().map((p) => p.id);
  const ratingEl = document.getElementById('rating-value');
  if (!ids.length) { ratingEl.textContent = '&mdash;'; return; }
  try {
    const res = await Api.rateSquad(ids);
    ratingEl.textContent = `${res.rating} / 100`;
    if (res.ruleViolations.length) {
      document.getElementById('rule-warnings').textContent = res.ruleViolations.join(' · ');
    }
  } catch (_) { /* rating is best-effort */ }
}

async function runOptimiser() {
  const btn = document.getElementById('optimise-btn');
  btn.disabled = true;
  btn.textContent = 'Optimising…';
  try {
    const requiredPlayerIds = allSquadPlayers().map((p) => p.id);
    const result = await Api.optimiseSquad({ budget: BUDGET, requiredPlayerIds });
    squad = { GKP: [], DEF: [], MID: [], FWD: [] };
    result.squad.forEach((p) => squad[p.position].push(p));
    formation = result.formation;
    captainId = result.captainId;
    viceCaptainId = result.viceCaptainId;
    document.querySelectorAll('.pill').forEach((p) => p.classList.toggle('active', p.dataset.formation === formation));
    render();
    toast(`Squad optimised — projected score ${result.projectedScore}`, 'success');
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '✨ AI-optimise squad';
  }
}

async function saveSquad() {
  const total = allSquadPlayers().length;
  if (total === 0) { toast('Add at least one player before saving', 'error'); return; }
  const payload = {
    name: document.getElementById('squad-name').value.trim() || 'My Squad',
    formation,
    budget: BUDGET,
    playerIds: allSquadPlayers().map((p) => p.id),
    captainId,
    viceCaptainId,
  };
  try {
    if (currentSquadId) {
      await Api.updateSquad(currentSquadId, payload);
    } else {
      const res = await Api.createSquad(payload);
      currentSquadId = res.squad.id;
    }
    toast('Squad saved', 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function loadExistingSquad() {
  const params = new URLSearchParams(window.location.search);
  const squadId = params.get('squadId');
  if (!squadId) return;
  try {
    const { squads } = await Api.mySquads();
    const found = squads.find((s) => String(s.id) === squadId);
    if (!found) return;
    currentSquadId = found.id;
    document.getElementById('squad-name').value = found.name;
    formation = found.formation;
    captainId = found.captainId;
    viceCaptainId = found.viceCaptainId;
    document.querySelectorAll('.pill').forEach((p) => p.classList.toggle('active', p.dataset.formation === formation));
    found.playerIds.forEach((id) => {
      const p = allPlayersById.get(id);
      if (p) squad[p.position].push(p);
    });
    render();
  } catch (err) {
    toast(err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  Auth.requireAuth();
  renderNav('builder');

  try {
    const { players } = await Api.players({ limit: 700 });
    allPlayersById = new Map(players.map((p) => [p.id, p]));
  } catch (err) {
    toast(err.message, 'error');
  }

  document.getElementById('formation-pills').addEventListener('click', (e) => {
    const pill = e.target.closest('.pill');
    if (!pill) return;
    document.querySelectorAll('.pill').forEach((p) => p.classList.remove('active'));
    pill.classList.add('active');
    formation = pill.dataset.formation;
    render();
  });

  document.getElementById('optimise-btn').addEventListener('click', runOptimiser);
  document.getElementById('save-squad-btn').addEventListener('click', saveSquad);

  const addSearch = document.getElementById('add-search');
  const addResults = document.getElementById('add-results');
  let debounceTimer = null;
  addSearch.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const q = addSearch.value.trim();
      if (!q) { addResults.innerHTML = ''; return; }
      try {
        const { players } = await Api.players({ search: q, limit: 8 });
        addResults.innerHTML = players.map((p) => `
          <div class="watchlist-card" style="background:var(--panel-raised);border-radius:8px;padding:8px 10px;cursor:pointer;" data-id="${p.id}">
            <div>
              <div style="font-weight:600;font-size:13px;">${p.webName} <span class="${fmt.posBadgeClass(p.position)}">${p.position}</span></div>
              <div class="sub">${p.teamShort} · ${fmt.money(p.nowCost)}</div>
            </div>
            <span class="btn btn-sm">Add</span>
          </div>
        `).join('') || `<div class="sub" style="padding:8px;">No players found.</div>`;

        addResults.querySelectorAll('[data-id]').forEach((el) => {
          el.addEventListener('click', () => {
            const player = allPlayersById.get(Number(el.dataset.id));
            if (player) addPlayer(player);
          });
        });
      } catch (err) {
        toast(err.message, 'error');
      }
    }, 250);
  });

  await loadExistingSquad();
  render();
});
