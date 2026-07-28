document.addEventListener('DOMContentLoaded', async () => {
  Auth.requireAuth();
  renderNav('watchlist');

  const content = document.getElementById('watchlist-content');

  async function load() {
    let items = [];
    try {
      items = (await Api.watchlist()).items;
    } catch (err) {
      content.innerHTML = `<div class="empty-state" style="color:var(--danger);">${err.message}</div>`;
      return;
    }

    if (!items.length) {
      content.innerHTML = `<div class="empty-state"><div class="icon">&#9733;</div>Your watchlist is empty. Add players from the search page.</div>`;
      return;
    }

    let players = [];
    try {
      const { players: allPlayers } = await Api.players({ limit: 700 });
      const byId = new Map(allPlayers.map((p) => [p.id, p]));
      players = items.map((i) => ({ ...i, player: byId.get(i.playerId) })).filter((i) => i.player);
    } catch (err) {
      content.innerHTML = `<div class="empty-state" style="color:var(--danger);">${err.message}</div>`;
      return;
    }

    content.innerHTML = players.map(({ player, playerId }) => `
      <div class="card watchlist-card">
        <div style="display:flex;align-items:center;gap:14px;">
          <div class="player-chip .shirt" style="width:40px;height:40px;border-radius:10px;background:var(--panel-raised);border:2px solid var(--amber);display:flex;align-items:center;justify-content:center;font-family:var(--font-display);font-weight:700;font-size:12px;">${fmt.initials(player.webName)}</div>
          <div>
            <div style="font-weight:700;">${player.webName} <span class="${fmt.posBadgeClass(player.position)}">${player.position}</span></div>
            <div class="sub">${player.teamName} &middot; ${fmt.money(player.nowCost)} &middot; Form ${player.form}</div>
          </div>
        </div>
        <button class="btn btn-sm btn-danger remove-btn" data-id="${playerId}">Remove</button>
      </div>
    `).join('');

    content.querySelectorAll('.remove-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          await Api.removeWatchlist(Number(btn.dataset.id));
          toast('Removed from watchlist', 'success');
          load();
        } catch (err) {
          toast(err.message, 'error');
        }
      });
    });
  }

  load();
});
