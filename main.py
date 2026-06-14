import asyncio
import random
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# =====================================================================
# ВСТАВЬ СВОЙ ТОКЕН СЮДА:
BOT_TOKEN = "8999022213:AAHlLNRC0iDgSljIWzvLnB-FMHjefFGsiJw"
# =====================================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных SQLite для хранения игроков
DB_NAME = "onepiece_rpg.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            fraction TEXT,
            level INTEGER,
            exp INTEGER,
            gold INTEGER,
            base_hp INTEGER,
            base_atk INTEGER,
            stat_points INTEGER,
            weapon_name TEXT,
            weapon_rank TEXT,
            weapon_dmg INTEGER,
            weapon_level INTEGER,
            unlocked_island INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Данные игры
ISLANDS = [
    {"name": "Фууся (Ист Блу)", "mult": 1.0, "boss": "Хигума"},
    {"name": "Арлонг Парк", "mult": 1.5, "boss": "Арлонг"},
    {"name": "Логтаун", "mult": 2.0, "boss": "Смокер"},
    {"name": "Виски Пик", "mult": 3.0, "boss": "Мистер 5"},
    {"name": "Алабаста", "mult": 4.5, "boss": "Крокодайл"},
    {"name": "Скайпия", "mult": 6.0, "boss": "Энель"},
    {"name": "Эниес Лобби", "mult": 8.0, "boss": "Роб Луччи"},
    {"name": "Маринфорд", "mult": 11.0, "boss": "Акаину"},
    {"name": "Дресс Роза", "mult": 15.0, "boss": "Дофламинго"},
    {"name": "Вано (Новый Мир)", "mult": 22.0, "boss": "Кайдо"}
]

WEAPONS_SHOP = [
    {"id": 1, "name": "Сабля", "rank": "E", "damage": 5, "price": 100},
    {"id": 2, "name": "Труба Сабо", "rank": "E", "damage": 12, "price": 300},
    {"id": 3, "name": "Пистолет", "rank": "D", "damage": 25, "price": 800},
    {"id": 4, "name": "Кикоку Ло", "rank": "D", "damage": 45, "price": 1800},
    {"id": 5, "name": "Муракумогори", "rank": "C", "damage": 75, "price": 4000},
    {"id": 6, "name": "Вандо Итимондзи", "rank": "C", "damage": 120, "price": 8500},
    {"id": 7, "name": "Сандай Китэцу", "rank": "B", "damage": 200, "price": 17000},
    {"id": 8, "name": "Сюсуй", "rank": "B", "damage": 350, "price": 35000},
    {"id": 9, "name": "Энма", "rank": "A", "damage": 600, "price": 75000},
    {"id": 10, "name": "Ёру Михока", "rank": "S", "damage": 1200, "price": 150000}
]

