document.addEventListener('DOMContentLoaded', async () => {
    // Shared Search Index
    let searchIndex = [];
    
    try {
        // Handle different path depths (root vs sub-pages)
        const path = typeof SEARCH_INDEX_PATH !== 'undefined' ? SEARCH_INDEX_PATH : 'search.json';
        const response = await fetch(path);
        searchIndex = await response.json();
    } catch (error) {
        console.error("Could not load search index:", error);
    }

    class SearchController {
        constructor(inputId, resultsId, isGlobal = false) {
            this.input = document.getElementById(inputId);
            this.results = document.getElementById(resultsId);
            this.isGlobal = isGlobal;
            this.selectedIndex = -1;
            
            if (this.input && this.results) this.init();
        }

        init() {
            // Placeholder logic: Show "Search RISC-V..." if inside that section
            if (typeof CURRENT_ARCH !== 'undefined' && CURRENT_ARCH && !this.isGlobal) {
                this.input.placeholder = `Search ${CURRENT_ARCH} instructions...`;
            }

            this.input.addEventListener('input', (e) => this.handleInput(e));
            
            // Close on click outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest(`#${this.input.id}`) && !e.target.closest(`#${this.results.id}`)) {
                    this.results.style.display = 'none';
                }
            });
        }

        handleInput(e) {
            const query = e.target.value.toLowerCase().trim();
            this.selectedIndex = -1;

            if (query.length < 2) {
                this.results.style.display = 'none';
                return;
            }

            // Filter Logic
            let pool = searchIndex;
            // Only filter by Arch if we are NOT the global/hero search
            if (!this.isGlobal && typeof CURRENT_ARCH !== 'undefined' && CURRENT_ARCH) {
                pool = searchIndex.filter(item => item.arch === CURRENT_ARCH);
            }

            // Fuzzy-ish Match: Check if all typed terms exist in label or summary
            const terms = query.split(" ").filter(t => t);
            const results = pool.filter(item => {
                const text = `${item.label} ${item.mnemonic} ${item.summary}`.toLowerCase();
                return terms.every(term => text.includes(term));
            });

            this.render(results);
        }

        render(results) {
            this.results.innerHTML = '';
            if (results.length > 0) {
                this.results.style.display = 'block';
                // Show max 10 results
                results.slice(0, 10).forEach((result, index) => {
                    const div = document.createElement('div');
                    div.className = 'search-result-item';
                    
                    // Fix pathing for links
                    let basePath = typeof SEARCH_INDEX_PATH !== 'undefined' ? SEARCH_INDEX_PATH.replace('search.json', '') : './';
                    if (this.isGlobal) basePath = ""; // Hero search is always at root

                    div.innerHTML = `
                        <a href="${basePath}${result.url}" style="text-decoration: none; color: inherit;">
                            <div class="result-title">
                                ${result.label} 
                                <span class="badge" style="font-size: 0.7em; opacity: 0.7;">${result.arch}</span>
                            </div>
                            <div class="result-summary">${result.summary}</div>
                        </a>
                    `;
                    this.results.appendChild(div);
                });
            } else {
                this.results.style.display = 'none';
            }
        }
    }

    // Initialize Controllers
    // 1. Navigation Bar Search
    new SearchController('search-input', 'search-results'); 
    
    // 2. Homepage Hero Search
    new SearchController('hero-search', 'hero-results', true); 
});
