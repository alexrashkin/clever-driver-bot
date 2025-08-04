// Универсальный менеджер тёмной темы для всех страниц

class ThemeManager {
    constructor() {
        this.themeToggleBtn = document.getElementById('theme-toggle');
        this.logoImg = document.getElementById('logo-img');
        this.init();
    }

    init() {
        // Применяем сохранённую тему при загрузке страницы
        this.applyTheme();
        
        // Настраиваем обработчик клика для кнопки переключения
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
        }
    }

    applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark');
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '☀️';
            }
        } else {
            document.body.classList.remove('dark');
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '🌙';
            }
        }
        
        // Обновляем логотип если он есть
        this.updateLogo();
    }

    toggleTheme() {
        const isDark = document.body.classList.contains('dark');
        
        if (isDark) {
            document.body.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '🌙';
            }
        } else {
            document.body.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '☀️';
            }
        }
        
        this.updateLogo();
    }

    updateLogo() {
        if (this.logoImg) {
            if (document.body.classList.contains('dark')) {
                this.logoImg.src = '/static/logo_dark.png';
            } else {
                this.logoImg.src = '/static/logo_light.png';
            }
        }
    }
}

// Инициализируем менеджер темы при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});

// Экспортируем для возможного использования в других скриптах
window.ThemeManager = ThemeManager; 