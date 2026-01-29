document.addEventListener('DOMContentLoaded', () => {
    
    // --- Copy Button Logic ---
    document.querySelectorAll('.code-block').forEach(block => {
        // Create button
        const button = document.createElement('button');
        button.className = 'copy-btn';
        button.innerText = 'Copy';
        
        button.addEventListener('click', () => {
            const code = block.querySelector('code, pre')?.innerText || block.innerText;
            navigator.clipboard.writeText(code).then(() => {
                button.innerText = 'Copied!';
                setTimeout(() => button.innerText = 'Copy', 2000);
            });
        });
        
        // Add to block (ensure relative positioning in CSS)
        if (getComputedStyle(block).position === 'static') {
            block.style.position = 'relative';
        }
        block.appendChild(button);
    });

    // --- Sidebar Filter Logic ---
    const sidebarInput = document.getElementById('sidebar-filter');
    if (sidebarInput) {
        sidebarInput.addEventListener('input', (e) => {
            const filter = e.target.value.toLowerCase();
            const links = document.querySelectorAll('.sidebar-list a');
            
            links.forEach(link => {
                if (link.innerText.toLowerCase().includes(filter)) {
                    link.style.display = 'block';
                } else {
                    link.style.display = 'none';
                }
            });
        });
    }

    // --- Sort Table Logic ---
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const index = Array.from(th.parentNode.children).indexOf(th);
            const isAsc = th.dataset.order !== 'asc';
            
            rows.sort((a, b) => {
                const aText = a.children[index].innerText.toLowerCase();
                const bText = b.children[index].innerText.toLowerCase();
                return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
            });
            
            rows.forEach(row => tbody.appendChild(row));
            
            // Update icons/state
            table.querySelectorAll('th').forEach(h => {
                h.dataset.order = '';
                h.style.color = '';
            });
            th.dataset.order = isAsc ? 'asc' : 'desc';
            th.style.color = 'var(--accent)'; // Highlight active sort
        });
    });

    // --- Extension Filter Logic ---
    const extFilter = document.getElementById('extension-filter');
    if (extFilter) {
        extFilter.addEventListener('change', (e) => {
            const filter = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');
            
            rows.forEach(row => {
                // Check both the specific data attribute and the raw text for flexibility
                const extData = (row.dataset.extension || '').toLowerCase();
                const rawText = row.innerText.toLowerCase();
                
                // If filter matches data-attribute OR is found in text (like "Vector" in Summary)
                if (filter === "" || extData.includes(filter) || rawText.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // --- Auto-add Anchor Links to Headers ---
    document.querySelectorAll('.panel h3').forEach(header => {
        header.style.position = 'relative';
        header.style.cursor = 'pointer';
        
        const anchor = document.createElement('span');
        anchor.innerHTML = '#';
        anchor.style.position = 'absolute';
        anchor.style.left = '-20px';
        anchor.style.opacity = '0';
        anchor.style.color = 'var(--accent)';
        anchor.style.transition = 'opacity 0.2s';
        
        header.appendChild(anchor);
        
        // Generate ID if missing
        if (!header.id) {
            header.id = header.innerText.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        }
        
        header.addEventListener('mouseenter', () => anchor.style.opacity = '1');
        header.addEventListener('mouseleave', () => anchor.style.opacity = '0');
        header.addEventListener('click', () => {
            window.location.hash = header.id;
            navigator.clipboard.writeText(window.location.href);
        });
    });

});
