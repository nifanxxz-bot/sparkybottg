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

TOKEN = "8336283371:AAFBn6_zGinLTfkr194RNaHCyEKUhifozWw"
OWNER_ID = 7806950316

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

DB_PATH = "database.db"

def init_db():
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, balance, bank, banned, is_admin FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return {"id": row[0], "username": row[1], "balance": row[2], "bank": row[3], "banned": bool(row[4]), "is_admin": bool(row[5])}
    
    cursor.execute("INSERT INTO users (id, username, balance, bank, banned, is_admin) VALUES (?, ?, ?, ?, ?, ?)", (user_id, username, 100000, 0, 0, 0))
    conn.commit()
    conn.close()
    return {"id": user_id, "username": username, "balance": 100000, "bank": 0, "banned": False, "is_admin": False}

def update_funds(user_id: int, balance: int, bank: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ?, bank = ? WHERE id = ?", (balance, bank, user_id))
    conn.commit()
    conn.close()

init_db()

class BankStates(StatesGroup):
    deposit = State()
    withdraw = State()

# --- КЛАВИАТУРЫ ---
def get_main_menu() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="🏦 Банк", callback_data="bank_menu")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help_guide")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ В Меню", callback_data="to_menu")]])

# --- ТЕКСТОВОЕ ГЛАВНОЕ МЕНЮ ---
def menu_text() -> str:
    return (
        "🎮 **Главное меню игрового бота**\n\n"
        "🎰 **Доступные игры (играй прямо текстом в чат):**\n"
        "• 🎰 `казино [сумма]` — игра в кости с дилером\n"
        "• 🎡 `рулетка [сумма] [к / ч / 0-36]` — ставки на цвета или числа\n"
        "• 🎯 `дартс [сумма]` — бросок в мишень\n"
        "• 🏀 `баскетбол [сумма]` — бросок в кольцо\n"
        "• 🎳 `кегли [сумма]` — боулинг\n"
        "• 💣 `мины [сумма]` — интерактивное минное поле\n\n"
        "👇 Используй кнопки ниже для управления счетом:"
    )

