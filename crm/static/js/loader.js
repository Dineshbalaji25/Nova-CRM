/**
 * App Loader
 * Fetches base.html and merges the current page content into it.
 * Simulates Server-Side Includes on the Client Side.
 */

(async function initApp() {
    // 1. Identify Current Page Content
    const pageContent = document.getElementById('content-area');
    const pageTitle = document.title;
    const pageCss = document.getElementById('page-specific-css')?.href;

    if (!pageContent) {
        console.warn('No #content-area found. Skipping layout load.');
        return;
    }

    try {
        // 2. Fetch Base Layout
        // Django serves base.html at /pages/base.html
        const response = await fetch('/pages/base.html');
        if (!response.ok) throw new Error('Failed to load base.html');
        const baseHtml = await response.text();

        // 3. Parse Base Layout
        const parser = new DOMParser();
        const doc = parser.parseFromString(baseHtml, 'text/html');

        // 4. Inject Page Content
        const slot = doc.getElementById('app-slot');
        slot.innerHTML = pageContent.innerHTML;

        // 5. Update Title & CSS
        doc.title = pageTitle;
        const cssLink = doc.getElementById('page-css');
        if (pageCss && cssLink) {
            cssLink.href = pageCss;
        } else if (cssLink) {
            cssLink.remove();
        }

        // 6. Highlight Active Nav Item
        // Check pathname: /dashboard -> nav-dashboard
        let currentPath = window.location.pathname.split('/').pop().replace('.html', '');
        if (!currentPath || currentPath === '/') currentPath = 'dashboard';

        const navId = 'nav-' + currentPath;
        const activeNav = doc.getElementById(navId);
        if (activeNav) activeNav.classList.add('active');

        // 7. Replace Document
        document.documentElement.innerHTML = doc.documentElement.innerHTML;

        // 8. Re-execute Scripts (innerHTML scripts don't run by default)
        // We need to re-run Lucide and any page specific scripts
        if (window.lucide) window.lucide.createIcons();

        // Load Command Palette
        const cmdScript = document.createElement('script');
        cmdScript.src = '../assets/js/command-palette.js';
        document.body.appendChild(cmdScript);

        // Run any scripts that were in the original content-area
        const scripts = document.querySelectorAll('#app-slot script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });

    } catch (e) {
        console.error('Layout Loader Error:', e);
        // Fallback: Show content as is
        document.body.style.display = 'block';
    }
})();
