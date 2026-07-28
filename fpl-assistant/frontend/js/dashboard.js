document.addEventListener('DOMContentLoaded', async () => {
  Auth.requireAuth();
  renderNav('dashboard');

  const user = Auth.getUser();
  document.getElementById('dash-name').textContent = user?.displayName || 'Manager';

  const statGrid = document.getElementById('stat-grid');
  const squadList = document.getElementById('squad-list');
  const formList = document.getElementById('form-list');
  const fixturesBody = document.getElementById('fixtures-body');

  let squads = [];
  let watchlist = [];
  let topForm = [];

  try {
    [squads, watchlist, topForm] = await Promise.all([
      Api.mySquads().then((r) => r.squads),
      Api.watchlist().then((r) => r.items),
      Api.players({ sortBy: 'form', order: 'desc', limit: 6 }).then((r) => r.players),
    ]);
  } catch (err) {
    toast(err.message, 'error');
  }

  statGrid.innerHTML = `
    <div class="stat-card"><div class="label">Saved squads</div><div class="value">${squads.length}</div></div>
    <div class="stat-card"><div class="label">Watchlist players</div><div class="value">${watchlist.length}</div></div>
    <div class="stat-card"><div class="label">Top form player</div><div class="value" style="font-size:18px;">${topForm[0] ? topForm[0].webName : '&mdash;'}</div></div>
    <div class="stat-card"><div class="label">5-year points target</div><div class="value">2,350</div></div>
  `;

  squadList.innerHTML = squads.length
    ? squads.slice(0, 4).map((s) => `
        <div class="watchlist-card" style="background:var(--panel-raised);border-radius:10px;">
          <div>
            <div style="font-weight:700;">${s.name}</div>
            <div class="sub">${s.formation} &middot; ${fmt.money(s.budget)} budget &middot; ${s.playerIds.length}/15 players</div>
          </div>
          <a class="btn btn-sm" href="squad-builder.html?squadId=${s.id}">Open</a>
        </div>`).join('')
    : `<div class="empty-state" style="padding:24px;"><div class="icon">&#9917;</div>No squads yet &mdash; build your first one.</div>`;

  formList.innerHTML = topForm.length
    ? topForm.map((p) => `
        <div class="watchlist-card" style="background:var(--panel-raised);border-radius:10px;">
          <div>
            <div style="font-weight:700;">${p.webName} <span class="${fmt.posBadgeClass(p.position)}">${p.position}</span></div>
            <div class="sub">${p.teamShort} &middot; ${fmt.money(p.nowCost)}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-family:var(--font-display);font-weight:700;">${p.form}</div>
            <div class="sub">form</div>
          </div>
        </div>`).join('')
    : `<div class="empty-state" style="padding:24px;">Player data unavailable right now.</div>`;

  try {
    const { fixtures } = await Api.fixtures({ next: 8 });
    fixturesBody.innerHTML = fixtures.length
      ? fixtures.map((f) => `
          <tr>
            <td>GW ${f.event ?? '&mdash;'}</td>
            <td>${f.homeTeamShort}</td>
            <td><span class="${fmt.fdrBadgeClass(f.homeDifficulty)}">${f.homeDifficulty}</span></td>
            <td>${f.awayTeamShort}</td>
            <td><span class="${fmt.fdrBadgeClass(f.awayDifficulty)}">${f.awayDifficulty}</span></td>
            <td class="sub">${f.kickoffTime ? new Date(f.kickoffTime).toLocaleString() : 'TBC'}</td>
          </tr>`).join('')
      : `<tr><td colspan="6" style="text-align:center;padding:24px;">No upcoming fixtures found.</td></tr>`;
  } catch (err) {
    fixturesBody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--danger);">${err.message}</td></tr>`;
  }
});
