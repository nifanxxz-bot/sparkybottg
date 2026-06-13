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

class AdminStates(StatesGroup):
    give_id = State()
    give_amount = State()
    ban_id = State()

MINES_GAMES = {}

# --- КЛАВИАТУРЫ ---
def get_start_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть Игры", callback_data="show_games")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="🏦 Банк", callback_data="bank_menu")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help_guide")]
    ])

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ В Главное Меню", callback_data="to_menu")]])

# --- НАВИГАЦИЯ ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    load_user(message.from_user.id, message.from_user.full_name)
    text = (
        "✨ **Добро пожаловать в GRAM BOT!** ✨\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "💵 Твой баланс уже ждет тебя в профиле.\n"
        "Выбирай интересующий раздел в меню ниже 👇"
    )
    await message.answer(text, reply_markup=get_start_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "✨ **Главное меню GRAM BOT** ✨\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Управляй банком, смотри профиль или играй!"
    )
    await call.message.edit_text(text, reply_markup=get_start_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "show_games")
async def callback_show_games(call: CallbackQuery):
    text = (
        "🎮 **Игровой зал GRAM BOT** 🎮\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "👉 *Играй прямо текстом в чат:*\n\n"
        "🎰 `казино [сумма]` — три в ряд (**x15**)\n"
        "🎡 `рулетка [сумма] [к / ч / 0-36]` — точный цвет/число (**x15**)\n"
        "🎲 `кубы [сумма] [1-6]` — угадай число на кубике (**x15**)\n"
        "🎯 `дартс [сумма]` — край (**x1**) | пред-центр (**x2.5**) | центр (**x15**)\n"
        "🏀 `баскетбол [сумма]` — на кольце (**x1**) | четкий гол (**x15**)\n"
        "🎳 `кегли [сумма]` — сбей пару (**x1.5**) | страйк (**x15**)\n"
        "💣 `мины [сумма]` — интерактивное поле 7х7 (5 мин)"
    )
    await call.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

