# Telegram Bot 🤖

Красивый Telegram бот с inline кнопками на Python.

## Функции

- 🎨 Красивый дизайн с эмодзи
- 📱 Inline кнопки для навигации
- ℹ️ Раздел "О нас"
- 🌐 Ссылка на сайт
- 📱 Меню социальных сетей
- 💬 Поддержка через прямую ссылку
- 🔄 Навигация назад

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` (скопируйте из `.env.example`):
```bash
cp .env.example .env
```

3. Получите токен бота у @BotFather и вставьте в `.env`:
```
BOT_TOKEN=your_bot_token_here
```

4. Настройте ссылки в `main.py`:
```python
SOCIAL_LINKS = {
    "website": "https://your-website.com",
    "instagram": "https://instagram.com/your_profile",
    "telegram_channel": "https://t.me/your_channel",
    "vk": "https://vk.com/your_group",
    "youtube": "https://youtube.com/@your_channel",
    "support": "https://t.me/your_support",
}
```

## Запуск

```bash
python main.py
```

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Помощь

## Структура

```
bot/
├── main.py              # Основной файл бота
├── requirements.txt     # Зависимости
├── .env.example        # Пример переменных окружения
└── README.md           # Документация
```
