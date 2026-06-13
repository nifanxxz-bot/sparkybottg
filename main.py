import asyncio
import random
import sqlite3
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импортируем всё необходимое из нашего соседнего файла config
from config import bot, dp, init_db, OWNER_ID, DB_PATH, load_user, update_funds, MINES_GAMES

router = Router()

class BankStates(StatesGroup):
    deposit = State()
    withdraw = State()

class AdminStates(StatesGroup):
    give_id = State()
    give_amount = State()
    ban_id = State()

# --- МЕНЮ И КНОПКИ ---
def get_start_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть Игры", callback_data="show_games")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="🏦 Банк", callback_data="bank_menu")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help_guide")]
    ])

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ В Главное Меню", callback_data="to_menu")]])

@router.message(Command("start"))
async def cmd_start(message: Message):
    load_user(message.from_user.id, message.from_user.full_name)
    text = (
        "✨ Добро пожаловать в GRAM BOT! ✨\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "💵 Твой баланс уже ждет тебя в профиле.\n"
        "Выбирай интересующий раздел в меню ниже 👇"
    )
    await message.answer(text, reply_markup=get_start_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "✨ Главное меню GRAM BOT ✨\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Управляй банком, смотри профиль или играй!"
    )
    await call.message.edit_text(text, reply_markup=get_start_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "help_guide")
