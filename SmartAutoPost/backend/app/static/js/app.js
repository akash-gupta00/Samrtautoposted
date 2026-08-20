(function(){
    const params = new URLSearchParams(window.location.search);
    const tokenFromFacebook = params.get("token");
    const refreshFromFacebook = params.get("refresh");

    if(tokenFromFacebook){
        localStorage.setItem("access_token", tokenFromFacebook);
        localStorage.setItem("refresh_token", refreshFromFacebook || "");
        localStorage.setItem("login_provider", params.get("provider") || "social");
        console.log("Social login token saved");
        setTimeout(()=>{
            window.location.href="/dashboard";
        }, 100);
    }
})();

let organizations = [], currentOrg = null, postsCache = [];

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

// Converts a "YYYY-MM-DDTHH:MM" datetime-local value (assumed to be entered
// in IST, since that's what fmtDate displays) into a proper UTC ISO string.
// This does NOT depend on the browser/system timezone — it always treats
// the input as IST (+05:30) and converts to UTC explicitly.
function istInputToUTCISOString(localValue){
    if(!localValue) return null;
    // localValue looks like "2026-08-20T16:32" (no seconds, no offset)
    let value = localValue.length === 16 ? localValue + ':00' : localValue;
    const withOffset = `${value}+05:30`;
    const d = new Date(withOffset);
    if(isNaN(d.getTime())) return null;
    return d.toISOString();
}

// Converts a UTC/ISO date string into a "YYYY-MM-DDTHH:MM" value expressed
// in IST, suitable for a <input type="datetime-local"> field. This does NOT
// depend on the browser/system timezone — it always renders in IST.
function toLocalInputString(dateStr){
    if(!dateStr) return '';
    let iso = typeof dateStr === 'string' && !dateStr.includes('Z') && !dateStr.includes('+') ? dateStr + 'Z' : dateStr;
    const d = new Date(iso);
    if(isNaN(d.getTime())) return '';

    // Format the UTC instant into IST wall-clock parts using Intl, then
    // assemble the datetime-local string manually.
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

async function bootstrap(){
    if(!token()){location.href='/login';return}
    try{
        const me = await api('/auth/me');
        localStorage.setItem('user', JSON.stringify(me));
        setUser(me);
        const isAdmin = me.role === 'admin';
        document.body.dataset.role = isAdmin ? 'admin' : 'user';
        document.body.dataset.authProvider = me.auth_provider || 'email';
        organizations = await api('/organizations/');
        const sel = document.getElementById('organizationSelect');
        if(sel){
            sel.innerHTML = organizations.map(o => `<option value="${o.id}">${esc(o.name)}</option>`).join('');
            let saved = Number(localStorage.getItem('organization_id'));
            currentOrg = organizations.find(o => o.id === saved) || organizations[0];
            if(currentOrg){
                sel.value = currentOrg.id;
                localStorage.setItem('organization_id', currentOrg.id);
                document.getElementById('sidebarOrg').textContent = currentOrg.name;
            }
            sel.onchange = () => {
                localStorage.setItem('organization_id', sel.value);
                location.reload();
            }
        }
        if(!organizations.length && isAdmin && location.pathname !== '/organizations'){
            showToast('Create an organization to start', true);
            setTimeout(() => {
                if(location.pathname !== '/organizations') location.href = '/organizations';
            }, 1200);
        } else if(!organizations.length && !isAdmin){
            showToast('Account setup me thodi der lag rahi hai, please refresh karein.', true);
        }
        await loadPage();
    } catch(e) {
        showToast(e.message, true);
    }
}

function setUser(u){
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
            api(`/dashboard/summary?organization_id=${orgId()}`),
            api(`/dashboard/recent-posts?organization_id=${orgId()}&limit=5`).catch(() => []),
            api(`/social-accounts/?organization_id=${orgId()}`).catch(() => [])
        ]);
        const pick = (...k) => k.map(x => s[x]).find(x => x !== undefined) ?? 0;
        totalPosts.textContent = pick('total_posts');
        scheduledPosts.textContent = pick('scheduled_posts');
        publishedPosts.textContent = pick('published_posts');
        aiGenerations.textContent = pick('ai_generations');
        qaPosts.textContent = pick('total_posts');
        qaScheduled.textContent = pick('scheduled_posts');
        qaPublished.textContent = pick('published_posts');
        qaAccounts.textContent = pick('connected_accounts', 'social_accounts') || a.length;
        recentPosts.innerHTML = tablePosts(r);
        dashboardAccounts.innerHTML = a.length ? a.map(x => `<div><b>${esc(x.account_name)}</b><small>${esc(x.provider)}</small></div>`).join('') : '<p class="muted">No accounts connected.</p>';
    } catch(e) {
        showToast(e.message, true);
    }
}

