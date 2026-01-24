document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    const root = document.documentElement;
    const icon = toggleBtn.querySelector('span');

    // 1. Check Local Storage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        root.setAttribute('data-theme', 'light');
        icon.textContent = '🌙'; // Moon icon for switching BACK to dark
    } else {
        icon.textContent = '☀️'; // Sun icon for switching TO light
    }

    // 2. Toggle Logic
    toggleBtn.addEventListener('click', () => {
        const currentTheme = root.getAttribute('data-theme');
        
        if (currentTheme === 'light') {
            // Switch to Dark
            root.removeAttribute('data-theme');
            localStorage.setItem('theme', 'dark');
            icon.textContent = '☀️';
        } else {
            // Switch to Light
            root.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            icon.textContent = '🌙';
        }
    });
});
