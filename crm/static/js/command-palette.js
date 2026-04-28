// Command Palette - Standard JS implementation

// State
var cmdIsOpen = false;
var cmdSelectedIndex = 0;
var cmdResults = [];

// DOM Elements
var cmdOverlay, cmdInput, cmdResultsContainer;

// Data (Mock)
var cmdStaticItems = [
    { title: 'Dashboard', url: 'dashboard', icon: 'layout-dashboard', group: 'Navigation' },
    { title: 'Deals Pipeline', url: 'deals', icon: 'bar-chart-2', group: 'Navigation' },
    { title: 'Contacts', url: 'contacts', icon: 'users', group: 'Navigation' },
    { title: 'Workflows', url: 'workflows', icon: 'git-branch', group: 'Navigation' },
    { title: 'Settings', url: 'settings', icon: 'settings', group: 'Navigation' }
];

document.addEventListener('DOMContentLoaded', function () {
    initCommandPalette();
});

function initCommandPalette() {
    // 1. Inject HTML Overlay
    var html = `
    <div id="cmd-overlay" class="cmd-overlay">
        <div class="cmd-modal">
            <div class="cmd-input-wrapper">
                <i data-lucide="search" class="cmd-icon"></i>
                <input type="text" id="cmd-input" class="cmd-input" placeholder="Search pages, deals, contacts..." autocomplete="off">
                <span class="kbd-shortcut">Esc</span>
            </div>
            <div id="cmd-results" class="cmd-results"></div>
            <div class="cmd-footer">
                <span><span class="kbd-shortcut">↑</span> <span class="kbd-shortcut">↓</span> to navigate</span>
                <span><span class="kbd-shortcut">Enter</span> to select</span>
            </div>
        </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', html);

    // 2. Cache Elements
    cmdOverlay = document.getElementById('cmd-overlay');
    cmdInput = document.getElementById('cmd-input');
    cmdResultsContainer = document.getElementById('cmd-results');

    // 3. Bind Events
    document.addEventListener('keydown', function (e) {
        // Toggle Cmd+K / Ctrl+K
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            toggleCommandPalette();
        }
        // Close on Esc
        if (e.key === 'Escape' && cmdIsOpen) {
            closeCommandPalette();
        }
    });

    cmdInput.addEventListener('input', handleCmdInput);
    cmdInput.addEventListener('keydown', handleCmdNavigation);

    cmdOverlay.addEventListener('click', function (e) {
        if (e.target === cmdOverlay) closeCommandPalette();
    });

    if (window.lucide) window.lucide.createIcons();
}

function toggleCommandPalette() {
    if (cmdIsOpen) closeCommandPalette();
    else openCommandPalette();
}

function openCommandPalette() {
    cmdIsOpen = true;
    cmdOverlay.classList.add('active');
    cmdInput.value = '';
    cmdInput.focus();
    renderCmdResults(cmdStaticItems); // Show default
    if (window.lucide) window.lucide.createIcons();
}

function closeCommandPalette() {
    cmdIsOpen = false;
    cmdOverlay.classList.remove('active');
}

function handleCmdInput(e) {
    var query = e.target.value.toLowerCase().trim();

    if (query === '') {
        renderCmdResults(cmdStaticItems);
        return;
    }

    // Simple filter
    var filtered = cmdStaticItems.filter(function (item) {
        return item.title.toLowerCase().includes(query);
    });

    // Mock "Remote" Results
    if (query.length > 2) {
        if ('alice'.includes(query)) filtered.push({ title: 'Alice Smith (Contact)', url: 'contacts.html?id=1', icon: 'user', group: 'Contacts' });
        if ('acme'.includes(query)) filtered.push({ title: 'Acme Corp (Company)', url: 'companies.html?id=2', icon: 'building', group: 'Companies' });
    }

    renderCmdResults(filtered);
}

function renderCmdResults(items) {
    cmdResults = items;
    cmdSelectedIndex = 0;

    if (items.length === 0) {
        cmdResultsContainer.innerHTML = '<div style="padding:12px;text-align:center;color:#94a3b8;">No results found</div>';
        return;
    }

    var html = '';
    var lastGroup = '';

    items.forEach(function (item, index) {
        if (item.group && item.group !== lastGroup) {
            html += `<div class="cmd-group-title">${item.group}</div>`;
            lastGroup = item.group;
        }

        var activeClass = index === 0 ? 'selected' : '';
        html += `
        <div class="cmd-item ${activeClass}" data-index="${index}" onclick="cmdSelectItem(${index})">
            <div class="cmd-item-icon"><i data-lucide="${item.icon}" width="18"></i></div>
            <div class="cmd-item-text">${item.title}</div>
            ${index === 0 ? '<i data-lucide="corner-down-left" width="14" style="opacity:0.5"></i>' : ''}
        </div>`;
    });

    cmdResultsContainer.innerHTML = html;

    // Re-run icons for new content
    if (window.lucide) window.lucide.createIcons();
}

function handleCmdNavigation(e) {
    if (!cmdResults.length) return;

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        cmdSelectedIndex = (cmdSelectedIndex + 1) % cmdResults.length;
        updateCmdSelection();
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        cmdSelectedIndex = (cmdSelectedIndex - 1 + cmdResults.length) % cmdResults.length;
        updateCmdSelection();
    } else if (e.key === 'Enter') {
        e.preventDefault();
        cmdSelectItem(cmdSelectedIndex);
    }
}

function updateCmdSelection() {
    var items = cmdResultsContainer.querySelectorAll('.cmd-item');
    items.forEach(function (el) { el.classList.remove('selected'); });

    var selected = items[cmdSelectedIndex];
    if (selected) {
        selected.classList.add('selected');
        selected.scrollIntoView({ block: 'nearest' });
    }
}

function cmdSelectItem(index) {
    var item = cmdResults[index];
    if (item) {
        window.location.href = item.url;
        closeCommandPalette();
    }
}

// Make global
window.openCommandPalette = openCommandPalette;
