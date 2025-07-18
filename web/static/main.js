// Передача переменной IS_AUTHORIZED из шаблона происходит в index.html

function showMessage(text, type) {
    const existingMsg = document.querySelector('.msg');
    if (existingMsg) {
        existingMsg.remove();
    }
    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg' + (type === 'error' ? ' error' : '');
    msgDiv.textContent = text;
    const container = document.querySelector('.container');
    const statusDiv = document.querySelector('.status');
    container.insertBefore(msgDiv, statusDiv.nextSibling);
    setTimeout(() => {
        if (msgDiv.parentNode) {
            msgDiv.remove();
        }
    }, 3000);
}

function onAuthRequired(event) {
    if (!window.IS_AUTHORIZED) {
        showMessage('Пожалуйста, авторизуйтесь через Telegram для использования этой функции.', 'error');
        event.preventDefault();
        return false;
    }
    return true;
}

function sendManualNotification(event) {
    if (!onAuthRequired(event)) return false;
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Отправка...';
    button.disabled = true;
    fetch('/api/notify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Уведомление отправлено!', 'success');
        } else {
            showMessage('Ошибка отправки: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    })
    .catch(error => {
        showMessage('Ошибка сети: ' + error.message, 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
    return false;
}

function sendDanyaWakeup(event) {
    if (!onAuthRequired(event)) return false;
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Отправка...';
    button.disabled = true;
    fetch('/api/user1', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Сообщение отправлено!', 'success');
        } else {
            showMessage('Ошибка отправки: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    })
    .catch(error => {
        showMessage('Ошибка сети: ' + error.message, 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
    return false;
}

function sendLizaWakeup(event) {
    if (!onAuthRequired(event)) return false;
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Отправка...';
    button.disabled = true;
    fetch('/api/user2', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Сообщение отправлено!', 'success');
        } else {
            showMessage('Ошибка отправки: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    })
    .catch(error => {
        showMessage('Ошибка сети: ' + error.message, 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
    return false;
}

function sendDynamicButton(event, idx) {
    if (!onAuthRequired(event)) return false;
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Отправка...';
    button.disabled = true;
    fetch(`/api/button/${idx}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Сообщение отправлено!', 'success');
        } else {
            showMessage('Ошибка отправки: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    })
    .catch(error => {
        showMessage('Ошибка сети: ' + error.message, 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
    return false;
}

// Тёмная/светлая тема + логотип
const btn = document.getElementById('theme-toggle');
const logoImg = document.getElementById('logo-img');
function updateLogo() {
  if (document.body.classList.contains('dark')) {
    logoImg.src = '/static/logo_dark.png';
  } else {
    logoImg.src = '/static/logo_light.png';
  }
}
btn.onclick = function() {
  document.body.classList.toggle('dark');
  btn.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  updateLogo();
};
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
  btn.textContent = '☀️';
}
updateLogo(); 