function tablePosts(rows){
    if(!rows.length) return '<p class="muted">No posts found.</p>';
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
        postsTable.innerHTML = e.message;
        showToast(e.message, true);
    }
}

function renderPosts(rows){
    postsTable.innerHTML = tablePosts(rows);
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
        showToast('Post updated');
        closeModal('postModal');
        loadPosts();
    } catch(err) {
        showToast(err.message, true);
    }
});

async function publishPost(id){
    if(!confirm('Publish this post to Instagram now?')) return;
    try{
        await api(`/posts/${id}/publish`, { method: 'POST' });
        showToast('Post published successfully to Instagram! 🎉');
        await loadPosts();
        if(typeof loadDashboard === 'function') loadDashboard();
    } catch(err) {
        showToast(err.message || 'Publishing failed', true);
    }
}

async function deletePost(id){
    if(!confirm('Delete this post?')) return;
    try{
        await api(`/posts/${id}`, { method: 'DELETE' });
        showToast('Post deleted successfully');
        postsCache = postsCache.filter(p => p.id !== id);
        renderPosts(postsCache);
    } catch(e) {
        showToast(e.message || 'Delete failed', true);
    }
}

async function loadCreatePost(){
    const select = document.getElementById('socialAccount');
    if(!select) return;
    if(!orgId()){
        select.innerHTML = '<option value="">Create an organization first</option>';
        select.disabled = true;
        return;
    }
    try{
        const accounts = await api(`/social-accounts/?organization_id=${orgId()}`);
        if(!Array.isArray(accounts) || !accounts.length){
            select.innerHTML = '<option value="">Connect a social account first</option>';
            select.disabled = true;
            return;
        }
        select.disabled = false;
        select.innerHTML = accounts.map(x => `<option value="${x.id}">${esc(x.account_name)} (${esc(x.provider)})</option>`).join('');
    } catch(e) {
        select.innerHTML = '<option value="">Unable to load accounts</option>';
        select.disabled = true;
        showToast(e.message, true);
    }
}

['postTitle', 'postCaption'].forEach(id => document.getElementById(id)?.addEventListener('input', e => {
    document.getElementById(id === 'postTitle' ? 'previewTitle' : 'previewCaption').textContent = e.target.value || (id === 'postTitle' ? 'Your title' : 'Your caption will appear here.');
}));

document.getElementById('createPostForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    if(!orgId()){ showToast('Create an organization first', true); location.href = '/organizations'; return; }
    if(!Number(socialAccount.value)){ showToast('Connect and select a social account first', true); return; }
    try{
        const media = mediaIds.value.split(',').map(x => Number(x.trim())).filter(Boolean);
        let formattedSchedule = null;
        if(scheduledAt.value){
            formattedSchedule = istInputToUTCISOString(scheduledAt.value);
        }
        await api('/posts/', {
            method: 'POST',
            body: JSON.stringify({
                organization_id: orgId(),
                social_account_id: Number(socialAccount.value),
                title: postTitle.value.trim(),
                caption: postCaption.value.trim(),
                scheduled_at: formattedSchedule,
                media_ids: media
            })
        });
        showToast('Post created successfully');
        setTimeout(() => location.href = '/posts', 700);
    } catch(err) {
        showToast(err.message, true);
    }
});

async function quickGenerate(){
    try{
        const d = await api('/gemini-generate', {
            method: 'POST',
            body: JSON.stringify({
                organization_id: orgId(),
                generation_type: 'caption',
                platform: quickPlatform.value.toLowerCase(),
                prompt: quickPrompt.value
            })
        });
        quickResult.innerHTML = `<b>Caption idea</b><p>${esc(d.generated_content || d.content || JSON.stringify(d))}</p>`;
    } catch(e) {
        showToast(e.message, true);
    }
}

document.getElementById('aiForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const type = aiType.value;
    let path = type === 'caption' ? '/ai/caption' : type === 'hashtags' ? '/ai/hashtags' : type === 'seo' ? '/ai/seo' : '/ai/image-prompt';
    let body = { prompt: aiPrompt.value, platform: aiPlatform.value.toLowerCase() };
    try{
        const d = await api(path, { method: 'POST', body: JSON.stringify(body) });
        aiResult.textContent = d.generated_content || d.caption || d.hashtags || d.seo_content || d.image_prompt || JSON.stringify(d, null, 2);
    } catch(err) {
        showToast(err.message, true);
    }
});

