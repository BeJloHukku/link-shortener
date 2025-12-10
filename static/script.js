const API_BASE = 'http://localhost:8000';

// Элементы DOM
const shortUrlForm = document.getElementById('shortUrlForm');
const customUrlForm = document.getElementById('customUrlForm');
const resultDiv = document.getElementById('result');
const errorDiv = document.getElementById('error');
const resultLink = document.getElementById('resultLink');
const copyBtn = document.getElementById('copyBtn');

// Скрыть результат и ошибку
function hideMessages() {
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
}

// Показать результат
function showResult(url) {
    hideMessages();
    // Убираем слеш если url уже начинается с него
    const slug = url.startsWith('/') ? url.substring(1) : url;
    const fullUrl = `${API_BASE}/${slug}`;
    resultLink.href = fullUrl;
    resultLink.textContent = fullUrl;
    resultDiv.classList.remove('hidden');
}

// Показать ошибку
function showError(message) {
    hideMessages();
    errorDiv.textContent = `Ошибка: ${message}`;
    errorDiv.classList.remove('hidden');
}

// Обработка формы короткой ссылки
shortUrlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const longUrl = document.getElementById('longUrl').value;

    try {
        const response = await fetch(`${API_BASE}/shorten_url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ long_url: longUrl })
        });

        const data = await response.json();

        if (response.ok) {
            showResult(data.data);
            shortUrlForm.reset();
        } else {
            showError(data.detail || 'Не удалось создать короткую ссылку');
        }
    } catch (error) {
        showError('Ошибка подключения к серверу');
    }
});

// Обработка формы пользовательской ссылки
customUrlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const originUrl = document.getElementById('customOriginUrl').value;
    const customUrl = document.getElementById('customSlug').value;

    try {
        const response = await fetch(`${API_BASE}/custom_url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                origin_url: originUrl,
                custom_url: customUrl 
            })
        });

        const data = await response.json();

        if (response.ok) {
            showResult(data.data);
            customUrlForm.reset();
        } else {
            showError(data.detail || 'Не удалось создать пользовательскую ссылку');
        }
    } catch (error) {
        showError('Ошибка подключения к серверу');
    }
});

// Копирование ссылки
copyBtn.addEventListener('click', async () => {
    const url = resultLink.textContent;
    try {
        await navigator.clipboard.writeText(url);
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Скопировано!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    } catch (error) {
        showError('Не удалось скопировать ссылку');
    }
});