# Вспомогательные функции БД
def get_player(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_player(user_id, name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO players 
        VALUES (?, ?, 'Пираты', 1, 0, 500, 100, 10, 0, 'Кулаки', 'F', 0, 1, 0)
    ''', (user_id, name))
    conn.commit()
    conn.close()

def update_player(p):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE players SET 
        name=?, fraction=?, level=?, exp=?, gold=?, base_hp=?, base_atk=?, 
        stat_points=?, weapon_name=?, weapon_rank=?, weapon_dmg=?, 
        weapon_level=?, unlocked_island=? WHERE user_id=?
    ''', (p['name'], p['fraction'], p['level'], p['exp'], p['gold'], p['base_hp'], p['base_atk'],
          p['stat_points'], p['weapon_name'], p['weapon_rank'], p['weapon_dmg'],
          p['weapon_level'], p['unlocked_island'], p['user_id']))
    conn.commit()
    conn.close()

def get_total_atk(p):
    w_bonus = p['weapon_dmg'] * (1 + (p['weapon_level'] - 1) * 0.2)
    return int(p['base_atk'] + w_bonus)

def get_max_hp(p):
    return p['base_hp'] + (p['level'] * 15)

def check_lvl_up(p):
    needed = p['level'] * 100
    if p['exp'] >= needed:
        p['exp'] -= needed
        p['level'] += 1
        p['stat_points'] += 5
        return True
    return False

# --- КЛАВИАТУРЫ ---
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺️ Острова", callback_query_data="menu_islands"),
         InlineKeyboardButton(text="🛒 Магазин", callback_query_data="menu_shop")],
        [InlineKeyboardButton(text="⚙️ Настройки/Прокачка", callback_query_data="menu_settings"),
         InlineKeyboardButton(text="📜 Помощь", callback_query_data="menu_help")]
    ])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    create_player(message.from_user.id, message.from_user.first_name)
    p = get_player(message.from_user.id)
    
    text = (f"🏴‍☠️ **Добро пожаловать в мир One Piece, Капитан {p['name']}!**\n\n"
            f"⭐ Уровень: {p['level']}\n"
            f"💰 Золото: {p['gold']} белли\n"
            f"⚔️ Оружие: {p['weapon_name']} [{p['weapon_rank']}] (+{p['weapon_level']})")
    
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "to_main")
async def to_main(call: CallbackQuery):
    p = get_player(call.from_user.id)
    text = (f"🏴‍☠️ **Главное Меню**\n\n"
            f"👤 Капитан: {p['name']} | Фракция: {p['fraction']}\n"
            f"⭐ Уровень: {p['level']} (Опыт: {p['exp']}/{p['level']*100})\n"
            f"💰 Золото: {p['gold']} белли\n"
            f"⚔️ Оружие: {p['weapon_name']} (+{p['weapon_level']})")
    await call.message.edit_text(text, reply_markup=main_menu_kb(), parse_mode="Markdown")

# Помощь
@dp.callback_query(F.data == "menu_help")
async def help_cb(call: CallbackQuery):
    text = ("📜 **МИНИ-ГАЙД ПО ИГРЕ**\n\n"
            "1. **Острова:** Проходи цепочки островов (от слабых к сильным). Каждый остров состоит из 9 врагов. 9-й враг — БОСС. За босса дают постоянный бонус к макс. HP и кучу золота!\n"
            "2. **Магазин:** Покупай легендарные клинки и затачивай их у Кузнеца за белли.\n"
            "3. **Настройки:** Вкачивай свободные очки характеристик (даются за лвл-ап) в Атаку или ХП.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# Настройки
@dp.callback_query(F.data == "menu_settings")
async def settings_cb(call: CallbackQuery):
    p = get_player(call.from_user.id)
    text = (f"⚙️ **НАСТРОЙКИ И ПРОКАЧКА**\n\n"
            f"👤 Имя: {p['name']}\n"
            f"🏴 Фракция: {p['fraction']}\n"
            f"✨ Свободные очки: {p['stat_points']}\n"
            f"❤️ Базовое HP: {p['base_hp']} (Всего: {get_max_hp(p)})\n"
            f"⚔️ Базовая ATK: {p['base_atk']} (Всего: {get_total_atk(p)})\n\n"
            f"_Чтобы сменить ник, просто отправьте новое имя в чат текстом!_")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Вкачать Силу (+2 ATK)", callback_query_data="up_atk"),
         InlineKeyboardButton(text="➕ Вкачать Выносливость (+15 HP)", callback_query_data="up_hp")],
        [InlineKeyboardButton(text="🏴 Сменить Фракцию", callback_query_data="change_fraction")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("up_"))
async def upgrade_stat(call: CallbackQuery):
    p = get_player(call.from_user.id)
    if p['stat_points'] <= 0:
        await call.answer("У вас нет свободных очков характеристик!", show_alert=True)
        return
    
    p['stat_points'] -= 1
    if call.data == "up_atk":
        p['base_atk'] += 2
    else:
        p['base_hp'] += 15
        
    update_player(p)
    await settings_cb(call)

@dp.callback_query(F.data == "change_fraction")
async def change_fraction(call: CallbackQuery):
    p = get_player(call.from_user.id)
    fractions = ["Пираты", "Морской Дозор", "Революционеры"]
    current_idx = fractions.index(p['fraction'])
    p['fraction'] = fractions[(current_idx + 1) % len(fractions)]
    update_player(p)
    await settings_cb(call)

