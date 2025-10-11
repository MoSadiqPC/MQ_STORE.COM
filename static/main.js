document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Logic
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const body = document.body;
        function setTheme(theme) {
            body.classList.toggle('light-mode', theme === 'light');
            themeToggle.textContent = theme === 'light' ? '🌙' : '☀️';
            localStorage.setItem('theme', theme);
        }
        themeToggle.addEventListener('click', () => { setTheme(body.classList.contains('light-mode') ? 'dark' : 'light'); });
        setTheme(localStorage.getItem('theme') || 'dark');
    }

    // Language Toggle Logic
    const langToggle = document.getElementById('lang-toggle');
    if(langToggle){
        function setLang(lang){
            document.body.classList.toggle('lang-ar', lang === 'ar');
            langToggle.textContent = lang === 'ar' ? 'En' : 'ع';
            localStorage.setItem('lang', lang);
        }
        langToggle.addEventListener('click', () => { setLang(document.body.classList.contains('lang-ar') ? 'en' : 'ar'); });
        setLang(localStorage.getItem('lang') || 'en');
    }

    // Live Clock Logic
    const clockElement = document.getElementById('live-clock');
    if (clockElement) {
        function updateClock() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            const dateString = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
            clockElement.innerHTML = `<span>${timeString}</span><span>${dateString}</span>`;
        }
        updateClock(); setInterval(updateClock, 1000);
    }

    // Countdown Logic for Reveal Page
    const countdownElement = document.getElementById('countdown');
    if (countdownElement) {
        let seconds = 10;
        const countdownSection = document.getElementById('countdownSection');
        const loginForm = document.getElementById('loginForm');
        const timer = setInterval(() => {
            seconds--;
            countdownElement.textContent = seconds;
            if (seconds <= 0) {
                clearInterval(timer);
                if (countdownSection) countdownSection.style.display = 'none';
                if (loginForm) loginForm.style.display = 'block';
            }
        }, 1000);
    }
});