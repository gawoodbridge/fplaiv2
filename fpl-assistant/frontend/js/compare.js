const COMPARE_STATS = [
  ['nowCost', 'Price', fmt.money],
  ['form', 'Form', (v) => v],
  ['totalPoints', 'Total points', (v) => v],
  ['pointsPerGame', 'Points / game', (v) => v],
  ['selectedByPercent', 'Ownership %', (v) => `${v}%`],
  ['goalsScored', 'Goals', (v) => v],
  ['assists', 'Assists', (v) => v],
  ['cleanSheets', 'Clean sheets', (v) => v],
  ['bonus', 'Bonus points', (v) => v],
  ['ictIndex', 'ICT index', (v) => v],
  ['minutes', 'Minutes played', (v) => v],
];

document.addEventListener('DOMContentLoaded', async () => {
  Auth.requireAuth();
  renderNav('compare');

  const content = document.getElementById('compare-content');
  const ids = JSON.parse(sessionStorage.getItem('fpl_compare_ids') || '[]');

  if (ids.length < 2) {
    content.innerHTML = `<div class="empty-state"><div class="icon">&#9878;</div>Select 2-5 players on the <a href="players.html">search page</a> to compare them here.</div>`;
    return;
  }

  content.innerHTML = `<div style="padding:40px;text-align:center;"><div class="spinner" style="margin:0 auto;"></div></div>`;

  let players = [];
  try {
    const res = await Api.comparePlayers(ids);
    players = res.players;
  } catch (err) {
    content.innerHTML = `<div class="empty-state" style="color:var(--danger);">${err.message}</div>`;
    return;
  }

  function bestValueClass(row, value) {
    const values = players.map((p) => p[row]);
    const max = Math.max(...values);
    return value === max && max > 0 ? 'style="color:var(--success);font-weight:700;"' : '';
  }

  content.innerHTML = `
    <div class="compare-grid" style="margin-bottom:24px;">
      ${players.map((p) => `
        <div class="card">
          <div class="${fmt.posBadgeClass(p.position)}" style="margin-bottom:8px;display:inline-flex;">${p.position}</div>
          <h3>${p.webName}</h3>
          <div class="sub">${p.teamName}</div>
          <div style="font-family:var(--font-display);font-size:24px;margin-top:10px;">${fmt.money(p.nowCost)}</div>
        </div>
      `).join('')}
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Stat</th>${players.map((p) => `<th>${p.webName}</th>`).join('')}</tr>
        </thead>
        <tbody>
          ${COMPARE_STATS.map(([key, label, format]) => `
            <tr>
              <td class="player-meta">${label}</td>
              ${players.map((p) => `<td ${bestValueClass(key, p[key])}>${format(p[key])}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
});
