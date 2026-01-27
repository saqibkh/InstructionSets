document.addEventListener('DOMContentLoaded', async () => {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    let searchIndex = [];
    let selectedIndex = -1;

    // 1. Fetch Search Index
    try {
        const path = typeof SEARCH_INDEX_PATH !== 'undefined' ? SEARCH_INDEX_PATH : 'search.json';
        const response = await fetch(path);
        searchIndex = await response.json();
    } catch (error) {
        console.error("Could not load search index:", error);
    }

    // 2. Search Logic (Only runs if input exists)
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            selectedIndex = -1;
            
            if (query.length < 2) {
                resultsContainer.style.display = 'none';
                return;
            }

	    // Weighted Search: Score results based on relevance
            const results = searchIndex.map(item => {
                let score = 0;
                const label = item.label.toLowerCase();
                const summary = item.summary.toLowerCase();
                const queryLower = query.toLowerCase();

                // 1. Exact Match (Highest Priority)
                if (label === queryLower || item.label.toLowerCase().startsWith(queryLower + " ")) score += 100;
                // 2. Starts With (High Priority)
                else if (label.startsWith(queryLower)) score += 50;
                // 3. Contains in Mnemonic/Title (Medium Priority)
                else if (label.includes(queryLower)) score += 10;
                // 4. Contains in Summary (Low Priority)
                else if (summary.includes(queryLower)) score += 1;
                
                return { item, score };
            })
            .filter(r => r.score > 0) // Remove non-matches
            .sort((a, b) => b.score - a.score) // Sort by highest score
            .map(r => r.item); // Unwrap back to original item format

            renderResults(results);
        });

        // 3. Keyboard Navigation (Arrows/Enter)
        searchInput.addEventListener('keydown', (e) => {
            const items = resultsContainer.querySelectorAll('.search-result-item');
            if (items.length === 0) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % items.length;
                updateSelection(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                updateSelection(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (selectedIndex >= 0) {
                    items[selectedIndex].querySelector('a').click();
                }
            }
        });
    } // <--- End of if(searchInput)

    // 4. Global Keyboard Shortcut (Ctrl+K) - MOVED OUTSIDE for safety
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault(); 
            const heroInput = document.getElementById('hero-search');
            const navInput = document.getElementById('search-input');

            // Focus hero if visible (homepage), otherwise nav
            if (heroInput && heroInput.offsetParent !== null) {
                heroInput.focus();
            } else if (navInput) {
                navInput.focus();
            }
        }
    });

    function renderResults(results) {
        resultsContainer.innerHTML = '';
        if (results.length > 0) {
            resultsContainer.style.display = 'block';
            results.slice(0, 10).forEach((result, index) => {
                const div = document.createElement('div');
                div.className = 'search-result-item';
                div.innerHTML = `
                    <a href="${typeof SEARCH_INDEX_PATH !== 'undefined' ? SEARCH_INDEX_PATH.replace('search.json', '') : './'}${result.url}">
                        <div class="result-title">${result.label}</div>
                        <div class="result-summary">${result.summary}</div>
                    </a>
                `;
                div.addEventListener('mouseenter', () => {
                    selectedIndex = index;
                    updateSelection(resultsContainer.querySelectorAll('.search-result-item'));
                });
                resultsContainer.appendChild(div);
            });
        } else {
            resultsContainer.style.display = 'none';
        }
    }

    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (searchInput && !e.target.closest('.search-wrapper')) {
            resultsContainer.style.display = 'none';
        }
    });
});
