document.addEventListener('DOMContentLoaded', async () => {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    
    // 1. Fetch the Search Index
    let searchIndex = [];
    try {
        const response = await fetch('/search.json'); // Adjust path if hosted in subfolder
        searchIndex = await response.json();
    } catch (error) {
        console.error("Could not load search index:", error);
    }

    // 2. Search Logic
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        resultsContainer.innerHTML = '';
        
        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }

        const results = searchIndex.filter(item => 
            item.label.toLowerCase().includes(query) || 
            item.summary.toLowerCase().includes(query)
        );

        // 3. Render Results
        if (results.length > 0) {
            resultsContainer.style.display = 'block';
            results.slice(0, 8).forEach(result => {
                const div = document.createElement('div');
                div.className = 'search-result-item';
                div.innerHTML = `
                    <a href="/${result.url}">
                        <div class="result-title">${result.label}</div>
                        <div class="result-summary">${result.summary}</div>
                    </a>
                `;
                resultsContainer.appendChild(div);
            });
        } else {
            resultsContainer.style.display = 'none';
        }
    });

    // Close search if clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-wrapper')) {
            resultsContainer.style.display = 'none';
        }
    });
});