function copyAI(){
    navigator.clipboard.writeText(aiResult.textContent);
    showToast('Copied');
}

let calDate = new Date();
async function loadCalendar(){
    renderCalendar([]);
    if(!orgId()) return;
    try{
        const rows = await api(`/calendar/?organization_id=${orgId()}`);
        renderCalendar(rows);
    } catch(e) {
        showToast(e.message, true);
    }
}

function changeMonth(n){
    calDate.setMonth(calDate.getMonth() + n);
    loadCalendar();
}

function renderCalendar(events){
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
        reach.textContent = summary.total_reach ?? summary.reach ?? '—';
        impressions.textContent = summary.total_impressions ?? summary.impressions ?? '—';
        engagement.textContent = (summary.engagement_rate ?? summary.engagement ?? '—') + (typeof(summary.engagement_rate ?? summary.engagement) === 'number' ? '%' : '');
        clicks.textContent = summary.total_clicks ?? summary.clicks ?? '—';
        analyticsPosts.innerHTML = tablePosts(posts.slice(0, 8));
        new Chart(performanceChart, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{ label: 'Engagement', data: charts.engagement || [10, 16, 12, 22, 19, 26, 30], tension: .35 }]
            },
            options: { responsive: true }
        });
        const counts = ['draft', 'scheduled', 'published'].map(s => posts.filter(p => p.status === s).length);
        new Chart(statusChart, {
            type: 'doughnut',
            data: {
                labels: ['Draft', 'Scheduled', 'Published'],
                datasets: [{ data: counts }]
            }
        });
    } catch(e) {
        showToast(e.message, true);
    }
}

async function loadAccounts(){
    if(!orgId()) return;
    try{
        const rows = await api(`/social-accounts/?organization_id=${orgId()}`);
        accountsGrid.innerHTML = rows.length ? rows.map(a => `
            <div class="account-card">
                <div class="platform-icon">${a.provider === 'facebook' ? 'f' : a.provider === 'instagram' ? '◎' : 'in'}</div>
                <h3>${esc(a.account_name)}</h3>
                <p class="muted">${esc(a.provider)}</p>
                <button class="btn danger" onclick="deleteAccount(${a.id})">Disconnect</button>
            </div>
        `).join('') : '<div class="card"><p>No social accounts connected.</p></div>';
    } catch(e) {
        showToast(e.message, true);
    }
}

document.getElementById('accountForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    try{
        await api('/social-accounts/', {
            method: 'POST',
            body: JSON.stringify({
                organization_id: orgId(),
                provider: provider.value,
                account_name: accountName.value,
                access_token: accessToken.value,
                refresh_token: refreshToken.value || null
            })
        });
        closeModal('accountModal');
        showToast('Account connected');
        loadAccounts();
    } catch(err) {
        showToast(err.message, true);
    }
});

async function deleteAccount(id){
    if(!confirm('Disconnect account?')) return;
    try{
        await api(`/social-accounts/${id}`, { method: 'DELETE' });
        showToast('Disconnected');
        loadAccounts();
    } catch(e) {
        showToast(e.message, true);
    }
}

async function loadMedia(){
    if(!orgId()) return;
    try{
        const rows = await api(`/media/list?organization_id=${orgId()}`);
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
    } catch(e) {
        showToast(e.message, true);
    }
}

document.getElementById('mediaUpload')?.addEventListener('change', async e => {
    const f = e.target.files[0];
    if(!f) return;
    const fd = new FormData();
    fd.append('file', f);
    try{
        await api(`/media/upload?organization_id=${orgId()}`, { method: 'POST', body: fd });
        showToast('Uploaded');
        loadMedia();
    } catch(err) {
        showToast(err.message, true);
    }
});

async function deleteMedia(id){
    try{
        await api(`/media/${id}`, { method: 'DELETE' });
        loadMedia();
    } catch(e) {
        showToast(e.message, true);
    }
}

async function loadOrganizations(){
    try{
        const rows = await api('/organizations/');
        organizationsGrid.innerHTML = rows.map(o => `
            <div class="account-card">
                <div class="platform-icon">◇</div>
                <h3>${esc(o.name)}</h3>
                <p>${esc(o.industry || 'General')}</p>
                <p class="muted">${esc(o.timezone || '')}</p>
                <button class="btn" onclick="selectOrg(${o.id})">Open</button>
            </div>
        `).join('') || '<p>No organizations yet.</p>';
    } catch(e) {
        showToast(e.message, true);
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
        showToast(err.message, true);
    }
});