@dp.message(F.text & ~F.text.startswith('/'))
async def change_name_msg(message: Message):
    p = get_player(message.from_user.id)
    if p:
        p['name'] = message.text[:20] # ограничение 20 символов
        update_player(p)
        await message.answer(f"Status: Ваше имя изменено на **{p['name']}**!", parse_mode="Markdown")

# Магазин
@dp.callback_query(F.data == "menu_shop")
async def shop_cb(call: CallbackQuery):
    p = get_player(call.from_user.id)
    text = (f"🛒 **МАГАЗИН И КУЗНИЦА**\n\n"
            f"💰 Баланс: {p['gold']} белли\n"
            f"⚔️ Твое оружие: {p['weapon_name']} [{p['weapon_rank']}] (+{p['weapon_level']})\n")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Купить Оружие", callback_query_data="shop_weapons")],
        [InlineKeyboardButton(text="🔨 Заточить оружие", callback_query_data="shop_forge")],
        [InlineKeyboardButton(text="🎁 Открыть Сундук (500 белли)", callback_query_data="buy_chest")],
        [InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "shop_weapons")
async def shop_weapons_list(call: CallbackQuery):
    p = get_player(call.from_user.id)
    text = f"💰 Твой баланс: {p['gold']} белли\nВыбери оружие для покупки:"
    buttons = []
    for w in WEAPONS_SHOP:
        buttons.append([InlineKeyboardButton(text=f"{w['name']} [{w['rank']}] (+{w['damage']} ATK) — {w['price']} B", callback_query_data=f"buy_w_{w['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_query_data="menu_shop")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("buy_w_"))
async def buy_weapon_proc(call: CallbackQuery):
    w_id = int(call.data.split("_")[2])
    w = next(item for item in WEAPONS_SHOP if item["id"] == w_id)
    p = get_player(call.from_user.id)
    
    if p['gold'] < w['price']:
        await call.answer("Недостаточно золота!", show_alert=True)
        return
        
    p['gold'] -= w['price']
    p['weapon_name'] = w['name']
    p['weapon_rank'] = w['rank']
    p['weapon_dmg'] = w['damage']
    p['weapon_level'] = 1
    update_player(p)
    await call.answer(f"Успешно куплено: {w['name']}!")
    await shop_cb(call)

@dp.callback_query(F.data == "shop_forge")
async def forge_proc(call: CallbackQuery):
    p = get_player(call.from_user.id)
    if p['weapon_name'] == "Кулаки":
        await call.answer("Кулаки нельзя точить! Купите оружие.", show_alert=True)
        return
    cost = int(p['weapon_dmg'] * p['weapon_level'] * 1.5)
    if p['gold'] < cost:
        await call.answer(f"Не хватает белли! Нужно {cost}", show_alert=True)
        return
    p['gold'] -= cost
    p['weapon_level'] += 1
    update_player(p)
    await call.answer(f"Заточка успешна! Теперь +{p['weapon_level']}", show_alert=True)
    await shop_cb(call)

@dp.callback_query(F.data == "buy_chest")
async def buy_chest(call: CallbackQuery):
    p = get_player(call.from_user.id)
    if p['gold'] < 500:
        await call.answer("Нужно 500 белли!", show_alert=True)
        return
    p['gold'] -= 500
    win_gold = random.randint(150, 900)
    win_exp = random.randint(30, 120)
    p['gold'] += win_gold
    p['exp'] += win_exp
    lvl_up = check_lvl_up(p)
    update_player(p)
    
    res = f"🎁 Из сундука выпало:\n💰 {win_gold} белли\n✨ {win_exp} EXP!"
    if lvl_up: res += "\n🎉 УРОВЕНЬ ПОВЫШЕН!"
    await call.answer(res, show_alert=True)
    await shop_cb(call)

# Острова
@dp.callback_query(F.data == "menu_islands")
async def islands_cb(call: CallbackQuery):
    p = get_player(call.from_user.id)
    text = "🗺️ **ВЫБОР ОСТРОВА ДЛЯ БОЯ**\n\nВам предстоит одолеть 9 противников подряд!"
    buttons = []
    for i, island in enumerate(ISLANDS):
        if i <= p['unlocked_island']:
            buttons.append([InlineKeyboardButton(text=f"🏝️ {island['name']} (x{island['mult']})", callback_query_data=f"isl_{i}_1")])
        else:
            buttons.append([InlineKeyboardButton(text=f"🔒 {island['name']}", callback_query_data="isl_locked")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_query_data="to_main")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data == "isl_locked")
async def isl_locked(call: CallbackQuery):
    await call.answer("Этот остров заблокирован! Победите босса на предыдущем.", show_alert=True)

# Боевая система
@dp.callback_query(F.data.startswith("isl_"))
async def island_fight(call: CallbackQuery):
    _, isl_idx, stage = call.data.split("_")
    isl_idx, stage = int(isl_idx), int(stage)
    p = get_player(call.from_user.id)
    island = ISLANDS[isl_idx]
    
    is_boss = (stage == 9)
    enemy_name = island['boss'] if is_boss else f"Пират островов {stage}"
    
    # Расчет статов врага
    if is_boss:
        e_hp = int(60 * island['mult'] * 2.5)
        e_atk = int(8 * island['mult'] * 1.8)
    else:
        e_hp = int(40 * island['mult'] * (1 + stage * 0.1))
        e_atk = int(6 * island['mult'] * (1 + stage * 0.05))
        
    # СИМУЛЯЦИЯ БОЯ НА СЕРВЕРЕ (Пошагово за один клик, чтобы не спамить кнопками)
    p_hp = get_max_hp(p)
    p_atk = get_total_atk(p)
    
    battle_log = f"⚔️ **БОЙ НА ОСТРОВЕ {island['name'].upper()} [{stage}/9]**\n\n"
    battle_log += f"🔴 Противник: {enemy_name} (HP: {e_hp} | ATK: {e_atk})\n\n"
    
    while p_hp > 0 and e_hp > 0:
        crit = 2 if random.random() < 0.15 else 1
        dmg = int(p_atk * random.uniform(0.9, 1.1) * crit)
        e_hp -= dmg
        if e_hp <= 0: break
        
        edmg = int(e_atk * random.uniform(0.8, 1.2))
        p_hp -= edmg

    if p_hp <= 0:
        battle_log += "☠️ **Вы проиграли бой!** Команда оттащила вас на корабль. Подкачайтесь в магазине!"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 На Острова", callback_query_data="menu_islands")]])
        await call.message.edit_text(battle_log, reply_markup=kb, parse_mode="Markdown")
    else:
        # Победа
        gold_reward = int(25 * island['mult'])
        exp_reward = int(20 * island['mult'])
        
        if is_boss:
            gold_reward += int(150 * island['mult'])
            p['base_hp'] += int(10 * island['mult']) # Перманентное ХП за босса
            battle_log += f"🏆 **БОСС ОДОЛЕН!** Остров полностью зачищен!\n❤️ Макс. HP увеличено навсегда!"
            if p['unlocked_island'] == isl_idx and p['unlocked_island'] < len(ISLANDS) - 1:
                p['unlocked_island'] += 1
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗺️ К островам", callback_query_data="menu_islands")]])
        else:
            battle_log += f"✌️ **Победа!** Противник повержен."
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="▶️ Следующий противник", callback_query_data=f"isl_{isl_idx}_{stage+1}")]])
            
        p['gold'] += gold_reward
        p['exp'] += exp_reward
        lvl_up = check_lvl_up(p)
        if lvl_up: battle_log += "\n🎉 **УРОВЕНЬ ПОВЫШЕН! Получено 5 очков прокачки!**"
        
        battle_log += f"\n\n💰 Награда: +{gold_reward} белли, +{exp_reward} EXP"
        update_player(p)
        await call.message.edit_text(battle_log, reply_markup=kb, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    