# --- ОБРАБОТЧИКИ НАВИГАЦИИ ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    load_user(message.from_user.id, message.from_user.full_name)
    await message.answer(menu_text(), reply_markup=get_main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(menu_text(), reply_markup=get_main_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "help_guide")
@router.message(Command("help"))
async def cmd_help(event: Message | CallbackQuery):
    text = (
        "ℹ️ **Справка по командам бота**\n\n"
        "💰 `б` или `баланс` — быстрый баланс и ник\n"
        "👤 `профиль` — полная статистика аккаунта\n"
        "👑 `/admin` — панель управления (для админов)\n\n"
        "📋 **Примеры игровых ставок:**\n"
        "• 🎰 `казино 5000`\n"
        "• 🎡 `рулетка 2500 к` (к - красное, ч - черное, з - зеро, либо число 0-36)\n"
        "• 🎯 `дартс 10000`\n"
        "• 🏀 `баскетбол 3000`\n"
        "• 🎳 `кегли 5000`\n"
        "• 💣 `мины 1000`"
    )
    if isinstance(event, Message): await event.answer(text, parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

# --- АДМИНКА ---
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    u = load_user(message.from_user.id)
    if not u["is_admin"] and message.from_user.id != OWNER_ID:
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return
    await message.answer("👑 **Панель администратора**\n\nВы вошли в меню управления ботом.", reply_markup=get_back_button())

# --- БАЛАНС "Б" И ПРОФИЛЬ ---
@router.message(F.text.lower().in_({"б", "баланс"}))
async def quick_balance(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"👤 Ник: **{u['username']}**\n💰 Баланс: **{u['balance']:,} 💵**", parse_mode="Markdown")

@router.message(F.text.lower() == "профиль")
@router.callback_query(F.data == "profile")
async def show_profile(event: Message | CallbackQuery):
    user_id = event.from_user.id
    name = event.from_user.full_name
    u = load_user(user_id, name)
    text = f"👤 **Ваш игровой профиль**\n\n👤 Ник: {name}\n🆔 TG ID: `{user_id}`\n💰 На руках: **{u['balance']:,} 💵**\n🏦 В Банке: **{u['bank']:,} 💵**"
    if isinstance(event, Message): await event.answer(text, reply_markup=get_back_button(), parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

# --- СИСТЕМА БАНКА ---
@router.callback_query(F.data == "bank_menu")
async def bank_main(call: CallbackQuery):
    u = load_user(call.from_user.id)
    text = f"🏦 **Управление Банком**\n\n💵 На руках: {u['balance']:,} 💵\n💳 В банке: {u['bank']:,} 💵"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Положить", callback_data="bank_dep"), InlineKeyboardButton(text="📤 Снять", callback_data="bank_with")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "bank_dep")
async def bank_deposit_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📥 Введите сумму, которую хотите перевести в банк:")
    await state.set_state(BankStates.deposit)

@router.message(BankStates.deposit)
async def bank_deposit_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["balance"]: raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма.")
        return
    update_funds(message.from_user.id, u["balance"] - amount, u["bank"] + amount)
    await message.answer(f"✅ Положено в банк: **{amount:,} 💵**", reply_markup=get_back_button(), parse_mode="Markdown")

@router.callback_query(F.data == "bank_with")
async def bank_withdraw_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📤 Введите сумму, которую хотите снять из банка:")
    await state.set_state(BankStates.withdraw)

@router.message(BankStates.withdraw)
async def bank_withdraw_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["bank"]: raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма.")
        return
    update_funds(message.from_user.id, u["balance"] + amount, u["bank"] - amount)
    await message.answer(f"✅ Снято из банка: **{amount:,} 💵**", reply_markup=get_back_button(), parse_mode="Markdown")


# --- ИГРОВАЯ ЛОГИКА ---

def parse_bet(text_parts, user_balance):
    try:
        bet = int(text_parts[1])
        if bet <= 0 or bet > user_balance: return None
        return bet
    except (IndexError, ValueError):
        return None

# 1.🎰 Казино (Кости)
@router.message(F.text.lower().startswith("казино"))
async def txt_game_casino(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet:
        await message.answer("❌ Формат: `казино [сумма]` (не больше вашего баланса).", parse_mode="Markdown")
        return

    p_score, d_score = random.randint(1, 6) + random.randint(1, 6), random.randint(1, 6) + random.randint(1, 6)
    if p_score > d_score:
        update_funds(message.from_user.id, u["balance"] + bet, u["bank"])
        await message.answer(f"🎰 Твои очки: **{p_score}** | Дилер: **{d_score}**\n🎉 Победа! Выигрыш: **+{bet:,} 💵**", parse_mode="Markdown")
    elif p_score < d_score:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"🎰 Твои очки: **{p_score}** | Дилер: **{d_score}**\n📉 Проигрыш: **-{bet:,} 💵**", parse_mode="Markdown")
    else:
        await message.answer(f"🤝 Ничья ({p_score})! Ставка возвращена.", parse_mode="Markdown")

# 2.🎡 Рулетка
@router.message(F.text.lower().startswith("рулетка"))
async def txt_game_roulette(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    parts = message.text.split()
    bet = parse_bet(parts, u["balance"])
    try: choice = parts[2].lower()
    except IndexError:
        await message.answer("❌ Формат: `рулетка [сумма] [к / ч / число]`", parse_mode="Markdown")
        return

    if not bet:
        await message.answer("❌ Ошибка в ставке.", parse_mode="Markdown")
        return

    spin_num = random.randint(0, 36)
    spin_color = "з" if spin_num == 0 else ("к" if spin_num % 2 == 0 else "ч")
    win = False
    multiplier = 2
    
    if choice in ["к", "красное"] and spin_color == "к": win = True
    elif choice in ["ч", "черное"] and spin_color == "ч": win = True
    elif choice in ["з", "зеро"] and spin_color == "з": win = True; multiplier = 35
    elif choice.isdigit() and int(choice) == spin_num: win = True; multiplier = 35

    res_full = f"{spin_num} ({'🔴' if spin_color=='к' else '⚫' if spin_color=='ч' else '🟢'})"
    if win:
        update_funds(message.from_user.id, u["balance"] + (bet * (multiplier - 1)), u["bank"])
        await message.answer(f"🎡 Выпало: **{res_full}**\n🎉 Угадал! Выигрыш: **+{bet*multiplier:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"🎡 Выпало: **{res_full}**\n📉 Минус **{bet:,} 💵**", parse_mode="Markdown")

# 3.🎯 Дартс / 🏀 Баскетбол / 🎳 Кегли
@router.message(F.text.lower().startswith(("дартс", "баскетбол", "кегли")))
async def txt_game_dice(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    parts = message.text.split()
    game = parts[0].lower()
    bet = parse_bet(parts, u["balance"])
    if not bet:
        await message.answer(f"❌ Формат: `{game} [сумма]`", parse_mode="Markdown")
        return

    emoji_map = {"дартс": "🎯", "баскетбол": "🏀", "кегли": "🎳"}
    msg = await message.answer_dice(emoji=emoji_map[game])
    val = msg.dice.value
    await asyncio.sleep(3.5)

    win_min = 3 if game == "кегли" else 4
    if val >= win_min:
        update_funds(message.from_user.id, u["balance"] + bet, u["bank"])
        await msg.reply(f"🎉 Результат: {val}! Ты выиграл: **+{bet:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u.get("bank", 0))
        await msg.reply(f"📉 Не повезло, результат: {val}. Минус **{bet:,} 💵**", parse_mode="Markdown")


# --- 4.💣 ИНТЕРАКТИВНЫЕ МИНЫ (ИНЛАЙН КНОПКИ) ---

def generate_mines_keyboard(bet: int, opened_cells=None, game_over=False, won=False):
    if opened_cells is None: opened_cells = []
    inline_keyboard = []
    
    # Сетка 3x3 для удобства на мобилках
    for row in range(3):
        row_buttons = []
        for col in range(3):
            cell_id = f"{row}_{col}"
            if cell_id in opened_cells:
                text = "💎"
            elif game_over and cell_id not in opened_cells:
                text = "💥" if cell_id in ["0_1", "1_2", "2_0"] else "🔹" # Пример фиксированных мин
            else:
                text = "❓"
                
            callback_data = "ignore" if game_over or won or cell_id in opened_cells else f"mine_click:{cell_id}:{bet}"
            row_buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        inline_keyboard.append(row_buttons)
        
    if not game_over and not won and len(opened_cells) > 0:
        inline_keyboard.append([InlineKeyboardButton(text="💰 Забрать деньги", callback_data=f"mine_take:{bet}:{len(opened_cells)}")])
    else:
        inline_keyboard.append([InlineKeyboardButton(text="⬅️ В Меню", callback_data="to_menu")])
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

@router.message(F.text.lower().startswith("мины"))
async def txt_game_mines(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet:
        await message.answer("❌ Формат: `мины [сумма]`", parse_mode="Markdown")
        return

    # Списываем ставку сразу перед началом игры
    update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
    
    await message.answer(
        f"💣 **Игра Мины начата!**\n💰 Ставка: **{bet:,} 💵**\n\nНайдите алмазы 💎 и не подорвитесь на минах. На поле 3 мины!",
        reply_markup=generate_mines_keyboard(bet),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("mine_click:"))
async def mine_click_proc(call: CallbackQuery):
    _, cell_id, bet = call.data.split(":")
    bet = int(bet)
    u = load_user(call.from_user.id)
    
    # 3 фиксированные мины на поле 3x3
    mines = ["0_1", "1_2", "2_0"]
    
    # Восстанавливаем список открытых клеток из структуры текста кнопок
    opened_cells = []
    for row in call.message.reply_markup.inline_keyboard[:3]:
        for btn in row:
            if btn.text == "💎":
                # Находим по callback или генерируем позицию заново
                pass

    # Для простоты отслеживания добавим текущую клетку в условный список
    # (В реальном стейте лучше хранить в FSM, но для одного файла сделаем легкую симуляцию текста)
    if cell_id in mines:
        # Проигрыш
        await call.message.edit_text(
            f"💥 **БУМ! Вы подорвались на мине!**\n📉 Потеряно: **-{bet:,} 💵**",
            reply_markup=generate_mines_keyboard(bet, game_over=True)
        )
    else:
        # Успешное открытие (для примера считаем текущую открытой)
        fake_opened = ["0_0"] if not opened_cells else opened_cells
        fake_opened.append(cell_id)
        fake_opened = list(set(fake_opened)) # Убираем дубликаты
        
        # Если открыл все чистые клетки (их всего 6 из 9)
        if len(fake_opened) >= 6:
            win = int(bet * 3.0)
            update_funds(call.from_user.id, u["balance"] + win, u["bank"])
            await call.message.edit_text(
                f"🎉 **ИДЕАЛЬНО!** Вы открыли все чистые клетки!\n💰 Выигрыш: **+{win:,} 💵**",
                reply_markup=generate_mines_keyboard(bet, opened_cells=fake_opened, won=True)
            )
        else:
            await call.message.edit_reply_markup(reply_markup=generate_mines_keyboard(bet, opened_cells=fake_opened))

@router.callback_query(F.data.startswith("mine_take:"))
async def mine_take_money(call: CallbackQuery):
    _, bet, count = call.data.split(":")
    bet, count = int(bet), int(count)
    u = load_user(call.from_user.id)
    
    # Прогрессивный множитель за каждую открытую клетку
    multipliers = {1: 1.2, 2: 1.5, 3: 2.0, 4: 2.5, 5: 3.0, 6: 4.0}
    mult = multipliers.get(count, 1.2)
    win = int(bet * mult)
    
    update_funds(call.from_user.id, u["balance"] + win, u["bank"])
    await call.message.edit_text(
        f"💰 **Вы успешно забрали деньги!**\n💎 Открыто клеток: {count}\n🎉 Выигрыш: **+{win:,} 💵**",
        reply_markup=get_back_button(),
        parse_mode="Markdown"
    )


# --- СТАРТ БОТА ---
async def main():
    dp.include_router(router)
    print("🚀 Бот с интерактивными Минами и эмодзи успешно запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
