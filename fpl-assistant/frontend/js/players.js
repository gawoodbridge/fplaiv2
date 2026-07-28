const COMPARE_KEY = 'fpl_compare_ids';

function getCompareIds() {
  return JSON.parse(sessionStorage.getItem(COMPARE_KEY) || '[]');
}
function setCompareIds(ids) {
  sessionStorage.setItem(COMPARE_KEY, JSON.stringify(ids));
}

document.addEventListener('DOMContentLoaded', async () => {
  Auth.requireAuth();
  renderNav('players');

  const searchInput = document.getElementById('search-input');
  const positionFilter = document.getElementById('position-filter');
  const teamFilter = document.getElementById('team-filter');
  const maxCostFilter = document.getElementById('max-cost-filter');
  const sortFilter = document.getElementById('sort-filter');
  const tbody = document.getElementById('players-body');
  const compareTray = document.getElementById('compare-tray');
  const compareCount = document.getElementById('compare-count');

  try {
    const { teams } = await Api.teams();
    teamFilter.innerHTML += teams.map((t) => `<option value="${t.id}">${t.name}</option>`).join('');
  } catch (_) { /* team filter is a nice-to-have, ignore failures */ }

  let debounceTimer = null;
  function scheduleLoad() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadPlayers, 250);
  }

  async function loadPlayers() {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:30px;"><div class="spinner" style="margin:0 auto;"></div></td></tr>`;
    try {
      const { players } = await Api.players({
        search: searchInput.value.trim(),
        position: positionFilter.value,
        team: teamFilter.value,
        maxCost: maxCostFilter.value,
        sortBy: sortFilter.value,
        order: 'desc',
        limit: 60,
      });
      renderRows(players);
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:30px;color:var(--danger);">${err.message}</td></tr>`;
    }
  }

  function renderRows(players) {
    const compareIds = getCompareIds();
    if (!players.length) {
      tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state"><div class="icon">&#128269;</div>No players match those filters.</div></td></tr>`;
      return;
    }
    tbody.innerHTML = players.map((p) => `
      <tr>
        <td><input type="checkbox" class="compare-check" data-id="${p.id}" ${compareIds.includes(p.id) ? 'checked' : ''}></td>
        <td>
          <div class="player-name">${p.webName}</div>
          <div class="player-meta">${p.statusLabel !== 'Available' ? `&#9888; ${p.statusLabel}` : ''}</div>
        </td>
        <td><span class="${fmt.posBadgeClass(p.position)}">${p.position}</span></td>
        <td>${p.teamShort}</td>
        <td>${fmt.money(p.nowCost)}</td>
        <td>${p.form}</td>
        <td>${p.totalPoints}</td>
        <td>${p.pointsPerGame}</td>
        <td>${p.selectedByPercent}%</td>
        <td><button class="btn btn-sm watch-btn" data-id="${p.id}">+ Watch</button></td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.compare-check').forEach((cb) => {
      cb.addEventListener('change', () => {
        let ids = getCompareIds();
        const id = Number(cb.dataset.id);
        if (cb.checked) {
          if (ids.length >= 5) { cb.checked = false; toast('You can compare up to 5 players at once', 'error'); return; }
          ids.push(id);
        } else {
          ids = ids.filter((i) => i !== id);
        }
        setCompareIds(ids);
        updateCompareTray();
      });
    });

    tbody.querySelectorAll('.watch-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          await Api.addWatchlist(Number(btn.dataset.id));
          toast('Added to watchlist', 'success');
        } catch (err) {
          toast(err.message, 'error');
        }
      });
    });
  }

  function updateCompareTray() {
    const ids = getCompareIds();
    if (ids.length >= 2) {
      compareTray.classList.remove('hidden');
      compareCount.textContent = `${ids.length} player${ids.length > 1 ? 's' : ''} selected`;
    } else {
      compareTray.classList.add('hidden');
    }
  }

  [searchInput].forEach((el) => el.addEventListener('input', scheduleLoad));
  [positionFilter, teamFilter, maxCostFilter, sortFilter].forEach((el) => el.addEventListener('change', loadPlayers));

  updateCompareTray();
  loadPlayers();
});