async function loadMembers(){
    if(!orgId()) return;
    try{
        const rows = await api(`/organizations/${orgId()}/members`);
        membersTable.innerHTML = `<table class="table">
            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead>
            <tbody>${rows.map(m => `<tr><td>${esc(m.user?.name || m.name || 'Member')}</td><td>${esc(m.user?.email || m.email || '')}</td><td>${esc(m.role || 'member')}</td><td>Active</td></tr>`).join('')}</tbody>
        </table>`;
    } catch(e) {
        showToast(e.message, true);
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
        showToast('Member added');
        loadMembers();
    } catch(err) {
        showToast(err.message, true);
    }
});

async function loadCompetitors(){
    if(!orgId()) return;
    try{
        const rows = await api(`/competitors/?organization_id=${orgId()}`);
        competitorsTable.innerHTML = `<table class="table">
            <thead><tr><th>Name</th><th>Platform</th><th>Profile</th><th>Added</th></tr></thead>
            <tbody>${rows.map(c => `<tr><td>${esc(c.name)}</td><td>${esc(c.platform)}</td><td>${esc(c.profile_url || '—')}</td><td>${fmtDate(c.created_at)}</td></tr>`).join('')}</tbody>
        </table>`;
    } catch(e) {
        competitorsTable.innerHTML = '<p class="muted">No competitors or endpoint unavailable.</p>';
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
        showToast(err.message, true);
    }
});

async function loadBilling(){
    try{
        const [plans, inv, usage] = await Promise.all([
            api('/plans/').catch(() => []),
            api(`/invoices/?organization_id=${orgId()}`).catch(() => []),
            api(`/usage/?organization_id=${orgId()}`).catch(() => [])
        ]);
        plansGrid.innerHTML = plans.map(p => `
            <div class="pricing-card">
                <h3>${esc(p.name)}</h3>
                <h2>₹${p.price || 0}</h2>
                <p>${esc(p.description || '')}</p>
                <button class="btn primary">Choose plan</button>
            </div>
        `).join('') || '<p>No plans configured.</p>';
        invoiceCount.textContent = inv.length;
        usageCount.textContent = Array.isArray(usage) ? usage.length : (usage.total_usage ?? '—');
        invoiceTable.innerHTML = `<table class="table">
            <thead><tr><th>Invoice</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>${inv.map(i => `<tr><td>#${i.id}</td><td>₹${i.amount || 0}</td><td>${esc(i.status)}</td><td>${fmtDate(i.created_at)}</td></tr>`).join('')}</tbody>
        </table>`;
    } catch(e) {
        showToast(e.message, true);
    }
}

async function loadNotifications(){
    try{
        const rows = await api('/notifications/');
        notificationList.innerHTML = rows.map(n => `
            <div><b>${esc(n.title || n.type || 'Notification')}</b><p>${esc(n.message || '')}</p><small>${fmtDate(n.created_at)}</small></div>
        `).join('') || '<p>No notifications.</p>';
    } catch(e) {
        showToast(e.message, true);
    }
}

async function markAllRead(){
    try{
        await api('/notifications/read-all', { method: 'PUT' });
        loadNotifications();
    } catch(e) {
        showToast(e.message, true);
    }
}

async function loadRoles(){
    if(!orgId()) return;
    try{
        const [roles, perms] = await Promise.all([
            api(`/roles/?organization_id=${orgId()}`),
            api('/permissions')
        ]);
        rolesList.innerHTML = roles.map(r => `<div><b>${esc(r.name)}</b><p>${esc(r.description || '')}</p></div>`).join('') || '<p>No roles.</p>';
        permissionsList.innerHTML = perms.map(p => `<span>${esc(p.name)}</span>`).join('');
    } catch(e) {
        showToast(e.message, true);
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
        showToast(err.message, true);
    }
});

async function loadAuditLogs(){
    if(!orgId()) return;
    try{
        const rows = await api(`/audit-logs/?organization_id=${orgId()}`);
        auditTable.innerHTML = `<table class="table">
            <thead><tr><th>Action</th><th>Entity</th><th>User</th><th>Time</th></tr></thead>
            <tbody>${rows.map(x => `<tr><td>${esc(x.action)}</td><td>${esc(x.entity_type)} #${x.entity_id || ''}</td><td>${x.user_id || '—'}</td><td>${fmtDate(x.created_at)}</td></tr>`).join('')}</tbody>
        </table>`;
    } catch(e) {
        auditTable.innerHTML = `<p>${esc(e.message)}</p>`;
    }
}

function loadSettings(){
    themeSelect.value = localStorage.getItem('theme') || 'light';
    themeSelect.onchange = () => {
        localStorage.setItem('theme', themeSelect.value);
        document.documentElement.dataset.theme = themeSelect.value;
    }
}

bootstrap();