@router.message(Command("help"))
async def cmd_help(event: Message | CallbackQuery):
    text = (
        "ℹ️ Полезные команды для чата:\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "💰 б или баланс — твой быстрый счет\n"
        "👤 профиль — развернутая статистика\n"
        "🏦 Команды банка:\n"
        "• банк положить [сумма]\n"
        "• банк снять [сумма]\n\n"
        "📋 Примеры ставок:\n"
        "• кубы 5000 4 | казино 2000 | мины 10000"
    )
    if isinstance(event, Message): await event.answer(text, parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

@router.message(F.text.lower().in_({"б", "баланс"}))
async def quick_balance(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    await message.answer(f"👤 Ник: {u['username']}\n💰 Баланс: {u['balance']:,} 💵", parse_mode="Markdown")

@router.message(F.text.lower() == "профиль")
@router.callback_query(F.data == "profile")
async def show_profile(event: Message | CallbackQuery):
    u = load_user(event.from_user.id, event.from_user.full_name)
    if u["banned"]: return
    text = (
        "👤 Игровой профиль пользователя\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"• Ник: {u['username']}\n"
        f"• Telegram ID: {u['id']}\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"💵 На руках: {u['balance']:,} 💵\n"
        f"💳 В банке: {u['bank']:,} 💵"
    )
    if isinstance(event, Message): await event.answer(text, reply_markup=get_back_button(), parse_mode="Markdown")
    else: await event.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

# --- ЛОГИКА ТЕКСТОВОГО И ИНЛАЙН БАНКА ---
@router.message(F.text.lower().startswith("банк "))
async def txt_bank_commands(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    if len(parts) < 3: return
    action, amount_str = parts[1].lower(), parts[2]
    try: amount = int(amount_str)
    except ValueError: return

    if action in ["положить", "депозит"] and amount <= u["balance"] and amount > 0:
        update_funds(message.from_user.id, u["balance"] - amount, u["bank"] + amount)
        await message.answer(f"🏦 Банк GRAM\n✅ Положено на вклад: +{amount:,} 💵")
    elif action in ["снять", "вывод"] and amount <= u["bank"] and amount > 0:
        update_funds(message.from_user.id, u["balance"] + amount, u["bank"] - amount)
        await message.answer(f"🏦 Банк GRAM\n✅ Выдано наличными: +{amount:,} 💵")

@router.callback_query(F.data == "bank_menu")
async def bank_main(call: CallbackQuery):
    u = load_user(call.from_user.id)
    text = f"🏦 Финансовый Департамент Банка\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n Наличные: {u['balance']:,} 💵\n В банке: {u['bank']:,} 💵"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Депозит", callback_data="bank_dep"), InlineKeyboardButton(text="📤 Вывод", callback_data="bank_with")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "bank_dep")
async def bank_deposit_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📥 Введите сумму для вклада:")
    await state.set_state(BankStates.deposit)

@router.message(BankStates.deposit)
async def bank_deposit_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["balance"]: raise ValueError
    except ValueError: return
    update_funds(message.from_user.id, u["balance"] - amount, u["bank"] + amount)
    await message.answer(f"✅ Положено на счет: {amount:,} 💵", reply_markup=get_back_button())

@router.callback_query(F.data == "bank_with")
async def bank_withdraw_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("📤 Введите сумму для снятия:")
    await state.set_state(BankStates.withdraw)

@router.message(BankStates.withdraw)
async def bank_withdraw_proc(message: Message, state: FSMContext):
    u = load_user(message.from_user.id)
    await state.clear()
    try:
        amount = int(message.text)
        if amount <= 0 or amount > u["bank"]: raise ValueError
    except ValueError: return
    update_funds(message.from_user.id, u["balance"] + amount, u["bank"] - amount)
    await message.answer(f"✅ Выдано наличными: {amount:,} 💵", reply_markup=get_back_button())

# --- ИГРОВОЙ ЗАЛ ---
def parse_bet(text_parts, user_balance):
    try:
        bet = int(text_parts[1])
        if bet <= 0 or bet > user_balance: return None
        return bet
    except (IndexError, ValueError): return None

@router.callback_query(F.data == "show_games")
async def callback_show_games(call: CallbackQuery):
    text = (
        "🎮 Игровой зал GRAM BOT 🎮\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "👉 Играй прямо текстом в чат:\n\n"
        "🎰 казино [сумма] — три в ряд (x15)\n"
        "🎡 рулетка [сумма] [к / ч / 0-36] — точный цвет/число (x15)\n"
        "🎲 кубы [сумма] [1-6] — угадай число кубика (x15)\n"
        "🎯 дартс [сумма] — край (x1) | пред-центр (x2.5) | центр (x15)\n"
        "🏀 баскетбол [сумма] — на кольце (x1) | гол (x15)\n"
        "🎳 кегли [сумма] — сбей пару (x1.5) | страйк (x15)\n"
        "💣 мины [сумма] — поле 7х7 (5 мин)"
    )
    await call.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")

# 🎲 КУБЫ
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
        await message.answer("❌ Формат: кубы [сумма] [число 1-6]")
        return
    if not bet: return

    msg = await message.answer_dice(emoji="🎲")
    cube_res = msg.dice.value
    await asyncio.sleep(4.0)

    if cube_res == user_num:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"🎲 ТОЧНО В ЦЕЛЬ!\nВы загадали: {user_num} | Выпало: {cube_res}\n🎉 Выигрыш (х15): +{win_sum:,} 💵")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"🎲 Вы загадали: {user_num} | Выпало: {cube_res}\n📉 Не повезло. Проебал {bet:,} 💵")

# 🎰 КАЗИНО
@router.message(F.text.lower().startswith("казино"))
async def txt_game_casino(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet: return

    msg = await message.answer_dice(emoji="🎰")
    val = msg.dice.value
    await asyncio.sleep(4.0)

    if val in [1, 22, 43, 64]:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"🎰 ДЖЕКПОТ ТРИ В РЯД!\n🎉 Множитель x15: +{win_sum:,} 💵")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"🎰 Мимо линии!\n📉 Не повезло. Проебал {bet:,} 💵")

