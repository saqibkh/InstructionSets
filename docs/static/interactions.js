document.addEventListener('DOMContentLoaded', () => {
    // 1. Interactive Bit-Field Highlighting
    const bitBoxes = document.querySelectorAll('.bit-box');
    const operandRows = document.querySelectorAll('.operand-row');

    const tooltip = document.getElementById('bit-tooltip');

    function highlight(name, active) {
        let descText = "";

        // 1. Highlight Bit Boxes
        bitBoxes.forEach(box => {
            if (box.dataset.op === name) {
                if(active) box.classList.add('highlight');
                else box.classList.remove('highlight');
            }
        });

        // 2. Highlight Operand Rows & Grab Description
        operandRows.forEach(row => {
            if (row.dataset.op === name) {
                if(active) {
                    row.classList.add('highlight');
                    // Grab the description from the second span in the row
                    const descSpan = row.querySelectorAll('span')[1]; 
                    if (descSpan) descText = descSpan.innerText;
                } else {
                    row.classList.remove('highlight');
                }
            }
        });

        // 3. Update Tooltip
        if (tooltip) {
            if (active) {
                // If we found a description in operands, use it. 
                // Otherwise, check if it looks like a fixed binary value (0/1) or Hex
                if (descText) {
                    tooltip.innerText = `${name}: ${descText}`;
                    tooltip.style.opacity = '1';
                } else if (/^[01]+$/.test(name)) {
                    tooltip.innerText = "Fixed Opcode Bits";
                    tooltip.style.opacity = '1';
                } else {
                    // Fallback for things like 'opcode' or 'func3' that aren't operands
                    tooltip.innerText = name; 
                    tooltip.style.opacity = '1';
                }
            } else {
                tooltip.style.opacity = '0';
            }
        }
    }

    // Attach events to Bit Boxes
    bitBoxes.forEach(box => {
        if(box.dataset.op) { // Only if it has a name
            box.addEventListener('mouseenter', () => highlight(box.dataset.op, true));
            box.addEventListener('mouseleave', () => highlight(box.dataset.op, false));
        }
    });

    // Attach events to Operand Rows
    operandRows.forEach(row => {
        if(row.dataset.op) {
            row.addEventListener('mouseenter', () => highlight(row.dataset.op, true));
            row.addEventListener('mouseleave', () => highlight(row.dataset.op, false));
        }
    });

    // --- New: Copy to Clipboard Logic ---
    document.querySelectorAll('.code-block').forEach(block => {
        // 1. Create the button
        const button = document.createElement('button');
        button.className = 'copy-btn';
        button.innerHTML = '📋';
        button.ariaLabel = 'Copy code';
        
        // 2. Add click handler
        button.addEventListener('click', () => {
            navigator.clipboard.writeText(block.innerText.trim());
            
            // Visual feedback
            const originalText = button.innerHTML;
            button.innerHTML = '✅';
            setTimeout(() => button.innerHTML = originalText, 2000);
        });

        // 3. Append to the block
        block.style.position = 'relative';
        block.appendChild(button);
    });

    // --- Sidebar Filter Logic ---
    const sidebarFilter = document.getElementById('sidebar-filter');
    if (sidebarFilter) {
        sidebarFilter.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            
            // 1. Filter individual links
            document.querySelectorAll('.group-links a').forEach(link => {
                const text = link.innerText.toLowerCase();
                link.style.display = text.includes(term) ? 'block' : 'none';
            });

            // 2. Hide empty groups (accordions)
            document.querySelectorAll('.nav-group').forEach(group => {
                const visibleLinks = group.querySelectorAll('.group-links a[style="display: block"]');
                const summaryText = group.querySelector('summary').innerText.toLowerCase();
                
                // If filter is empty, show everything.
                if (term === "") {
                    group.style.display = 'block';
                } 
                // If the Group Name matches OR it has visible children, show it.
                else {
                    const matchesGroup = summaryText.includes(term);
                    const hasChildren = visibleLinks.length > 0;
                    
                    if (matchesGroup || hasChildren) {
                        group.style.display = 'block';
                        // Auto-expand if searching
                        if (!matchesGroup && hasChildren) group.open = true;
                    } else {
                        group.style.display = 'none';
                    }
                }
            });
        });
    }

    // Auto-add anchor links to headers
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

    // --- Table Sorting Logic ---
    document.querySelectorAll('th').forEach((th, index) => {
        th.style.cursor = 'pointer';
        th.title = "Click to sort";
        
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAsc = th.dataset.order !== 'asc'; // Toggle sort order
            
            // Sort rows based on the text content of the clicked column
            rows.sort((a, b) => {
                const cellA = a.children[index].innerText.toLowerCase().trim();
                const cellB = b.children[index].innerText.toLowerCase().trim();
                
                return isAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            });

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
            
            // Reset other headers and update indicator
            table.querySelectorAll('th').forEach(h => {
                h.dataset.order = '';
                h.style.color = ''; // Reset color
            });
	    th.dataset.order = isAsc ? 'asc' : 'desc';
            th.style.color = 'var(--accent)'; // Highlight active sort
        });
    });

    // --- ADD THIS BLOCK ---
    const extFilter = document.getElementById('extension-filter');
    if (extFilter) {
        extFilter.addEventListener('change', (e) => {
            const filter = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');
            
            rows.forEach(row => {
                const extData = (row.dataset.extension || '').toLowerCase();
                const rawText = row.innerText.toLowerCase();
                
                if (filter === "" || extData.includes(filter) || rawText.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    // ---------------------

});
