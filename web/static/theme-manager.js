// Универсальный менеджер тёмной темы для всех страниц

class ThemeManager {
    constructor() {
        this.themeToggleBtn = document.getElementById('theme-toggle');
        this.logoImg = document.getElementById('logo-img');
        this.init();
    }

    init() {
        // Применяем сохранённую тему при загрузке страницы
        // Если тема не сохранена, применяем светлую по умолчанию
        if (!localStorage.getItem('theme')) {
            localStorage.setItem('theme', 'light');
        }
        this.applyTheme();
        
        // Настраиваем обработчик клика для кнопки переключения
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
        }
    }

    applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        // По умолчанию применяем светлую тему, если не сохранена тёмная
        if (savedTheme === 'dark') {
            document.body.classList.add('dark');
            // Применяем тёмный фон для html и body
            this.applyDarkBackground();
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '☀️';
            }
        } else {
            document.body.classList.remove('dark');
            // Применяем светлый фон для html и body
            this.applyLightBackground();
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
            // Применяем светлый фон
            this.applyLightBackground();
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '🌙';
            }
        } else {
            document.body.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            // Применяем тёмный фон
            this.applyDarkBackground();
            if (this.themeToggleBtn) {
                this.themeToggleBtn.textContent = '☀️';
            }
        }
        
        this.updateLogo();
    }

    applyLightBackground() {
        // Светлый градиентный фон для всех страниц
        if (!document.body.classList.contains('landing')) {
            document.documentElement.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
            document.body.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
        }
    }

    applyDarkBackground() {
        // Тёмный фон для всех страниц
        if (!document.body.classList.contains('landing')) {
            document.documentElement.style.background = '#0b1220';
            document.body.style.background = 'linear-gradient(180deg, #0b1220 0%, #0b1220 100%)';
        }
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