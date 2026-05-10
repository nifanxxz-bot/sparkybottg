import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Конфигурация ссылок
SOCIAL_LINKS = {
    "website": "https://your-website.com",
    "instagram": "https://instagram.com/your_profile",
    "telegram_channel": "https://t.me/your_channel",
    "vk": "https://vk.com/your_group",
    "youtube": "https://youtube.com/@your_channel",
    "support": "https://t.me/your_support",
}


def get_main_keyboard():
    """Главное меню с красивыми кнопками"""
    keyboard = [
        [
            InlineKeyboardButton("ℹ️ О нас", callback_data="about"),
            InlineKeyboardButton("🌐 Наш сайт", url=SOCIAL_LINKS["website"]),
        ],
        [
            InlineKeyboardButton("📱 Наши соц. сети", callback_data="socials"),
            InlineKeyboardButton("💬 Поддержка", url=SOCIAL_LINKS["support"]),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_socials_keyboard():
    """Клавиатура соцсетей"""
    keyboard = [
        [
            InlineKeyboardButton("📷 Instagram", url=SOCIAL_LINKS["instagram"]),
            InlineKeyboardButton("📢 Telegram", url=SOCIAL_LINKS["telegram_channel"]),
        ],
        [
            InlineKeyboardButton("🎵 VK", url=SOCIAL_LINKS["vk"]),
            InlineKeyboardButton("🎥 YouTube", url=SOCIAL_LINKS["youtube"]),
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в наш бот! 🎉

Здесь вы можете:
• 📖 Узнать больше о нас
• 🌐 Посетить наш сайт
• 📱 Подписаться на соц. сети
• 💬 Связаться с поддержкой

Выберите нужный раздел ниже 👇
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'О нас'"""
    query = update.callback_query
    await query.answer()
    
    about_text = """
<b>ℹ️ О нас</b>

🎯 <b>Наша миссия:</b>
Создавать лучшие продукты для наших клиентов

📅 <b>Основаны:</b> 2020 год

👥 <b>Наша команда:</b>
Профессионалы своего дела, готовые помочь вам

🏆 <b>Достижения:</b>
• 10,000+ довольных клиентов
• 5 лет на рынке
• 98% положительных отзывов

📞 <b>Контакты:</b>
Свяжитесь с нами через кнопку "Поддержка"
"""
    
    await query.edit_message_text(
        about_text,
        reply_markup=get_back_keyboard(),
        parse_mode="HTML",
    )


async def socials_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Наши соц. сети'"""
    query = update.callback_query
    await query.answer()
    
    socials_text = """
<b>📱 Наши социальные сети</b>

Подписывайтесь, чтобы быть в курсе:
• 🎁 Акции и скидки
• 📰 Новости и обновления
• 💡 Полезные советы
• 🎉 Конкурсы и розыгрыши

Выберите платформу ниже 👇
"""
    
    await query.edit_message_text(
        socials_text,
        reply_markup=get_socials_keyboard(),
        parse_mode="HTML",
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в наш бот! 🎉

Здесь вы можете:
• 📖 Узнать больше о нас
• 🌐 Посетить наш сайт
• 📱 Подписаться на соц. сети
• 💬 Связаться с поддержкой

Выберите нужный раздел ниже 👇
"""
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
<b>❓ Помощь по боту</b>

Доступные команды:
/start - Начать работу с ботом
/help - Показать это сообщение

Кнопки меню:
ℹ️ О нас - Информация о компании
🌐 Наш сайт - Переход на сайт
📱 Наши соц. сети - Ссылки на соцсети
💬 Поддержка - Написать в поддержку

Если у вас остались вопросы, 
нажмите кнопку "Поддержка" 👇
"""
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


def main() -> None:
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден! Установите его в .env файле")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback кнопки
    application.add_handler(CallbackQueryHandler(about_callback, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(socials_callback, pattern="^socials$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
