/* Renders the sidebar (desktop), topbar + tabbar (mobile) into any page
   that includes a <div id="nav-root"></div>. Keeps navigation markup in
   one place instead of duplicated across every HTML file. */

const NAV_ITEMS = [
  { href: 'dashboard.html', label: 'Dashboard', icon: '&#9679;', key: 'dashboard' },
  { href: 'squad-builder.html', label: 'Squad Builder', icon: '&#9917;', key: 'builder' },
  { href: 'players.html', label: 'Player Search', icon: '&#128269;', key: 'players' },
  { href: 'compare.html', label: 'Compare', icon: '&#9878;', key: 'compare' },
  { href: 'watchlist.html', label: 'Watchlist', icon: '&#9733;', key: 'watchlist' },
];

function renderNav(activeKey) {
  const root = document.getElementById('nav-root');
  if (!root) return;
  const user = Auth.getUser() || { displayName: 'Manager', email: '' };

  const linksHtml = NAV_ITEMS.map((item) => `
    <a class="nav-link ${item.key === activeKey ? 'active' : ''}" href="${item.href}">
      <span class="dot"></span>${item.label}
    </a>`).join('');

  root.innerHTML = `
    <aside class="sidebar">
      <div class="logo"><div class="mark">FA</div><span>FPL Assistant</span></div>
      <div class="nav-group">
        <div class="nav-label">Manage</div>
        ${linksHtml}
      </div>
      <div class="sidebar-footer">
        <div class="user-chip">
          <div class="avatar">${fmt.initials(user.displayName)}</div>
          <div>
            <div class="name">${user.displayName}</div>
            <div class="email">${user.email}</div>
          </div>
        </div>
        <button class="btn btn-ghost btn-block" id="logout-btn" style="margin-top:8px;">Log out</button>
      </div>
    </aside>

    <div class="mobile-topbar">
      <div class="logo"><div class="mark">FA</div>FPL Assistant</div>
      <button class="btn btn-sm btn-ghost" id="logout-btn-mobile">Log out</button>
    </div>

    <nav class="mobile-tabbar">
      ${NAV_ITEMS.map((item) => `
        <a href="${item.href}" class="${item.key === activeKey ? 'active' : ''}">
          <span class="icon">${item.icon}</span>${item.label.split(' ')[0]}
        </a>`).join('')}
    </nav>
  `;

  const doLogout = () => { Auth.clear(); window.location.href = 'index.html'; };
  document.getElementById('logout-btn')?.addEventListener('click', doLogout);
  document.getElementById('logout-btn-mobile')?.addEventListener('click', doLogout);
}
