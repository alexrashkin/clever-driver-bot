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
        
        // Принудительно применяем светлую тему при первой загрузке
        this.applyTheme();
        
        // Дополнительно применяем светлый фон для всех страниц
        if (localStorage.getItem('theme') !== 'dark') {
            this.applyLightBackground();
            
            // Принудительно применяем светлую тему для всех элементов с тёмным фоном
            setTimeout(() => {
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.style.background || el.style.backgroundColor || el.style.backgroundImage) {
                        const bg = el.style.background || el.style.backgroundColor || el.style.backgroundImage;
                        if (bg.includes('#0b1220') || bg.includes('#1e293b') || bg.includes('#334155') || 
                            bg.includes('#020617') || bg.includes('#0f172a') || bg.includes('#0a0a0a') ||
                            bg.includes('rgb(11, 18, 32)') || bg.includes('rgb(30, 41, 59)') || 
                            bg.includes('rgb(51, 65, 85)') || bg.includes('rgb(2, 6, 23)') || 
                            bg.includes('rgb(15, 23, 42)') || bg.includes('rgb(10, 10, 10)')) {
                            el.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                            el.style.backgroundColor = '#f0f9ff';
                            el.style.backgroundImage = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                        }
                    }
                });
            }, 100);
        }
        
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
            
            // Принудительно применяем светлую тему для всех элементов с тёмным фоном
            setTimeout(() => {
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.style.background || el.style.backgroundColor || el.style.backgroundImage) {
                        const bg = el.style.background || el.style.backgroundColor || el.style.backgroundImage;
                        if (bg.includes('#0b1220') || bg.includes('#1e293b') || bg.includes('#334155') || 
                            bg.includes('#020617') || bg.includes('#0f172a') || bg.includes('#0a0a0a')) {
                            el.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                            el.style.backgroundColor = '#f0f9ff';
                            el.style.backgroundImage = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                        }
                    }
                });
            }, 100);
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
            
            // Принудительно применяем светлую тему для всех элементов с тёмным фоном
            setTimeout(() => {
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.style.background || el.style.backgroundColor || el.style.backgroundImage) {
                        const bg = el.style.background || el.style.backgroundColor || el.style.backgroundImage;
                        if (bg.includes('#0b1220') || bg.includes('#1e293b') || bg.includes('#334155') || 
                            bg.includes('#020617') || bg.includes('#0f172a') || bg.includes('#0a0a0a') ||
                            bg.includes('rgb(11, 18, 32)') || bg.includes('rgb(30, 41, 59)') || 
                            bg.includes('rgb(51, 65, 85)') || bg.includes('rgb(2, 6, 23)') || 
                            bg.includes('rgb(15, 23, 42)') || bg.includes('rgb(10, 10, 10)')) {
                            el.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                            el.style.backgroundColor = '#f0f9ff';
                            el.style.backgroundImage = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                        }
                    }
                });
            }, 100);
            
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
        // Светлый градиентный фон для всех страниц, включая главную
        document.documentElement.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
        document.body.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
        
        // Принудительно применяем светлую тему для всех элементов
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            if (el.style.background || el.style.backgroundColor || el.style.backgroundImage) {
                const bg = el.style.background || el.style.backgroundColor || el.style.backgroundImage;
                if (bg.includes('#0b1220') || bg.includes('#1e293b') || bg.includes('#334155') || 
                    bg.includes('#020617') || bg.includes('#0f172a') || bg.includes('#0a0a0a') ||
                    bg.includes('rgb(11, 18, 32)') || bg.includes('rgb(30, 41, 59)') || 
                    bg.includes('rgb(51, 65, 85)') || bg.includes('rgb(2, 6, 23)') || 
                    bg.includes('rgb(15, 23, 42)') || bg.includes('rgb(10, 10, 10)')) {
                    el.style.background = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                    el.style.backgroundColor = '#f0f9ff';
                    el.style.backgroundImage = 'linear-gradient(135deg, #e0f2fe, #f0f9ff)';
                }
            }
        });
    }

    applyDarkBackground() {
        // Тёмный фон для всех страниц, включая главную
        document.documentElement.style.background = '#0b1220';
        document.body.style.background = 'linear-gradient(180deg, #0b1220 0%, #0b1220 100%)';
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