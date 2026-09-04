// Check and capture query params immediately before anything runs (OAuth Callback Safe)
const urlParams = new URLSearchParams(window.location.search);
const tokenFromUrl = urlParams.get("token");
const refreshFromUrl = urlParams.get("refresh");
const providerFromUrl = urlParams.get("provider") || urlParams.get("platform");

if (tokenFromUrl) {
    localStorage.setItem("access_token", tokenFromUrl);
    if (refreshFromUrl) {
        localStorage.setItem("refresh_token", refreshFromUrl);
    }
    if (providerFromUrl) {
        localStorage.setItem("active_platform", providerFromUrl);
        localStorage.setItem("login_provider", providerFromUrl);
    }
    // Clean URL query params without triggering page reload/flicker
    window.history.replaceState({}, document.title, window.location.pathname);
}

let organizations = [], currentOrg = null, postsCache = [];
let selectedSocialAccountIds = [];

// Helper to get organization ID
function orgId() {
    return localStorage.getItem('organization_id') || (currentOrg ? currentOrg.id : null);
}

// Escape HTML for XSS prevention
function esc(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Helper to get platform icons
function getPlatformIcon(provider = '') {
    const p = (provider || '').toLowerCase();
    if (p.includes('facebook')) return 'f';
    if (p.includes('instagram')) return '◎';
    if (p.includes('linkedin')) return 'in';
    if (p.includes('google') || p.includes('gmb')) return 'G';
    if (p.includes('threads')) return '@';
    return '●';
}

// Formats UTC/ISO date strings to exact IST display
function fmtDate(d){
    if(!d) return '—';
    try {
        let iso = typeof d === 'string' && !d.includes('Z') && !d.includes('+') ? d + 'Z' : d;
        let date = new Date(iso);
        if (isNaN(date.getTime())) date = new Date(d);
        
        return date.toLocaleString('en-IN', {
            timeZone: 'Asia/Kolkata',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    } catch(e) {
        return d;
    }
}

// Converts local datetime to UTC ISO
function istInputToUTCISOString(localValue){
    if(!localValue) return null;
    let value = localValue.length === 16 ? localValue + ':00' : localValue;
    const withOffset = `${value}+05:30`;
    const d = new Date(withOffset);
    if(isNaN(d.getTime())) return null;
    return d.toISOString();
}

// Converts UTC ISO to IST format for datetime-local input
function toLocalInputString(dateStr){
    if(!dateStr) return '';
    let iso = typeof dateStr === 'string' && !dateStr.includes('Z') && !dateStr.includes('+') ? dateStr + 'Z' : dateStr;
    const d = new Date(iso);
    if(isNaN(d.getTime())) return '';

    const parts = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    }).formatToParts(d).reduce((acc, p) => {
        acc[p.type] = p.value;
        return acc;
    }, {});

    return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

// Strict Master Admin Lock (Universal Protection)
function applyRoleBasedUI(user) {
    if (!user) return;
    try {
        const MASTER_ADMIN_EMAIL = "admin@smartautopost.com";
        const userEmail = (user.email || '').toLowerCase().trim();
        const isMasterAdmin = (userEmail === MASTER_ADMIN_EMAIL && user.role === 'admin');

        const adminRoutes = [
            'subscriptions', 'payments', 'invoices', 'refunds', 
            'coupons', 'usage', 'audit-logs', 'api-status', 
            'billing', 'plans', 'roles', 'clients', 'organizations'
        ];

        // 1. Sidebar ke links handle karo
        document.querySelectorAll('.sidebar a, nav a').forEach(link => {
            const href = (link.getAttribute('href') || '').toLowerCase();
            const isAdminLink = adminRoutes.some(route => href.includes(route));

            if (isAdminLink) {
                link.style.setProperty('display', isMasterAdmin ? 'flex' : 'none', 'important');
            } else {
                link.style.setProperty('display', 'flex', 'important');
            }
        });

        // 2. Data attributes check
        document.querySelectorAll('[data-admin-only="1"]').forEach(el => {
            el.style.setProperty('display', isMasterAdmin ? '' : 'none', 'important');
        });

        // 3. Admin Containers
        const adminBox = document.getElementById('adminFinanceContainer');
        if (adminBox) {
            adminBox.style.setProperty('display', isMasterAdmin ? 'block' : 'none', 'important');
        }

        // 4. Sidebar section labels
        document.querySelectorAll('.sidebar .nav-label, nav .nav-label, .sidebar p').forEach(label => {
            const text = label.textContent.toLowerCase();
            if (text.includes('finance') || text.includes('system') || text.includes('admin')) {
                label.style.setProperty('display', isMasterAdmin ? 'block' : 'none', 'important');
            } else {
                label.style.setProperty('display', 'block', 'important');
            }
        });

        // 5. Header Organization Dropdown
        const orgWrapper = document.getElementById('orgSelectWrapper') || document.querySelector('label[data-admin-only="1"]');
        if (orgWrapper) {
            orgWrapper.style.setProperty('display', isMasterAdmin ? 'inline-flex' : 'none', 'important');
        }
    } catch (err) {
        console.warn('Role UI error:', err);
    }
}

async function bootstrap(){
    const currentToken = typeof token === 'function' ? token() : localStorage.getItem('access_token');
    if(!currentToken){
        location.href = '/login';
        return;
    }
    try{
        const me = await api('/auth/me');
        localStorage.setItem('user', JSON.stringify(me));
        setUser(me);
        
        document.body.dataset.role = me.role || 'user';
        document.body.dataset.authProvider = me.auth_provider || 'email';
        
        applyRoleBasedUI(me);

        organizations = await api('/organizations/').catch(() => []);
        const sel = document.getElementById('organizationSelect');
        if(sel && organizations.length){
            sel.innerHTML = organizations.map(o => `<option value="${o.id}">${esc(o.name)}</option>`).join('');
            let saved = Number(localStorage.getItem('organization_id'));
            currentOrg = organizations.find(o => o.id === saved) || organizations[0];
            if(currentOrg){
                sel.value = currentOrg.id;
                localStorage.setItem('organization_id', currentOrg.id);
                const sbOrg = document.getElementById('sidebarOrg');
                if(sbOrg) sbOrg.textContent = currentOrg.name;
            }
            sel.onchange = () => {
                localStorage.setItem('organization_id', sel.value);
                location.reload();
            }
        }
        
        await loadPage();
        applyRoleBasedUI(me);
    } catch(e) {
        console.error("Bootstrap error:", e);
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

function setUser(u){
    if(!u) return;
    const initials = (u.name || u.email || 'U').split(/\s+/).map(x => x[0]).slice(0, 2).join('').toUpperCase();
    ['sidebarAvatar', 'profileAvatar'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.textContent = initials;
    });
    ['sidebarName', 'profileName'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.textContent = u.name || 'User';
    });
    const pe = document.getElementById('profileEmail');
    if(pe) pe.textContent = u.email || '';
    if(document.getElementById('profileNameInput')) profileNameInput.value = u.name || '';
    if(document.getElementById('profileEmailInput')) profileEmailInput.value = u.email || '';
}

async function loadPage(){
    const p = document.body.dataset.page;
    if(!p) return;
    const map = {
        dashboard: loadDashboard,
        posts: loadPosts,
        'create-post': loadCreatePost,
        'ai-content': () => {},
        calendar: loadCalendar,
        analytics: loadAnalytics,
        'social-accounts': loadAccounts,
        'media-library': loadMedia,
        competitors: loadCompetitors,
        clients: loadMembers,
        organizations: loadOrganizations,
        billing: loadBilling,
        notifications: loadNotifications,
        profile: () => {},
        settings: loadSettings,
        roles: loadRoles,
        'audit-logs': loadAuditLogs
    };
    if(map[p]) await map[p]();
}

async function loadDashboard(){
    if(!orgId()) return;
    try{
        const [s, r, a] = await Promise.all([
            api(`/dashboard/summary?organization_id=${orgId()}`).catch(() => ({})),
            api(`/dashboard/recent-posts?organization_id=${orgId()}&limit=5`).catch(() => []),
            api(`/social-accounts/?organization_id=${orgId()}`).catch(() => [])
        ]);
        const pick = (...k) => k.map(x => s[x]).find(x => x !== undefined) ?? 0;
        if(document.getElementById('totalPosts')) totalPosts.textContent = pick('total_posts');
        if(document.getElementById('scheduledPosts')) scheduledPosts.textContent = pick('scheduled_posts');
        if(document.getElementById('publishedPosts')) publishedPosts.textContent = pick('published_posts');
        if(document.getElementById('aiGenerations')) aiGenerations.textContent = pick('ai_generations');
        if(document.getElementById('qaPosts')) qaPosts.textContent = pick('total_posts');
        if(document.getElementById('qaScheduled')) qaScheduled.textContent = pick('scheduled_posts');
        if(document.getElementById('qaPublished')) qaPublished.textContent = pick('published_posts');
        if(document.getElementById('qaAccounts')) qaAccounts.textContent = pick('connected_accounts', 'social_accounts') || a.length;
        if(document.getElementById('recentPosts')) recentPosts.innerHTML = tablePosts(r);
        
        if(document.getElementById('dashboardAccounts')) {
            dashboardAccounts.innerHTML = a.length ? a.map(x => `<div><b>${esc(x.account_name)}</b> <small style="text-transform: capitalize; color:#64748b;">${esc((x.provider || '').replace('_', ' '))}</small></div>`).join('') : '<p class="muted">No accounts connected.</p>';
        }

        const activePlatform = localStorage.getItem('active_platform');
        const aiStudioDropdown = document.querySelector('.ai-studio select') || document.getElementById('aiPlatformSelect');
        if (aiStudioDropdown && activePlatform) {
            Array.from(aiStudioDropdown.options).forEach(opt => {
                if (opt.value.toLowerCase().includes(activePlatform.toLowerCase()) || 
                    opt.text.toLowerCase().includes(activePlatform.toLowerCase()) ||
                    (activePlatform.includes('google') && opt.text.toLowerCase().includes('google'))) {
                    opt.selected = true;
                }
            });
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

function tablePosts(rows){
    if(!rows || !rows.length) return '<p class="muted">No posts found.</p>';
    return `<table class="table">
        <thead>
            <tr>
                <th>Title</th>
                <th>Platform</th>
                <th>Status</th>
                <th>Scheduled</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            ${rows.map(p => `
                <tr>
                    <td><b>${esc(p.title || 'Untitled')}</b><br><small>${esc((p.caption || '').slice(0, 60))}</small></td>
                    <td>${p.social_account_id || '—'}</td>
                    <td><span class="status ${p.status}">${esc(p.status)}</span></td>
                    <td>${fmtDate(p.scheduled_at)}</td>
                    <td>
                        ${p.status !== 'published' ? `<button class="btn small" style="background:#2563eb;color:#fff;margin-right:4px;" onclick="publishPost(${p.id})">Publish</button>` : ''}
                        <button class="btn small" onclick="editPost(${p.id})">Edit</button> 
                        <button class="btn small danger" onclick="deletePost(${p.id})">Delete</button>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    </table>`;
}

async function loadPosts(){
    if(!orgId()) return;
    try{
        postsCache = await api(`/posts/?organization_id=${orgId()}`);
        renderPosts(postsCache);
    } catch(e) {
        if(document.getElementById('postsTable')) postsTable.innerHTML = e.message;
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

function renderPosts(rows){
    if(document.getElementById('postsTable')) postsTable.innerHTML = tablePosts(rows);
}

document.getElementById('postSearch')?.addEventListener('input', e => {
    renderPosts(postsCache.filter(p => (p.title + ' ' + p.caption).toLowerCase().includes(e.target.value.toLowerCase())));
});

document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
    document.querySelectorAll('.tabs button').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderPosts(b.dataset.status === 'all' ? postsCache : postsCache.filter(p => p.status === b.dataset.status));
});

function editPost(id){
    const p = postsCache.find(x => x.id === id);
    if(!p) return;
    editPostId.value = id;
    editTitle.value = p.title || '';
    editCaption.value = p.caption || '';
    editSchedule.value = toLocalInputString(p.scheduled_at);
    openModal('postModal');
}

document.getElementById('editPostForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        let formattedSchedule = null;
        if(editSchedule.value){
            formattedSchedule = istInputToUTCISOString(editSchedule.value);
        }
        await api(`/posts/${editPostId.value}`, {
            method: 'PUT',
            body: JSON.stringify({
                title: editTitle.value,
                caption: editCaption.value,
                scheduled_at: formattedSchedule
            })
        });
        if (typeof showToast === 'function') showToast('Post updated');
        closeModal('postModal');
        loadPosts();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function publishPost(id){
    if(!confirm('Publish this post now?')) return;
    try{
        await api(`/posts/${id}/publish`, { method: 'POST' });
        if (typeof showToast === 'function') showToast('Post published successfully! 🚀');
        await loadPosts();
        if(typeof loadDashboard === 'function') loadDashboard();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message || 'Publishing failed', true);
    }
}

async function deletePost(id){
    if(!confirm('Delete this post?')) return;
    try{
        await api(`/posts/${id}`, { method: 'DELETE' });
        if (typeof showToast === 'function') showToast('Post deleted successfully');
        postsCache = postsCache.filter(p => p.id !== id);
        renderPosts(postsCache);
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message || 'Delete failed', true);
    }
}

// =========================================================
// MULTI-ACCOUNT SELECTOR FOR POST CREATION
// =========================================================

async function loadCreatePost() {
    const container = document.getElementById('socialAccount') || document.getElementById('socialAccountsContainer');
    if (!container) return;

    if (!orgId()) {
        container.innerHTML = '<p class="muted">Create an organization first.</p>';
        return;
    }

    try {
        const accounts = await api(`/social-accounts/?organization_id=${orgId()}`).catch(() => []);

        if (!Array.isArray(accounts) || !accounts.length) {
            container.innerHTML = `
                <div style="padding: 10px; border: 1px dashed #cbd5e1; border-radius: 8px; font-size: 13px; color: #64748b;">
                    No accounts connected. Connect your social accounts from the <a href="/social-accounts" style="color:#2563eb; text-decoration:underline;">Accounts tab</a> first.
                </div>
            `;
            return;
        }

        // Default: Sabhi accounts select rahenge
        selectedSocialAccountIds = accounts.map(a => a.id);

        // Group accounts by platform
        const grouped = accounts.reduce((acc, item) => {
            const provider = (item.provider || 'OTHER').toUpperCase();
            if (!acc[provider]) acc[provider] = [];
            acc[provider].push(item);
            return acc;
        }, {});

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 13px; font-weight: 600; color: #475569;">Target Platforms (${accounts.length} connected)</span>
                <button type="button" class="btn small" style="padding: 2px 8px; font-size: 11px; cursor: pointer;" onclick="toggleSelectAllAccounts(${JSON.stringify(accounts.map(a => a.id)).replace(/"/g, '&quot;')})">
                    Select / Deselect All
                </button>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px;">
        `;

        for (const [provider, accList] of Object.entries(grouped)) {
            accList.forEach(a => {
                html += `
                    <label style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; background: #f8fafc; transition: all 0.2s;">
                        <input type="checkbox" value="${a.id}" class="social-acc-checkbox" checked onchange="handleAccountToggle(${a.id})" style="cursor:pointer;" />
                        <span style="font-weight: 700; font-size: 11px; padding: 2px 6px; border-radius: 4px; background: #e2e8f0;">${esc(provider)}</span>
                        <span style="font-size: 13px; font-weight: 500; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${esc(a.account_name)}</span>
                    </label>
                `;
            });
        }

        html += `</div>`;
        container.innerHTML = html;

    } catch (e) {
        container.innerHTML = '<p class="muted">Unable to load connected accounts.</p>';
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

function handleAccountToggle(id) {
    if (selectedSocialAccountIds.includes(id)) {
        selectedSocialAccountIds = selectedSocialAccountIds.filter(x => x !== id);
    } else {
        selectedSocialAccountIds.push(id);
    }
}

function toggleSelectAllAccounts(allIds) {
    const checkboxes = document.querySelectorAll('.social-acc-checkbox');
    if (selectedSocialAccountIds.length === allIds.length) {
        selectedSocialAccountIds = [];
        checkboxes.forEach(cb => cb.checked = false);
    } else {
        selectedSocialAccountIds = [...allIds];
        checkboxes.forEach(cb => cb.checked = true);
    }
}

document.getElementById('createPostForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedSocialAccountIds.length) {
        if (typeof showToast === 'function') showToast('Please select at least one social account!', true);
        return;
    }

    const payload = {
        organization_id: orgId(),
        account_ids: selectedSocialAccountIds,
        title: document.getElementById('postTitle')?.value || '',
        caption: document.getElementById('postCaption')?.value || '',
        media_url: document.getElementById('mediaUrl')?.value || null,
        scheduled_at: istInputToUTCISOString(document.getElementById('postSchedule')?.value)
    };

    try {
        await api('/posts/create-multi', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (typeof showToast === 'function') showToast('Post created across all selected platforms! 🚀');
        location.href = '/posts';
    } catch (err) {
        if (typeof showToast === 'function') showToast(err.message || 'Post creation failed', true);
    }
});

['postTitle', 'postCaption'].forEach(id => document.getElementById(id)?.addEventListener('input', e => {
    const el = document.getElementById(id === 'postTitle' ? 'previewTitle' : 'previewCaption');
    if(el) el.textContent = e.target.value || (id === 'postTitle' ? 'Your title' : 'Your caption will appear here.');
}));

async function loadCalendar(){
    renderCalendar([]);
    if(!orgId()) return;
    try{
        const rows = await api(`/calendar/?organization_id=${orgId()}`);
        renderCalendar(rows);
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

function changeMonth(n){
    calDate.setMonth(calDate.getMonth() + n);
    loadCalendar();
}

function renderCalendar(events){
    if(!document.getElementById('calendarTitle') || !document.getElementById('calendarGrid')) return;
    calendarTitle.textContent = calDate.toLocaleString('en', { month: 'long', year: 'numeric' });
    const y = calDate.getFullYear(), m = calDate.getMonth(), start = new Date(y, m, 1).getDay(), days = new Date(y, m + 1, 0).getDate();
    let h = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => `<div class="day-head">${d}</div>`).join('');
    for(let i = 0; i < start; i++) h += '<div></div>';
    for(let d = 1; d <= days; d++){
        const ev = events.filter(e => {
            const dt = new Date(e.scheduled_at);
            return dt.getDate() === d && dt.getMonth() === m;
        });
        h += `<div><b>${d}</b>${ev.map(x => `<div class="event">${esc(x.title || 'Post')}</div>`).join('')}</div>`;
    }
    calendarGrid.innerHTML = h;
}

async function loadAnalytics(){
    if(!orgId()) return;
    try{
        const [summary, charts, posts] = await Promise.all([
            api(`/analytics/summary?organization_id=${orgId()}`).catch(() => ({})),
            api(`/dashboard/charts?organization_id=${orgId()}`).catch(() => ({})),
            api(`/posts/?organization_id=${orgId()}`).catch(() => [])
        ]);
        if(document.getElementById('reach')) reach.textContent = summary.total_reach ?? summary.reach ?? '—';
        if(document.getElementById('impressions')) impressions.textContent = summary.total_impressions ?? summary.impressions ?? '—';
        if(document.getElementById('engagement')) engagement.textContent = (summary.engagement_rate ?? summary.engagement ?? '—') + (typeof(summary.engagement_rate ?? summary.engagement) === 'number' ? '%' : '');
        if(document.getElementById('clicks')) clicks.textContent = summary.total_clicks ?? summary.clicks ?? '—';
        if(document.getElementById('analyticsPosts')) analyticsPosts.innerHTML = tablePosts(posts.slice(0, 8));
        
        if(document.getElementById('performanceChart')) {
            new Chart(performanceChart, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{ label: 'Engagement', data: charts.engagement || [10, 16, 12, 22, 19, 26, 30], tension: .35 }]
                },
                options: { responsive: true }
            });
        }
        if(document.getElementById('statusChart')) {
            const counts = ['draft', 'scheduled', 'published'].map(s => posts.filter(p => p.status === s).length);
            new Chart(statusChart, {
                type: 'doughnut',
                data: {
                    labels: ['Draft', 'Scheduled', 'Published'],
                    datasets: [{ data: counts }]
                }
            });
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

// SAFE ACCOUNTS LOADER (Preserves OAuth Cards)
async function loadAccounts(){
    if(!orgId()) return;
    try{
        const rows = await api(`/social-accounts/?organization_id=${orgId()}`);
        const grid = document.getElementById('accountsGrid');
        if(!grid) return;

        if (!rows || !rows.length) {
            grid.innerHTML = `<div class="card" style="padding: 16px; border: 1px dashed #cbd5e1; border-radius: 8px;">
                <p class="muted" style="margin: 0;">Abhi tak koi account connect nahi hai. Upar diye gaye buttons se connect karein.</p>
            </div>`;
            return;
        }

        grid.innerHTML = rows.map(a => `
            <div class="card" style="padding: 16px; border-radius: 10px; display: flex; align-items: center; justify-content: space-between; border: 1px solid #e2e8f0; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                        ${getPlatformIcon(a.provider)}
                    </div>
                    <div>
                        <h4 style="margin: 0; font-size: 15px;">${esc(a.account_name)}</h4>
                        <small class="muted" style="text-transform: capitalize;">${esc((a.provider || '').replace('_', ' '))}</small>
                    </div>
                </div>
                <button class="btn small danger" onclick="deleteAccount(${a.id})">Disconnect</button>
            </div>
        `).join('');
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

document.getElementById('accountForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        const payload = {
            organization_id: orgId(),
            provider: provider.value,
            account_name: accountName.value,
            access_token: accessToken.value,
            refresh_token: refreshToken.value || null
        };

        const accField = document.getElementById('gmbAccountName');
        const locField = document.getElementById('gmbLocationId');
        if (provider.value === 'google_business' && (accField?.value || locField?.value)) {
            payload.metadata = {
                account_id: accField?.value?.trim() || '',
                location_id: locField?.value?.trim() || ''
            };
        }

        await api('/social-accounts/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        closeModal('accountModal');
        if (typeof showToast === 'function') showToast('Account connected successfully');
        loadAccounts();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function deleteAccount(id){
    if(!confirm('Disconnect account?')) return;
    try{
        await api(`/social-accounts/${id}`, { method: 'DELETE' });
        if (typeof showToast === 'function') showToast('Disconnected');
        loadAccounts();
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

async function loadMedia(){
    if(!orgId()) return;
    try{
        const rows = await api(`/media/list?organization_id=${orgId()}`);
        if(document.getElementById('mediaGrid')) {
            mediaGrid.innerHTML = rows.length ? rows.map(m => `
                <div class="media-item">
                    <div class="media-thumb">${m.file_type?.includes('video') ? '▶' : '▧'}</div>
                    <div class="media-meta">
                        <b>ID: ${m.id} | ${esc(m.file_name || 'Media')}</b>
                        <p>${fmtDate(m.created_at)}</p>
                        <button class="btn small" onclick="deleteMedia(${m.id})">Delete</button>
                    </div>
                </div>
            `).join('') : '<p>No media uploaded.</p>';
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

document.getElementById('mediaUpload')?.addEventListener('change', async e => {
    const f = e.target.files[0];
    if(!f) return;
    const fd = new FormData();
    fd.append('file', f);
    try{
        await api(`/media/upload?organization_id=${orgId()}`, { method: 'POST', body: fd });
        if (typeof showToast === 'function') showToast('Uploaded');
        loadMedia();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function deleteMedia(id){
    try{
        await api(`/media/${id}`, { method: 'DELETE' });
        loadMedia();
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

async function loadOrganizations(){
    try{
        const rows = await api('/organizations/');
        if(document.getElementById('organizationsGrid')) {
            organizationsGrid.innerHTML = rows.map(o => `
                <div class="account-card">
                    <div class="platform-icon">◇</div>
                    <h3>${esc(o.name)}</h3>
                    <p>${esc(o.industry || 'General')}</p>
                    <p class="muted">${esc(o.timezone || '')}</p>
                    <button class="btn" onclick="selectOrg(${o.id})">Open</button>
                </div>
            `).join('') || '<p>No organizations yet.</p>';
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

function selectOrg(id){
    localStorage.setItem('organization_id', id);
    location.href = '/dashboard';
}

document.getElementById('orgForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        const d = await api('/organizations/', {
            method: 'POST',
            body: JSON.stringify({
                name: orgName.value,
                industry: orgIndustry.value,
                timezone: orgTimezone.value,
                language: orgLanguage.value
            })
        });
        localStorage.setItem('organization_id', d.id);
        location.reload();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function loadMembers(){
    if(!orgId()) return;
    try{
        const rows = await api(`/organizations/${orgId()}/members`);
        if(document.getElementById('membersTable')) {
            membersTable.innerHTML = `<table class="table">
                <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead>
                <tbody>${rows.map(m => `<tr><td>${esc(m.user?.name || m.name || 'Member')}</td><td>${esc(m.user?.email || m.email || '')}</td><td>${esc(m.role || 'member')}</td><td>Active</td></tr>`).join('')}</tbody>
            </table>`;
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

document.getElementById('memberForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        await api(`/organizations/${orgId()}/members`, {
            method: 'POST',
            body: JSON.stringify({ email: memberEmail.value, role: memberRole.value })
        });
        closeModal('memberModal');
        if (typeof showToast === 'function') showToast('Member added');
        loadMembers();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function loadCompetitors(){
    if(!orgId()) return;
    try{
        const rows = await api(`/competitors/?organization_id=${orgId()}`);
        if(document.getElementById('competitorsTable')) {
            competitorsTable.innerHTML = `<table class="table">
                <thead><tr><th>Name</th><th>Platform</th><th>Profile</th><th>Added</th></tr></thead>
                <tbody>${rows.map(c => `<tr><td>${esc(c.name)}</td><td>${esc(c.platform)}</td><td>${esc(c.profile_url || '—')}</td><td>${fmtDate(c.created_at)}</td></tr>`).join('')}</tbody>
            </table>`;
        }
    } catch(e) {
        if(document.getElementById('competitorsTable')) competitorsTable.innerHTML = '<p class="muted">No competitors or endpoint unavailable.</p>';
    }
}

document.getElementById('competitorForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        await api('/competitors/', {
            method: 'POST',
            body: JSON.stringify({
                organization_id: orgId(),
                name: competitorName.value,
                platform: competitorPlatform.value,
                profile_url: competitorUrl.value
            })
        });
        closeModal('competitorModal');
        loadCompetitors();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function loadBilling(){
    try{
        const [plans, inv, usage] = await Promise.all([
            api('/plans/').catch(() => []),
            api(`/invoices/?organization_id=${orgId()}`).catch(() => []),
            api(`/usage/?organization_id=${orgId()}`).catch(() => [])
        ]);
        if(document.getElementById('plansGrid')) {
            plansGrid.innerHTML = plans.map(p => `
                <div class="pricing-card">
                    <h3>${esc(p.name)}</h3>
                    <h2>₹${p.price || 0}</h2>
                    <p>${esc(p.description || '')}</p>
                    <button class="btn primary">Choose plan</button>
                </div>
            `).join('') || '<p>No plans configured.</p>';
        }
        if(document.getElementById('invoiceCount')) invoiceCount.textContent = inv.length;
        if(document.getElementById('usageCount')) usageCount.textContent = Array.isArray(usage) ? usage.length : (usage.total_usage ?? '—');
        if(document.getElementById('invoiceTable')) {
            invoiceTable.innerHTML = `<table class="table">
                <thead><tr><th>Invoice</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>${inv.map(i => `<tr><td>#${i.id}</td><td>₹${i.amount || 0}</td><td>${esc(i.status)}</td><td>${fmtDate(i.created_at)}</td></tr>`).join('')}</tbody>
            </table>`;
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

async function loadNotifications(){
    try{
        const rows = await api('/notifications/');
        if(document.getElementById('notificationList')) {
            notificationList.innerHTML = rows.map(n => `
                <div><b>${esc(n.title || n.type || 'Notification')}</b><p>${esc(n.message || '')}</p><small>${fmtDate(n.created_at)}</small></div>
            `).join('') || '<p>No notifications.</p>';
        }
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

async function markAllRead(){
    try{
        await api('/notifications/read-all', { method: 'PUT' });
        loadNotifications();
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

async function loadRoles(){
    if(!orgId()) return;
    try{
        const [roles, perms] = await Promise.all([
            api(`/roles/?organization_id=${orgId()}`),
            api('/permissions')
        ]);
        if(document.getElementById('rolesList')) rolesList.innerHTML = roles.map(r => `<div><b>${esc(r.name)}</b><p>${esc(r.description || '')}</p></div>`).join('') || '<p>No roles.</p>';
        if(document.getElementById('permissionsList')) permissionsList.innerHTML = perms.map(p => `<span>${esc(p.name)}</span>`).join('');
    } catch(e) {
        if (typeof showToast === 'function') showToast(e.message, true);
    }
}

document.getElementById('roleForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        await api('/roles/', {
            method: 'POST',
            body: JSON.stringify({
                organization_id: orgId(),
                name: roleName.value,
                description: roleDescription.value
            })
        });
        closeModal('roleModal');
        loadRoles();
    } catch(err) {
        if (typeof showToast === 'function') showToast(err.message, true);
    }
});

async function loadAuditLogs(){
    if(!orgId()) return;
    try{
        const rows = await api(`/audit-logs/?organization_id=${orgId()}`);
        if(document.getElementById('auditTable')) {
            auditTable.innerHTML = `<table class="table">
                <thead><tr><th>Action</th><th>Entity</th><th>User</th><th>Time</th></tr></thead>
                <tbody>${rows.map(x => `<tr><td>${esc(x.action)}</td><td>${esc(x.entity_type)} #${x.entity_id || ''}</td><td>${x.user_id || '—'}</td><td>${fmtDate(x.created_at)}</td></tr>`).join('')}</tbody>
            </table>`;
        }
    } catch(e) {
        if(document.getElementById('auditTable')) auditTable.innerHTML = `<p>${esc(e.message)}</p>`;
    }
}

function loadSettings(){
    if(!document.getElementById('themeSelect')) return;
    themeSelect.value = localStorage.getItem('theme') || 'light';
    themeSelect.onchange = () => {
        localStorage.setItem('theme', themeSelect.value);
        document.documentElement.dataset.theme = themeSelect.value;
    }
}

bootstrap();