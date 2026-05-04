/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright (C) 2026 IMA LLC
 *
 * Marketplace palette controller.
 *
 * Talks to Python via two Fusion bridges:
 *   Outgoing:  adsk.fusionSendData(actionName, dataString)
 *   Incoming:  window.fusionJavaScriptHandler.handle(action, data)
 *
 * A tiny Promise-based RPC layer sits on top so UI code can simply:
 *   await rpc('install', { id, tab })
 */

(() => {
    'use strict';

    // ── RPC plumbing ───────────────────────────────────────────────────────
    let rpcCounter = 0;
    const pending = new Map();

    function rpc(method, params) {
        return new Promise((resolve, reject) => {
            const id = ++rpcCounter;
            pending.set(id, { resolve, reject });
            adsk.fusionSendData('rpc', JSON.stringify({ id, method, params: params || {} }));
        });
    }

    window.fusionJavaScriptHandler = {
        handle(action, data) {
            try {
                if (action === 'setTheme') {
                    document.documentElement.setAttribute('data-theme', data);
                    return 'OK';
                }
                if (action !== 'rpcReply') return 'OK';
                const msg = JSON.parse(data);
                const slot = pending.get(msg.id);
                if (!slot) return 'OK';
                pending.delete(msg.id);
                if (msg.ok) slot.resolve(msg.result);
                else slot.reject(new Error(msg.error || 'unknown'));
            } catch (e) {
                console.error('handle() failed', e);
                return 'FAILED';
            }
            return 'OK';
        }
    };

    // ── DOM references ─────────────────────────────────────────────────────
    const $search          = document.getElementById('search');
    const $installedOnly   = document.getElementById('installed-only');
    const $list            = document.getElementById('plugin-list');
    const $status          = document.getElementById('status');
    const $communityNotice = document.getElementById('community-notice');

    // ── State ──────────────────────────────────────────────────────────────
    const state = {
        tab:      'core',   // 'core' | 'community'
        addins:   [],       // full list from last RPC call
        busy:     new Set(), // ids currently installing/uninstalling
    };

    // ── Status helpers ─────────────────────────────────────────────────────
    function setStatus(text, type) {
        $status.textContent = text || '';
        $status.className = 'status' + (type ? ` ${type}` : '');
    }

    // ── Tab bar ────────────────────────────────────────────────────────────
    const $underline = document.querySelector('.tab-underline');

    function positionUnderline(btn) {
        if (!$underline) return;
        $underline.style.left  = btn.offsetLeft + 'px';
        $underline.style.width = btn.offsetWidth + 'px';
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.tab === state.tab) return;
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            state.tab = btn.dataset.tab;
            positionUnderline(btn);
            $communityNotice.hidden = state.tab !== 'community';
            loadAddins();
        });
    });

    // ── Load ───────────────────────────────────────────────────────────────
    async function loadAddins() {
        $list.innerHTML = '<div class="empty-state">Loading...</div>';
        setStatus('');
        try {
            state.addins = await rpc('listAddins', { tab: state.tab });
            renderList();
        } catch (e) {
            $list.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    }

    // ── Render ─────────────────────────────────────────────────────────────
    function renderList() {
        const query    = $search.value.trim().toLowerCase();
        const onlyInst = $installedOnly.checked;

        const visible = state.addins.filter(a => {
            if (onlyInst && !a.installed) return false;
            if (!query) return true;
            return (
                a.name.toLowerCase().includes(query) ||
                a.description.toLowerCase().includes(query) ||
                (a.publisher || '').toLowerCase().includes(query)
            );
        });

        if (!visible.length) {
            $list.innerHTML = '<div class="empty-state">No add-ins match your filter.</div>';
            return;
        }

        $list.innerHTML = '';
        for (const addin of visible) {
            $list.appendChild(buildRow(addin));
        }
    }

    function buildRow(addin) {
        const isCommunity = state.tab === 'community';
        const isBusy = state.busy.has(addin.id);

        const row = document.createElement('div');
        row.className = 'plugin-row';
        row.dataset.id = addin.id;

        // Left: info
        const info = document.createElement('div');
        info.className = 'plugin-info';

        // Name line
        const nameLine = document.createElement('div');
        nameLine.className = 'plugin-name-line';

        const name = document.createElement('span');
        name.className = 'plugin-name';
        name.textContent = addin.name;
        nameLine.appendChild(name);

        const meta = document.createElement('span');
        meta.className = 'plugin-meta';
        meta.textContent = `v${addin.version} · ${addin.publisher} · ${addin.license}`;
        nameLine.appendChild(meta);

        if (addin.update_available) {
            const badge = document.createElement('span');
            badge.className = 'badge-update';
            badge.textContent = '⚠ Update available';
            nameLine.appendChild(badge);
        }

        info.appendChild(nameLine);

        // Description
        const desc = document.createElement('p');
        desc.className = 'plugin-description';
        desc.textContent = addin.description;
        info.appendChild(desc);

        // Readme link (community tab only)
        if (isCommunity && addin.readme_url) {
            const link = document.createElement('button');
            link.className = 'readme-link';
            link.innerHTML = `<svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2H2a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7"/><path d="M8 1h3v3"/><path d="M11 1 6 6"/></svg> Open on GitHub`;
            link.addEventListener('click', () => openReadme(addin.readme_url));
            info.appendChild(link);
        }

        row.appendChild(info);

        // Right: toggle
        const controls = document.createElement('div');
        controls.className = 'plugin-controls';

        const toggleWrap = document.createElement('label');
        toggleWrap.className = 'toggle-wrap' + (isBusy ? ' busy' : '');
        toggleWrap.title = addin.installed ? 'Uninstall' : 'Install';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = addin.installed;
        checkbox.disabled = isBusy;
        checkbox.addEventListener('change', () => toggleAddin(addin, checkbox));

        const track = document.createElement('span');
        track.className = 'toggle-track';
        const thumb = document.createElement('span');
        thumb.className = 'toggle-thumb';
        track.appendChild(thumb);

        toggleWrap.appendChild(checkbox);
        toggleWrap.appendChild(track);
        controls.appendChild(toggleWrap);

        row.appendChild(controls);
        return row;
    }

    // ── Toggle (install / uninstall) ───────────────────────────────────────
    async function toggleAddin(addin, checkbox) {
        if (state.busy.has(addin.id)) return;

        state.busy.add(addin.id);
        checkbox.disabled = true;
        setStatus(addin.installed ? `Removing ${addin.name}…` : `Installing ${addin.name}…`);

        try {
            let result;
            if (addin.installed) {
                result = await rpc('uninstall', { id: addin.id });
                addin.installed = false;
                addin.installed_version = null;
                addin.update_available = false;
                setStatus(`${addin.name} removed.`, 'success');
            } else {
                result = await rpc('install', { id: addin.id, tab: state.tab });
                addin.installed = true;
                addin.installed_version = addin.version;
                addin.update_available = false;
                setStatus(result.message || `${addin.name} installed.`, 'success');
            }
        } catch (e) {
            // Revert the checkbox visually
            checkbox.checked = addin.installed;
            setStatus(`Error: ${e.message}`, 'error');
        } finally {
            state.busy.delete(addin.id);
        }

        // Re-render the affected row
        const existingRow = $list.querySelector(`[data-id="${addin.id}"]`);
        if (existingRow) {
            existingRow.replaceWith(buildRow(addin));
        }
    }

    // ── Readme ─────────────────────────────────────────────────────────────
    async function openReadme(url) {
        try {
            await rpc('openReadme', { url });
        } catch (e) {
            setStatus(`Could not open readme: ${e.message}`, 'error');
        }
    }

    // ── Search & filter (client-side) ──────────────────────────────────────
    let searchTimer = null;
    $search.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(renderList, 250);
    });

    $installedOnly.addEventListener('change', renderList);

    // ── Boot — wait for Fusion's adsk bridge ──────────────────────────────
    async function applyTheme() {
        try {
            const theme = await rpc('getTheme', {});
            document.documentElement.setAttribute('data-theme', theme);
        } catch (_) { /* keep :root dark default */ }
    }

    async function boot() {
        if (typeof adsk !== 'undefined') {
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) positionUnderline(activeTab);
            await applyTheme();
            loadAddins();
        } else {
            setTimeout(boot, 50);
        }
    }

    // Re-apply theme on palette re-show without a full page reload.
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && typeof adsk !== 'undefined') {
            applyTheme();
        }
    });

    boot();

})();