@router.callback_query(F.data == "help_guide")
@router.message(Command("help"))
async def cmd_help(event: Message | CallbackQuery):
    text = (
        "ℹ️ **Полезные команды для чата:**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "💰 `б` или `баланс` — твой быстрый счет\n"
        "👤 `профиль` — развернутая статистика\n"
        "🏦 **Команды банка:**\n"
        "• `банк положить [сумма]`\n"
        "• `банк снять [сумма]`\n\n"
        "📋 **Примеры игровых ставок:**\n"
        "• `кубы 5000 4` (ставка 5000 на число 4)\n"
        "• `казино 2000`\n"
        "• `рулетка 1000 к`\n"
        "• `мины 10000`"
    )
    if isinstance(event, Message): await event.answer(text, parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

# --- ПРОФИЛЬ И БАЛАНС ---
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
    text = (
        "👤 **Игровой профиль пользователя**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"• **Ник:** {u['username']}\n"
        f"• **Telegram ID:** `{u['id']}`\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"💵 **На руках:** {u['balance']:,} 💵\n"
        f"💳 **В банке:** {u['bank']:,} 💵"
    )
    if isinstance(event, Message): await event.answer(text, reply_markup=get_back_button(), parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")


# --- ТЕКСТОВЫЕ И ИНЛАЙН КОМАНДЫ БАНКА ---
@router.message(F.text.lower().startswith("банк "))
async def txt_bank_commands(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    
    if len(parts) < 3:
        await message.answer("❌ Неверный формат. Используйте: `банк положить [сумма]` или `банк снять [сумма]`")
        return
        
    action = parts[1].lower()
    try:
        amount = int(parts[2])
        if amount <= 0: raise ValueError
    except ValueError:
        await message.answer("❌ Сумма должна быть целым положительным числом.")
        return

    if action in ["положить", "депозит"]:
        if amount > u["balance"]:
            await message.answer("❌ У вас нет столько наличных денег на руках.")
            return
        update_funds(message.from_user.id, u["balance"] - amount, u["bank"] + amount)
        await message.answer(f"🏦 **Банк GRAM**\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n✅ Положено на вклад: **+{amount:,} 💵**", parse_mode="Markdown")

    elif action in ["снять", "вывод"]:
        if amount > u["bank"]:
            await message.answer("❌ В вашем банковском сейфе нет такого количества средств.")
            return
        update_funds(message.from_user.id, u["balance"] + amount, u["bank"] - amount)
        await message.answer(f"🏦 **Банк GRAM**\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n✅ Выдано наличными: **+{amount:,} 💵**", parse_mode="Markdown")
    else:
        await message.answer("❌ Неизвестная банковская операция. Используйте `положить` или `снять`.")

@router.callback_query(F.data == "bank_menu")
async def bank_main(call: CallbackQuery):
    u = load_user(call.from_user.id)
    text = (
        "🏦 **Финансовый Департамент Банка**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f" Наличные в кармане: **{u['balance']:,} 💵**\n"
        f" Сбережения на вкладе: **{u['bank']:,} 💵**\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Выберите нужное действие на панели:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Депозит (Положить)", callback_data="bank_dep"), InlineKeyboardButton(text="📤 Вывод (Снять)", callback_data="bank_with")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "bank_dep")
async def bank_deposit_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📥 **Пополнение вклада**\n\nВведите сумму, которую хотите отправить в банк:")
    await state.set_state(BankStates.deposit)

@router.message(BankStates.deposit)
async def bank_deposit_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["balance"]: raise ValueError
    except ValueError:
        await message.answer("❌ Сумма указана неверно или у вас недостаточно наличных.")
        return
    update_funds(message.from_user.id, u["balance"] - amount, u["bank"] + amount)
    await message.answer(f"✅ **Операция успешна!**\nПоложено на счет: **{amount:,} 💵**", reply_markup=get_back_button(), parse_mode="Markdown")

@router.callback_query(F.data == "bank_with")
async def bank_withdraw_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📤 **Снятие наличных**\n\nВведите сумму, которую хотите забрать из банка:")
    await state.set_state(BankStates.withdraw)

@router.message(BankStates.withdraw)
async def bank_withdraw_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["bank"]: raise ValueError
    except ValueError:
        await message.answer("❌ Сумма указана некорректно либо в банке нет таких средств.")
        return
    update_funds(message.from_user.id, u["balance"] + amount, u["bank"] - amount)
    await message.answer(f"✅ **Операция успешна!**\nВыдано наличными: **{amount:,} 💵**", reply_markup=get_back_button(), parse_mode="Markdown")


# --- ИГРЫ ТЕКСТОМ ---
def parse_bet(text_parts, user_balance):
    try:
        bet = int(text_parts[1])
        if bet <= 0 or bet > user_balance: return None
        return bet
    except (IndexError, ValueError):
        return None

# 🎲 НОВАЯ ИГРА: КУБЫ С СУММОЙ И ЧИСЛОМ (х15)
@router.message(F.text.lower().startswith("кубы"))
async def txt_game_cubes(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    bet = parse_bet(parts, u["balance"])
    
    try:
        user_num = int(parts[2])
        if user_num < 1 or user_num > 6: raise ValueError
    except (IndexError, ValueError):
        await message.answer("❌ Формат ставки: `кубы [сумма] [число от 1 до 6]`\nПример: `кубы 5000 4`")
        return

    if not bet:
        await message.answer("❌ Ошибка в сумме ставки или недостаточно баланса.")
        return

    msg = await message.answer_dice(emoji="🎲")
    cube_res = msg.dice.value
    await asyncio.sleep(4.0)

    if cube_res == user_num:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"🎲 **ТОЧНОЕ ПОПАДАНИЕ!** 🎲\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎯 Вы загадали: **{user_num}** | Выпало: **{cube_res}**\n🎉 Твой безумный выигрыш (х15): **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"🎲 **Не угадал! Ставка сгорела!** 🎲\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎯 Вы загадали: **{user_num}** | Выпало: **{cube_res}**\n📉 Потеряно: **-{bet:,} 💵**", parse_mode="Markdown")

# 🎰 КАЗИНО (СЛОТЫ)
@router.message(F.text.lower().startswith("казино"))
async def txt_game_casino(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet:
        await message.answer("❌ Формат ставки: `казино [сумма]`")
        return

    msg = await message.answer_dice(emoji="🎰")
    val = msg.dice.value
    await asyncio.sleep(4.0)

    if val in [1, 22, 43, 64]:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"🎰 **🎰 ТРИ В РЯД! ДЖЕКПОТ!** 🎰\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎉 Твой фантастический куш (х15): **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"🎰 **🎰 Увы, мимо!** 🎰\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n💥 Линия не совпала. Ставка сгорела: **-{bet:,} 💵**", parse_mode="Markdown")

# 🎡 РУЛЕТКА
@router.message(F.text.lower().startswith("рулетка"))
async def txt_game_roulette(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    bet = parse_bet(parts, u["balance"])
    try: choice = parts[2].lower()
    except IndexError:
        await message.answer("❌ Формат ставки: `рулетка [сумма] [к / ч / 0-36]`")
        return

    if not bet: return

    spin_num = random.randint(0, 36)
    spin_color = "з" if spin_num == 0 else ("к" if spin_num % 2 == 0 else "ч")
    
    win = False
    if choice in ["к", "красное"] and spin_color == "к": win = True
    elif choice in ["ч", "черное"] and spin_color == "ч": win = True
    elif choice.isdigit() and int(choice) == spin_num: win = True

    res_emoji = "🔴 КРАСНОЕ" if spin_color == "к" else "⚫ ЧЕРНОЕ" if spin_color == "ч" else "🟢 ЗЕРО"
    if win:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await message.answer(f"🎡 **Колесо остановилось!** 🎡\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎰 Выпало: **{spin_num} ({res_emoji})**\n🎉 Угадал! Победный приз (х15): **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"🎡 **Колесо остановилось!** 🎡\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎰 Выпало: **{spin_num} ({res_emoji})**\n📉 Ставка проиграна: **-{bet:,} 💵**", parse_mode="Markdown")

# 🎯 ДАРТС / 🏀 БАСКЕТБОЛ / 🎳 КЕГЛИ
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
        if val == 1: mult = 0; desc = "❌ Полный промах мимо мишени!"
        elif val == 2: mult = 1.0; desc = "⚪ Самый дальний белый круг (х1)"
        elif val == 3: mult = 2.5; desc = "🔴 Предпоследний ряд (красный круг) (х2.5)"
        elif val == 4: mult = 2.5; desc = "⚪ Предпоследний ряд (внутренний белый круг) (х2.5)"
        elif val == 5: mult = 2.5; desc = "🔴 Предпоследний ряд (внутренний красный круг) (х2.5)"
        elif val == 6: mult = 15.0; desc = "🎯 ЧИСТОЕ ПОПАДАНИЕ В ЯБЛОЧКО! (х15)"
        
    elif game == "баскетбол":
        if val in [1, 2]: mult = 0; desc = "❌ Мяч пролетел мимо щита!"
        elif val == 3: mult = 1.0; desc = "🏀 Мяч предательски застрял на кольце! Фол (х1)"
        elif val in [4, 5, 6]: mult = 15.0; desc = "💥 ЧИСТЕЙШИЙ ГОЛ! Сетка сорвана! (х15)"

    elif game == "кегли":
        if val == 1: mult = 0; desc = "❌ Шар улетел в желоб!"
        elif val in [2, 3, 4]: mult = 1.5; desc = "🎳 Сбито пару кеглей на дорожке (х1.5)"
        elif val in [5, 6]: mult = 15.0; desc = "🎳 МОЩНЫЙ СТРАЙК! Все кегли вдребезги! (х15)"

    if mult > 0:
        win_sum = int(bet * mult)
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"🎲 **Результат броска:**\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{desc}\n🎉 Начислено: **+{win_sum:,} 💵**", parse_mode="Markdown")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"🎲 **Результат броска:**\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{desc}\n📉 Потери: **-{bet:,} 💵**", parse_mode="Markdown")

# 💣 МИНЫ 7х7 (5 МИН)
def get_mines_kb(user_id, bet, game_over=False, won=False):
    game = MINES_GAMES[user_id]
    opened = game["opened"]
    mines = game["mines"]
    kb = []
    for r in range(7):
        row_btns = []
        for c in range(7):
            cell = f"{r}_{c}"
            if cell in opened: text = "💎"
            elif game_over and cell in mines: text = "💥"
            else: text = "❓"
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
        await message.answer("❌ Формат ставки: `мины [сумма]`")
        return

    all_cells = [f"{r}_{c}" for r in range(7) for c in range(7)]
    mines = random.sample(all_cells, 5)
    MINES_GAMES[message.from_user.id] = {"bet": bet, "mines": mines, "opened": []}
    
    update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
    await message.answer(
        f"💣 **МИННОЕ ПОЛЕ 7х7** 💣\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n• Ставка: **{bet:,} 💵**\n• Опасность: **5 скрытых мин**\n\nИщи алмазы 💎 и вовремя забирай банк!",
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
        await call.message.edit_text(f"💥 **БУМ! Подорвался!** 💥\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📉 Ты наступил на мину. Ставка **-{game['bet']:,} 💵** сгорела.", reply_markup=get_mines_kb(u_id, game['bet'], game_over=True))
        MINES_GAMES.pop(u_id, None)
    else:
        game["opened"].append(cell)
        if len(game["opened"]) >= 44:
            win_sum = game["bet"] * 15
            u = load_user(u_id)
            update_funds(u_id, u["balance"] + win_sum, u["bank"])
            await call.message.edit_text(f"🏆 **БЕЗУПРЕЧНО! ПОЛНАЯ ЗАЧИСТКА ПОЛЯ!** 🏆\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎉 Множитель x15 твой: **+{win_sum:,} 💵**", reply_markup=get_mines_kb(u_id, game['bet'], won=True))
            MINES_GAMES.pop(u_id, None)
        else:
            await call.message.edit_reply_markup(reply_markup=get_mines_kb(u_id, game['bet']))

@router.callback_query(F.data == "m_take")
async def mine_game_take(call: CallbackQuery):
    u_id = call.from_user.id
    if u_id not in MINES_GAMES: return
    game = MINES_GAMES[u_id]
