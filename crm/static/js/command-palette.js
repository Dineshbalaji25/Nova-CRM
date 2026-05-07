/**
 * Nova CRM Command Palette
 * Inspired by Linear (⌘K)
 */

class CommandPalette {
    constructor() {
        this.isOpen = false;
        this.selectedIndex = 0;
        this.commands = [
            { id: 'dash', title: 'Go to Dashboard', icon: 'layout-dashboard', meta: 'Navigation', action: () => window.location.href = '/dashboard' },
            { id: 'cont', title: 'Search Contacts', icon: 'users', meta: 'CRM', action: () => window.location.href = '/contacts' },
            { id: 'comp', title: 'Search Companies', icon: 'building', meta: 'CRM', action: () => window.location.href = '/companies' },
            { id: 'deal', title: 'Pipeline View', icon: 'bar-chart-2', meta: 'Sales', action: () => window.location.href = '/deals' },
            { id: 'task', title: 'My Tasks', icon: 'check-square', meta: 'Productivity', action: () => window.location.href = '/tasks' },
            { id: 'set', title: 'System Settings', icon: 'settings', meta: 'Admin', action: () => window.location.href = '/settings' },
            { id: 'bill', title: 'Billing & Plans', icon: 'credit-card', meta: 'Admin', action: () => window.location.href = '/billing' },
        ];

        this.filteredCommands = [...this.commands];
        this.init();
    }

    init() {
        this.createEl();
        this.bindEvents();
    }

    createEl() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'cmd-overlay';
        this.overlay.innerHTML = `
            <div class="cmd-modal">
                <div class="cmd-input-wrapper">
                    <i data-lucide="search" class="cmd-icon"></i>
                    <input type="text" class="cmd-input" placeholder="Type a command or search..." spellcheck="false">
                </div>
                <div class="cmd-results">
                    <div class="cmd-group-title">Suggestions</div>
                    <div id="cmd-list"></div>
                </div>
                <div class="cmd-footer">
                    <span><span class="kbd-shortcut">↑↓</span> to navigate</span>
                    <span><span class="kbd-shortcut">↵</span> to select</span>
                    <span><span class="kbd-shortcut">esc</span> to close</span>
                </div>
            </div>
        `;
        document.body.appendChild(this.overlay);
        this.input = this.overlay.querySelector('.cmd-input');
        this.listEl = this.overlay.querySelector('#cmd-list');

        if (window.lucide) lucide.createIcons();
    }

    bindEvents() {
        // Toggle with Cmd/Ctrl + K
        window.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
            if (e.key === 'Escape' && this.isOpen) this.close();

            if (this.isOpen) {
                if (e.key === 'ArrowDown') { e.preventDefault(); this.moveSelection(1); }
                if (e.key === 'ArrowUp') { e.preventDefault(); this.moveSelection(-1); }
                if (e.key === 'Enter') { e.preventDefault(); this.executeSelected(); }
            }
        });

        this.input.addEventListener('input', (e) => this.filter(e.target.value));

        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) this.close();
        });
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.overlay.classList.add('active');
        this.input.value = '';
        this.filter('');
        setTimeout(() => this.input.focus(), 10);
    }

    close() {
        this.isOpen = false;
        this.overlay.classList.remove('active');
    }

    filter(query) {
        const q = query.toLowerCase();
        this.filteredCommands = this.commands.filter(c =>
            c.title.toLowerCase().includes(q) || c.meta.toLowerCase().includes(q)
        );
        this.selectedIndex = 0;
        this.render();
    }

    moveSelection(dir) {
        this.selectedIndex += dir;
        if (this.selectedIndex < 0) this.selectedIndex = this.filteredCommands.length - 1;
        if (this.selectedIndex >= this.filteredCommands.length) this.selectedIndex = 0;
        this.render();
    }

    executeSelected() {
        const cmd = this.filteredCommands[this.selectedIndex];
        if (cmd) {
            cmd.action();
            this.close();
        }
    }

    render() {
        this.listEl.innerHTML = this.filteredCommands.map((cmd, i) => `
            <div class="cmd-item ${i === this.selectedIndex ? 'selected' : ''}" data-index="${i}">
                <div class="cmd-item-icon">
                    <i data-lucide="${cmd.icon}"></i>
                </div>
                <div class="cmd-item-text">${cmd.title}</div>
                <div class="cmd-item-meta">${cmd.meta}</div>
            </div>
        `).join('');

        if (window.lucide) lucide.createIcons();

        this.listEl.querySelectorAll('.cmd-item').forEach(el => {
            el.addEventListener('click', () => {
                this.selectedIndex = parseInt(el.dataset.index);
                this.executeSelected();
            });
        });
    }
}

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
    window.cmdPalette = new CommandPalette();
});
