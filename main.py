import os
import sys
import random
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
TOKEN = "8336283371:AAFBn6_zGinLTfkr194RNaHCyEKUhifozWw"
OWNER_ID = 7806950316

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# --- ИНИЦИАЛИЗАЦИЯ И РАБОТА С БАЗОЙ ДАННЫХ SQLite ---
DB_PATH = "database.db"

def init_db():
    """Создает локальную базу данных и таблицу пользователей, если их нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 100000,
            bank INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def load_user(user_id: int, username: str = "Игрок") -> dict:
    """Загружает игрока из локальной БД. Если его нет — регистрирует."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, balance, bank, banned, is_admin FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        conn.close()
        return {
            "id": row[0],
            "username": row[1],
            "balance": row[2],
            "bank": row[3],
            "banned": bool(row[4]),
            "is_admin": bool(row[5])
        }
    
    # Регистрация нового игрока с 100к баланса
    cursor.execute(
        "INSERT INTO users (id, username, balance, bank, banned, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, 100000, 0, 0, 0)
    )
    conn.commit()
    conn.close()
    return {"id": user_id, "username": username, "balance": 100000, "bank": 0, "banned": False, "is_admin": False}

def update_funds(user_id: int, balance: int, bank: int):
    """Обновляет баланс и банк игрока"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ?, bank = ? WHERE id = ?", (balance, bank, user_id))
    conn.commit()
    conn.close()

# Вызываем создание базы при старте скрипта
init_db()

# --- СОСТОЯНИЯ FSM ---
class GameStates(StatesGroup):
    bet_mines = State()
    bet_roulette = State()
    bet_casino = State()
    bank_deposit = State()
    bank_withdraw = State()

# --- КЛАВИАТУРЫ ---
def get_main_menu(user_id: int) -> InlineKeyboardMarkup:
    u = load_user(user_id)
    kb = [
        [InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"), InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette")],
        [InlineKeyboardButton(text="🎰 Казино (Кости)", callback_data="game_casino"), InlineKeyboardButton(text="🎯 Дартс", callback_data="game_darts")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="🏦 Банк", callback_data="bank_menu")],
    ]
    if u["is_admin"] or user_id == OWNER_ID:
        kb.append([InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТЧИКИ ---

@router.message(Command("start"))
async def cmd_start(message: Message):
    load_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n"
        f"💰 Твой стартовый баланс: **100 000 💵**\n"
        f"Выбирай игру или открой профиль 👇", 
        reply_markup=get_main_menu(message.from_user.id), 
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🎮 Главное меню бота. Выберите действие:", reply_markup=get_main_menu(call.from_user.id))

# --- ПРОФИЛЬ И БЫСТРЫЙ БАЛАНС "Б" ---

@router.message(F.text.lower().in_({"б", "баланс"}))
async def quick_balance(message: Message):
    u = load_user(message.from_user.id)
    await message.answer(f"💰 Ваш текущий баланс: **{u['balance']:,} 💵**", parse_mode="Markdown")

@router.message(F.text.lower() == "профиль")
@router.callback_query(F.data == "profile")
async def show_profile(event: Message | CallbackQuery):
    user_id = event.from_user.id
    name = event.from_user.full_name
    u = load_user(user_id, name)
    
    text = (
        f"👤 **Ваш игровой профиль**\n\n"
        f"👤 Имя: {name}\n"
        f"🆔 TG ID: `{user_id}`\n"
        f"💰 Баланс на руках: **{u['balance']:,} 💵**\n"
        f"🏦 В Банке: **{u['bank']:,} 💵**"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Меню", callback_data="to_menu")]])
    
    if isinstance(event, Message): 
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else: 
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- СИСТЕМА БАНКА ---

@router.callback_query(F.data == "bank_menu")
async def bank_main(call: CallbackQuery):
    u = load_user(call.from_user.id)
    text = f"🏦 **Управление Банком**\n\n💵 На руках: {u['balance']:,} 💵\n💳 В банке: {u['bank']:,} 💵"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Положить", callback_data="bank_dep"), InlineKeyboardButton(text="📤 Снять", callback_data="bank_with")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="to_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "bank_dep")
async def bank_deposit_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📥 Введите сумму, которую хотите перевести в банк:")
    await state.set_state(GameStates.bank_deposit)

@router.message(GameStates.bank_deposit)
async def bank_deposit_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["balance"]: 
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма или недостаточно наличных.")
        return
    
    update_funds(message.from_user.id, u["balance"] - amount, u["bank"] + amount)
    await message.answer(f"✅ Успешно положено в банк: **{amount:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")

@router.callback_query(F.data == "bank_with")
async def bank_withdraw_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📤 Введите сумму, которую хотите снять из банка:")
    await state.set_state(GameStates.bank_withdraw)

@router.message(GameStates.bank_withdraw)
async def bank_withdraw_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["bank"]: 
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма или в банке нет столько денег.")
        return
        
    update_funds(message.from_user.id, u["balance"] + amount, u["bank"] - amount)
    await message.answer(f"✅ Успешно снято из банка: **{amount:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")


# --- ИГРЫ ---

# 1. МИНЫ
@router.callback_query(F.data == "game_mines")
async def mines_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("💣 **ИГРА МИНЫ**\n\nВведите сумму вашей ставки:")
    await state.set_state(GameStates.bet_mines)

@router.message(GameStates.bet_mines)
async def mines_play(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        bet = int(message.text)
        if bet <= 0 or bet > u["balance"]: raise ValueError
    except ValueError:
        await message.answer("❌ Неверная ставка.")
        return

    if random.random() > 0.4:
        win = int(bet * 1.5)
        update_funds(message.from_user.id, u["balance"] + (win - bet), u["bank"])
        await message.answer(f"💎 Вы обошли все мины!\n🎉 Выигрыш: **+{win:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"💥 БУМ! Вы подорвались.\n📉 Потеряно: **-{bet:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")

# 2. РУЛЕТКА
@router.callback_query(F.data == "game_roulette")
async def roulette_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🎡 **РУЛЕТКА**\n\nВведите ставку:")
    await state.set_state(GameStates.bet_roulette)

@router.message(GameStates.bet_roulette)
async def roulette_play(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        bet = int(message.text)
        if bet <= 0 or bet > u["balance"]: raise ValueError
    except ValueError:
        await message.answer("❌ Неверная ставка.")
        return

    colors = ["🔴 КРАСНОЕ", "⚫ ЧЕРНОЕ", "🟢 ЗЕРО"]
    result = random.choices(colors, weights=[48, 48, 4], k=1)[0]
    
    if result != "🟢 ЗЕРО" and random.choice([True, False]):
        win = bet * 2
        update_funds(message.from_user.id, u["balance"] + bet, u["bank"])
        await message.answer(f"🎡 Результат: **{result}**\n🎉 Выигрыш: **+{win:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"🎡 Результат: **{result}**\n📉 Проигрыш: **-{bet:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")

# 3. КАЗИНО (КОСТИ)
@router.callback_query(F.data == "game_casino")
async def casino_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🎰 **КАЗИНО (КУБИКИ)**\n\nВведите ставку:")
    await state.set_state(GameStates.bet_casino)

@router.message(GameStates.bet_casino)
async def casino_play(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        bet = int(message.text)
        if bet <= 0 or bet > u["balance"]: raise ValueError
    except ValueError:
        await message.answer("❌ Неверная ставка.")
        return

    user_score = random.randint(1, 6) + random.randint(1, 6)
    bot_score = random.randint(1, 6) + random.randint(1, 6)
    
    if user_score > bot_score:
        update_funds(message.from_user.id, u["balance"] + bet, u["bank"])
        await message.answer(f"🎰 Твои очки: **{user_score}**\n🎲 Дилер: **{bot_score}**\n\n🎉 Вы победили! Выигрыш: **+{bet*2:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")
    elif user_score < bot_score:
        update_funds(message.from_user.id, u["balance"] - bet, u.get("bank", 0))
        await message.answer(f"🎰 Твои очки: **{user_score}**\n🎲 Дилер: **{bot_score}**\n\n📉 Проигрыш: **-{bet:,} 💵**", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")
    else:
        await message.answer(f"🤝 Ничья (**{user_score}** стабильно)! Ставка возвращена.", reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")

# 4. ДАРТС
@router.callback_query(F.data == "game_darts")
async def play_darts(call: CallbackQuery):
    u = load_user(call.from_user.id)
    bet = 5000
    if u["balance"] < bet:
        await call.answer("❌ Минимальная ставка 5,000 💵!", show_alert=True)
        return

    msg = await call.message.answer_darts()
    value = msg.darts.value
    await asyncio.sleep(4)
    
    if value >= 4:
        update_funds(call.from_user.id, u["balance"] + bet, u["bank"])
        await msg.reply(f"🎯 Попадание: {value}/6.\n🎉 Приз: **+{bet*2:,} 💵**", reply_markup=get_main_menu(call.from_user.id), parse_mode="Markdown")
    else:
        update_funds(call.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"💨 Слабо ({value}/6).\n📉 Минус **{bet:,} 💵**", reply_markup=get_main_menu(call.from_user.id), parse_mode="Markdown")


# --- СТАРТ ЛУПА ---
async def main():
    dp.include_router(router)
    print("🚀 Бот переведен на SQLite! Больше никаких внешних баз данных.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
            
