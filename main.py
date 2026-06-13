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

# --- СОСТОЯНИЯ FSM ---
class BankStates(StatesGroup):
    deposit = State()
    withdraw = State()

class AdminStates(StatesGroup):
    give_id = State()
    give_amount = State()
    take_id = State()
    take_amount = State()
    ban_id = State()
    unban_id = State()

# В памяти будем хранить состояние активных игр в мины (карты мин для юзеров)
MINES_GAMES = {}

# --- КЛАВИАТУРЫ ---
def get_start_menu() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🎮 Игры", callback_data="show_games")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="🏦 Банк", callback_data="bank_menu")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help_guide")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ В Меню", callback_data="to_menu")]])

# --- СТАРТ И НАВИГАЦИЯ ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    load_user(message.from_user.id, message.from_user.full_name)
    await message.answer("👋 **Добро пожаловать в игровой бот!**\nВыбирай нужное действие в меню ниже 👇", reply_markup=get_start_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("👋 **Главное меню игрового бота:**", reply_markup=get_start_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "show_games")
async def callback_show_games(call: CallbackQuery):
    text = (
        "🎰 **Список доступных игр (играй текстом в чат):**\n\n"
        "• 🎰 `казино [сумма]` — игровой автомат (3 в ряд = х15)\n"
        "• 🎡 `рулетка [сумма] [к/ч/число]` — выигрыш числа/цвета = х15\n"
        "• 🎯 `дартс [сумма]` — мишень (край х1, пред-центр х2.5, центр х15)\n"
        "• 🏀 `баскетбол [сумма]` — кольцо (застрял х1, гол х15)\n"
        "• 🎳 `кегли [сумма]` — сбей страйк\n"
        "• 💣 `мины [сумма]` — поле 7х7, 5 опасных мин!"
    )
    await call.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

@router.callback_query(F.data == "help_guide")
@router.message(Command("help"))
async def cmd_help(event: Message | CallbackQuery):
    text = (
        "ℹ️ **Справка по командам**\n\n"
        "💰 `б` или `баланс` — быстрый баланс и ник\n"
        "👤 `профиль` — статистика аккаунта\n"
        "👑 `/admin` — админ-панель\n\n"
        "📋 **Примеры ставок:**\n"
        "• `казино 5000`\n"
        "• `рулетка 1000 к` (или `рулетка 1000 17`)\n"
        "• `дартс 2000`\n"
        "• `баскетбол 5000`"
    )
    if isinstance(event, Message): await event.answer(text, parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

# --- ПРОФИЛЬ И БЫСТРЫЙ БАЛАНС "Б" ---
@router.message(F.text.lower().in_({"б", "баланс"}))
async def quick_balance(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    await message.answer(f"👤 Ник: **{u['username']}**\n💰 Баланс: **{u['balance']:,} 💵**", parse_mode="Markdown")

@router.message(F.text.lower() == "профиль")
@router.callback_query(F.data == "profile")
async def show_profile(event: Message | CallbackQuery):
    u = load_user(event.from_user.id, event.from_user.full_name)
    if u["banned"]: return
    text = f"👤 **Ваш игровой профиль**\n\n👤 Ник: {u['username']}\n🆔 TG ID: `{u['id']}`\n💰 На руках: **{u['balance']:,} 💵**\n🏦 В Банке: **{u['bank']:,} 💵**"
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
    await call.message.edit_text("📥 Введите сумму для перевода в банк:")
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
    await call.message.edit_text("📤 Введите сумму для снятия из банка:")
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


# --- ПОЛНОЦЕННАЯ НАСТРОЕННАЯ АДМИНКА ---
def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Выдать баланс", callback_data="adm_give"), InlineKeyboardButton(text="❌ Забрать баланс", callback_data="adm_take")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data="adm_ban"), InlineKeyboardButton(text="🟢 Разбан", callback_data="adm_unban")],
        [InlineKeyboardButton(text="⬅️ Выход", callback_data="to_menu")]
    ])

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    u = load_user(message.from_user.id)
    if not u["is_admin"] and message.from_user.id != OWNER_ID: return
    await message.answer("👑 **Панель Администратора**\n\nВыберите действие для управления игроками:", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "adm_give")
async def adm_give_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите Telegram ID игрока, кому выдать баланс:")
    await state.set_state(AdminStates.give_id)

@router.message(AdminStates.give_id)
async def adm_give_id(message: Message, state: FSMContext):
    await state.update_data(target_id=int(message.text))
    await message.answer("Введите сумму для начисления:")
    await state.set_state(AdminStates.give_amount)

@router.message(AdminStates.give_amount)
async def adm_give_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    t_user = load_user(data['target_id'])
    update_funds(t_user['id'], t_user['balance'] + int(message.text), t_user['bank'])
    await message.answer(f"✅ Успешно начислено {int(message.text):,} 💵 игроку `{data['target_id']}`", reply_markup=get_back_button())

@router.callback_query(F.data == "adm_ban")
async def adm_ban_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите ID для блокировки:")
    await state.set_state(AdminStates.ban_id)

@router.message(AdminStates.ban_id)
async def adm_ban_proc(message: Message, state: FSMContext):
    target = int(message.text)
    await state.clear()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 1 WHERE id = ?", (target,))
    conn.commit()
    conn.close()
    await message.answer(f"🚫 Пользователь `{target}` забанен.", reply_markup=get_back_button())


# --- ТЕКСТОВАЯ ЛОГИКА ИГР С Х15 КОЭФФИЦИЕНТАМИ ---

def parse_bet(text_parts, user_balance):
    try:
        bet = int(text_parts[1])
        if bet <= 0 or bet > user_balance: return None
        return bet
    except (IndexError, ValueError):
        return None

# 1. СЛОТЫ / КАЗИНО 🎰
@router.message(F.text.lower().startswith("казино"))
async def txt_game_casino(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet:
        await message.answer("❌ Формат: `казино [сумма]`")
        return

    # Отправляем настоящий анимационный слот-автомат
    msg = await message.answer_dice(emoji="🎰")
    val = msg.dice.value
    await asyncio.sleep(4.0)

    # В телеграме значения 1, 22, 43, 64 - это победные комбинации (три в ряд)
    win_values = [1, 22, 43, 64]
    
    if val in win_values:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"🎰 **ТРИ В РЯД!** Поздравляем!\n🎉 Твой выигрыш (х15): **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"💥 Комбинация не совпала. Ставка сгорела!\n📉 Потеряно: **-{bet:,} 💵**", parse_mode="Markdown")

# 2. РУЛЕТКА х15
@router.message(F.text.lower().startswith("рулетка"))
async def txt_game_roulette(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    bet = parse_bet(parts, u["balance"])
    try: choice = parts[2].lower()
    except IndexError:
        await message.answer("❌ Формат: `рулетка [сумма] [к / ч / 0-36]`")
        return

    if not bet: return

    spin_num = random.randint(0, 36)
    spin_color = "з" if spin_num == 0 else ("к" if spin_num % 2 == 0 else "ч")
    
    win = False
    if choice in ["к", "красное"] and spin_color == "к": win = True
    elif choice in ["ч", "черное"] and spin_color == "ч": win = True
    elif choice.isdigit() and int(choice) == spin_num: win = True

    res_emoji = "🔴" if spin_color == "к" else "⚫" if spin_color == "ч" else "🟢"
    if win:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await message.answer(f"🎡 Выпало: **{spin_num} {res_emoji}**\n🎉 Идеальное попадание! Выигрыш (х15): **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"🎡 Выпало: **{spin_num} {res_emoji}**\n📉 Не угадал, ставка сгорела: **-{bet:,} 💵**", parse_mode="Markdown")

# 3. ДАРТС, БАСКЕТБОЛ, КЕГЛИ С КАСТОМНЫМИ МНОЖИТЕЛЯМИ
@router.message(F.text.lower().startswith(("дартс", "баскетбол", "кегли")))
async def txt_interactive_dice(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    game = parts[0].lower()
    bet = parse_bet(parts, u["balance"])
    if not bet: return

    emoji_map = {"дартс": "🎯", "баскетбол": "🏀", "кегли": "🎳"}
    msg = await message.answer_dice(emoji=emoji_map[game])
    val = msg.dice.value
    await asyncio.sleep(4.0)

    mult = 0
    desc = ""

    if game == "дартс":
        if val == 1: mult = 0; desc = "Мимо мишени!"
        elif val in [2, 3]: mult = 1.0; desc = "Самый дальний круг (х1)"
        elif val in [4, 5]: mult = 2.5; desc = "Предпоследний круг (х2.5)"
        elif val == 6: mult = 15.0; desc = "🎯 ЧИСТОЕ ПОПАДАНИЕ В ЦЕНТР! (х15)"
        
    elif game == "баскетбол":
        if val in [1, 2]: mult = 0; desc = "Мимо кольца!"
        elif val == 3: mult = 1.0; desc = "🏀 Мяч застрял на кольце! Фол (х1)"
        elif val in [4, 5, 6]: mult = 15.0; desc = "💥 ЧИСТЫЙ ГОЛ! (х15)"

    elif game == "кегли":
        if val == 1: mult = 0; desc = "Мимо всех кегль!"
        elif val in [2, 3, 4]: mult = 1.5; desc = "Сбито несколько кегль (х1.5)"
        elif val in [5, 6]: mult = 15.0; desc = "🎳 СТРАЙК! Все кегли сбиты (х15)"

    if mult > 0:
        win_sum = int(bet * mult)
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"{desc}\n🎉 Твой выигрыш: **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"{desc}\n📉 Ставка сгорела полностью! **-{bet:,} 💵**", parse_mode="Markdown")


# --- 4. 💣 ИНТЕРАКТИВНЫЕ МИНЫ 7х7 (5 МИН) ---

def get_mines_kb(user_id, bet, game_over=False, won=False):
    game = MINES_GAMES[user_id]
    opened = game["opened"]
    mines = game["mines"]
    
    kb = []
    # Сетка 7 на 7
    for r in range(7):
        row_btns = []
        for c in range(7):
            cell = f"{r}_{c}"
            if cell in opened:
                text = "💎"
            elif game_over and cell in mines:
                text = "💥"
            else:
                text = "❓"
                
            cb = "ignore" if game_over or won or cell in opened else f"m_play:{r}:{c}"
            row_btns.append(InlineKeyboardButton(text=text, callback_data=cb))
        kb.append(row_btns)
        
    if not game_over and not won and len(opened) > 0:
        kb.append([InlineKeyboardButton(text="💰 Забрать деньги", callback_data="m_take")])
    else:
        kb.append([InlineKeyboardButton(text="⬅️ Главное Меню", callback_data="to_menu")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text.lower().startswith("мины"))
async def txt_game_mines(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet:
        await message.answer("❌ Формат: `мины [сумма]`")
        return

    # Генерируем 5 случайных мин на поле 7х7
    all_cells = [f"{r}_{c}" for r in range(7) for c in range(7)]
    mines = random.sample(all_cells, 5)
    
    MINES_GAMES[message.from_user.id] = {
        "bet": bet,
        "mines": mines,
        "opened": []
    }
    
    update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
    await message.answer(
        f"💣 **МИНЫ 7х7 НАЧАТЫ!**\n💰 Ставка: **{bet:,} 💵**\nНа поле спрятано **5 мин**. Открывайте клетки ❓!",
        reply_markup=get_mines_kb(message.from_user.id, bet),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("m_play:"))
async def mine_game_click(call: CallbackQuery):
    u_id = call.from_user.id
    if u_id not in MINES_GAMES: return
    
    _, r, c = call.data.split(":")
    cell = f"{r}_{c}"
    game = MINES_GAMES[u_id]
    
    if cell in game["mines"]:
        # Подорвался
        await call.message.edit_text(f"💥 **БУМ! Вы наступили на мину!**\n📉 Ставка **{game['bet']:,} 💵** полностью сгорела.", reply_markup=get_mines_kb(u_id, game['bet'], game_over=True))
        MINES_GAMES.pop(u_id, None)
    else:
        game["opened"].append(cell)
        # Если чудом открыл все чистые клетки (44 штуки)
        if len(game["opened"]) >= 44:
            win_sum = game["bet"] * 15
            u = load_user(u_id)
            update_funds(u_id, u["balance"] + win_sum, u["bank"])
            await call.message.edit_text(f"🏆 **НЕВЕРОЯТНО!** Вы зачистили поле!\n🎉 Выигрыш (х15): **+{win_sum:,} 💵**", reply_markup=get_mines_kb(u_id, game['bet'], won=True))
            MINES_GAMES.pop(u_id, None)
        else:
            await call.message.edit_reply_markup(reply_markup=get_mines_kb(u_id, game['bet']))

@router.callback_query(F.data == "m_take")
async def mine_game_take(call: CallbackQuery):
    u_id = call.from_user.id
    if u_id not in MINES_GAMES: return
    
    game = MINES_GAMES[u_id]
    count = len(game["opened"])
    
    # Плавный повышающийся коэффициент за количество открытых ячеек на поле 7х7
    coef = 1.0 + (count * 0.25)
    win_sum = int(game["bet"] * coef)
    
    u = load_user(u_id)
    update_funds(u_id, u["balance"] + win_sum, u["bank"])
    
    await call.message.edit_text(f"💰 **Деньги успешно забраны!**\n💎 Вы открыли ячеек: {count}\n🎉 Множитель: x{coef:.2f}\n💵 Зачислено: **+{win_sum:,} 💵**", reply_markup=get_back_button(), parse_mode="Markdown")
    MINES_GAMES.pop(u_id, None)


# --- СТАРТ ---
async def main():
    dp.include_router(router)
    print("🚀 Новая сборка с Казино 🎰, Минами 7х7 и х15 коэффами активна!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