# 🎡 РУЛЕТКА
@router.message(F.text.lower().startswith("рулетка"))
async def txt_game_roulette(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    parts = message.text.split()
    bet = parse_bet(parts, u["balance"])
    try: choice = parts[2].lower()
    except IndexError: return
    if not bet: return

    spin_num = random.randint(0, 36)
    spin_color = "з" if spin_num == 0 else ("к" if spin_num % 2 == 0 else "ч")
    win = (choice in ["к", "красное"] and spin_color == "к") or (choice in ["ч", "черное"] and spin_color == "ч") or (choice.isdigit() and int(choice) == spin_num)

    res_emoji = "🔴 КРАСНОЕ" if spin_color == "к" else "⚫ ЧЕРНОЕ" if spin_color == "ч" else "🟢 ЗЕРО"
    if win:
        win_sum = bet * 15
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await message.answer(f"🎡 Выпало: {spin_num} ({res_emoji})\n🎉 Выигрыш (х15): +{win_sum:,} 💵")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await message.answer(f"🎡 Выпало: {spin_num} ({res_emoji})\n📉 Не повезло. Проебал {bet:,} 💵")

# 🎯 ИНТЕРАКТИВНЫЕ ИГРЫ
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

    mult, desc = 0, ""
    if game == "дартс":
        if val == 1: mult, desc = 0, "❌ Полный промах мимо мишени!"
        elif val == 2: mult, desc = 1.0, "⚪ Самый дальний белый круг (х1)"
        elif val == 3: mult, desc = 2.5, "🔴 Предпоследний ряд (красный круг) (х2.5)"
        elif val == 4: mult, desc = 2.5, "⚪ Предпоследний ряд (внутренний белый круг) (х2.5)"
        elif val == 5: mult, desc = 2.5, "🔴 Предпоследний ряд (внутренний красный круг) (х2.5)"
        elif val == 6: mult, desc = 15.0, "🎯 ЧИСТОЕ ПОПАДАНИЕ В ЯБЛОЧКО! (х15)"
    elif game == "баскетбол":
        if val in [1, 2]: mult, desc = 0, "❌ Мимо щита!"
        elif val == 3: mult, desc = 1.0, "🏀 Мяч застрял на кольце! Фол (х1)"
        elif val in [4, 5, 6]: mult, desc = 15.0, "💥 ЧИСТЕЙШИЙ ГОЛ! (х15)"
    elif game == "кегли":
        if val == 1: mult, desc = 0, "❌ Шар улетел в желоб!"
        elif val in [2, 3, 4]: mult, desc = 1.5, "🎳 Сбито пару кеглей (х1.5)"
        elif val in [5, 6]: mult, desc = 15.0, "🎳 МОЩНЫЙ СТРАЙК! (х15)"

    if mult > 0:
        win_sum = int(bet * mult)
        update_funds(message.from_user.id, u["balance"] + (win_sum - bet), u["bank"])
        await msg.reply(f"{desc}\n🎉 Начислено: +{win_sum:,} 💵")
    else:
        update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
        await msg.reply(f"{desc}\n📉 Не повезло. Проебал {bet:,} 💵")

# --- ИГРА МИНЫ 7х7 ---
def get_mines_kb(user_id, bet, game_over=False, won=False):
    game = MINES_GAMES[user_id]
    opened, mines = game["opened"], game["mines"]
    kb = []
    for r in range(7):
        row_btns = []
        for c in range(7):
            cell = f"{r}_{c}"
            text = "💎" if cell in opened else ("💥" if game_over and cell in mines else "❓")
            cb = "ignore" if game_over or won or cell in opened else f"m_play:{r}:{c}"
            row_btns.append(InlineKeyboardButton(text=text, callback_data=cb))
        kb.append(row_btns)
    if not game_over and not won and len(opened) > 0:
        kb.append([InlineKeyboardButton(text="💰 Забрать деньги", callback_data="m_take")])
    else: kb.append([InlineKeyboardButton(text="⬅️ Главное Меню", callback_data="to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text.lower().startswith("мины"))
async def txt_game_mines(message: Message):
    u = load_user(message.from_user.id, message.from_user.full_name)
    if u["banned"]: return
    bet = parse_bet(message.text.split(), u["balance"])
    if not bet: return

    all_cells = [f"{r}_{c}" for r in range(7) for c in range(7)]
    mines = random.sample(all_cells, 5)
    MINES_GAMES[message.from_user.id] = {"bet": bet, "mines": mines, "opened": []}
    update_funds(message.from_user.id, u["balance"] - bet, u["bank"])
    await message.answer(f"💣 МИННОЕ ПОЛЕ 7х7 (5 МИН)\nСтавка: {bet:,} 💵", reply_markup=get_mines_kb(message.from_user.id, bet))

@router.callback_query(F.data.startswith("m_play:"))
async def mine_game_click(call: CallbackQuery):
    u_id = call.from_user.id
    if u_id not in MINES_GAMES: return
    _, r, c = call.data.split(":")
    cell = f"{r}_{c}"
    game = MINES_GAMES[u_id]
    
    if cell in game["mines"]:
        await call.message.edit_text(f"💥 БУМ! Подорвался!\n📉 Не повезло. Проебал {game['bet']:,} 💵", reply_markup=get_mines_kb(u_id, game['bet'], game_over=True))
        MINES_GAMES.pop(u_id, None)
    else:
        game["opened"].append(cell)
        if len(game["opened"]) >= 44:
            win_sum = game["bet"] * 15
            update_funds(u_id, load_user(u_id)["balance"] + win_sum, load_user(u_id)["bank"])
            await call.message.edit_text(f"🏆 ПОЛНАЯ ЗАЧИСТКА ПОЛЯ! Выигрыш x15: +{win_sum:,} 💵", reply_markup=get_mines_kb(u_id, game['bet'], won=True))
            MINES_GAMES.pop(u_id, None)
        else: await call.message.edit_reply_markup(reply_markup=get_mines_kb(u_id, game['bet']))

@router.callback_query(F.data == "m_take")
async def mine_game_take(call: CallbackQuery):
    u_id = call.from_user.id
    if u_id not in MINES_GAMES: return
    game = MINES_GAMES[u_id]
    count = len(game["opened"])
    coef = 1.0 + (count * 0.35)
    win_sum = int(game["bet"] * coef)
    update_funds(u_id, load_user(u_id)["balance"] + win_sum, load_user(u_id)["bank"])
    await call.message.edit_text(f"💰 Деньги забраны! Алмазов: {count} | Коэфф: x{coef:.2f}\nЗачислено: +{win_sum:,} 💵", reply_markup=get_back_button())
    MINES_GAMES.pop(u_id, None)

# --- АДМИНИСТРАТИВНАЯ ЧАСТЬ ---
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    u = load_user(message.from_user.id)
    if not u["is_admin"] and message.from_user.id != OWNER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Начислить деньги", callback_data="adm_give")],
        [InlineKeyboardButton(text="🚫 Забанить юзера", callback_data="adm_ban")],
        [InlineKeyboardButton(text="⬅️ Выйти", callback_data="to_menu")]
    ])
    await message.answer("👑 Панель Управления Создателя\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", reply_markup=kb)

@router.callback_query(F.data == "adm_give")
async def adm_give_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Укажите Telegram ID счастливчика:")
    await state.set_state(AdminStates.give_id)

@router.message(AdminStates.give_id)
async def adm_give_id(message: Message, state: FSMContext):
    await state.update_data(target_id=int(message.text))
    await message.answer("Какую сумму начислить?")
    await state.set_state(AdminStates.give_amount)

@router.message(AdminStates.give_amount)
async def adm_give_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    t_user = load_user(data['target_id'])
    update_funds(t_user['id'], t_user['balance'] + int(message.text), t_user['bank'])
    await message.answer(f"✅ На счет {data['target_id']} успешно упало {int(message.text):,} 💵", reply_markup=get_back_button())

@router.callback_query(F.data == "adm_ban")
async def adm_ban_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите Telegram ID для блокировки:")
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
    await message.answer(f"🚫 Профиль {target} заблокирован в системе бота.", reply_markup=get_back_button())

# --- ТОЧКА ВХОДА ЗАПУСКА ---
async def main():
    init_db()
    dp.include_router(router)
    print("🚀 GRAM BOT успешно обновился и готов к работе!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
