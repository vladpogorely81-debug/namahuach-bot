import logging
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from db import Database
from matches_data import get_upcoming_matches, get_match_by_id
from scoring import calculate_result, STAGE_STAKES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
db = Database("data/betting.db")

class BetStates(StatesGroup):
    waiting_score = State()

class ChampStates(StatesGroup):
    waiting_team = State()
    waiting_amount = State()

class AdminStates(StatesGroup):
    waiting_result = State()
    waiting_champion = State()
    waiting_addmatch_teams = State()
    waiting_addmatch_stage = State()
    waiting_addmatch_date = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def notify_admins(text: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception:
            pass

# ─── START / RULES ───────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message):
    db.register_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username)
    photo_path = os.path.join(os.path.dirname(__file__), "welcome.png")
    if os.path.exists(photo_path):
        await msg.answer_photo(FSInputFile(photo_path))
    await msg.answer(
        f"Вас вітає Лєвчік, у вузьких кругах — Старий, у ще вужчих — Старий Намахувач 🎲\n\n"
        f"<b>Команди:</b>\n"
        f"📅 /calendar — календар матчів\n"
        f"🎯 /bet — зробити ставку на матч\n"
        f"🏆 /champion — ставка на чемпіона\n"
        f"💰 /balance — мій баланс\n"
        f"📊 /standings — таблиця учасників\n"
        f"📈 /bets_stat — хто на що поставив\n"
        f"📋 /history — моя історія ставок\n"
        f"📖 /rules — правила\n",
        parse_mode="HTML"
    )

@router.message(Command("rules"))
async def cmd_rules(msg: Message):
    await msg.answer(
        "📖 <b>Правила ставок</b>\n\n"
        "❌ <b>Не вгадав результат</b> — все в банк\n"
        "✅ <b>Вгадав переможця / нічию</b> — повертаєш 50% від суми\n"
        "↩️ <b>Вгадав різницю голів</b> (напр. 3:1 → 2:0) — повернення суми\n"
        "✨ <b>Точний рахунок 1:0, 1:1, 2:1, 2:2</b> — виграш х2\n"
        "🔥 <b>Точний рахунок де голів &gt;4</b> (4:3, 7:1...) — виграш х3\n\n"
        "💵 <b>Розмір ставок:</b>\n"
        "Група — 10 грн · 1/32 — 20 грн · 1/16 — 30 грн\n"
        "1/8 — 40 грн · 1/2 — 50 грн · Фінал — 100 грн\n\n"
        "🏆 <b>Ставка на чемпіона</b> — будь-яка сума, виграш х2\n"
        "Команда: /champion",
        parse_mode="HTML"
    )

# ─── CALENDAR ────────────────────────────────────────────────────────────────

@router.message(Command("calendar"))
async def cmd_calendar(msg: Message):
    await show_calendar(msg, offset=0)

@router.callback_query(F.data.startswith("calendar_"))
async def calendar_page(callback: CallbackQuery):
    offset = int(callback.data.split("_")[1])
    await show_calendar(callback.message, offset=offset, edit=True, user_id=callback.from_user.id)
    await callback.answer()

async def show_calendar(msg, offset=0, edit=False, user_id=None):
    uid = user_id or msg.chat.id
    all_matches = db.get_all_matches_with_bets(uid)
    if not all_matches:
        await msg.answer("📅 Матчів не знайдено")
        return

    page_size = 8
    chunk = all_matches[offset:offset + page_size]

    text = f"📅 <b>Календар матчів</b> ({offset+1}–{offset+len(chunk)} з {len(all_matches)})\n\n"
    for m in chunk:
        if m['score1'] is not None:
            score_str = f"<b>{m['score1']}:{m['score2']}</b> 🏁"
        else:
            score_str = "⏳ очікується"
        bet_str = f"✏️ {m['user_bet']}" if m.get('user_bet') else "⚪ без ставки"
        text += (
            f"<b>{m['team1']} — {m['team2']}</b>\n"
            f"  {m['stage_name']} · {m['stake']}грн · {m['match_date']} · {score_str}\n"
            f"  {bet_str}\n\n"
        )

    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"calendar_{offset - page_size}"))
    if offset + page_size < len(all_matches):
        nav.append(InlineKeyboardButton(text="Далі ➡️", callback_data=f"calendar_{offset + page_size}"))

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🎯 Зробити ставку", callback_data="make_bet")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if edit:
        await msg.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await msg.answer(text, parse_mode="HTML", reply_markup=keyboard)

# ─── CHAMPION BET ─────────────────────────────────────────────────────────────

@router.message(Command("champion"))
async def cmd_champion(msg: Message, state: FSMContext):
    existing = db.get_champion_bet(msg.from_user.id)
    if existing:
        await msg.answer(
            f"🏆 Ти вже поставив на чемпіона!\n\n"
            f"🎯 Команда: <b>{existing['team']}</b>\n"
            f"💰 Сума: <b>{existing['amount']} грн</b>\n"
            f"При перемозі отримаєш: <b>{existing['amount'] * 2} грн</b>",
            parse_mode="HTML"
        )
        return

    teams = db.get_all_teams()
    buttons = []
    row = []
    for i, team in enumerate(teams):
        row.append(InlineKeyboardButton(text=team, callback_data=f"champ_{team}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await msg.answer(
        "🏆 <b>Ставка на чемпіона</b>\n\n"
        "Вибери команду — переможця турніру.\n"
        "При правильному виборі виграш х2!\n\n"
        "👇 Вибери команду:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(F.data.startswith("champ_"))
async def champ_team_selected(callback: CallbackQuery, state: FSMContext):
    team = callback.data[6:]
    await state.set_state(ChampStates.waiting_amount)
    await state.update_data(team=team)
    await callback.message.answer(
        f"🏆 Твій вибір: <b>{team}</b>\n\n"
        f"Введи суму ставки (грн):\n"
        f"Наприклад: <code>100</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ChampStates.waiting_amount)
async def champ_amount_entered(msg: Message, state: FSMContext):
    try:
        amount = int(msg.text.strip())
        if amount <= 0 or amount > 100000:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Введи суму цифрами, наприклад: <code>100</code>", parse_mode="HTML")
        return

    data = await state.get_data()
    team = data["team"]
    db.place_champion_bet(msg.from_user.id, team, amount)
    await state.clear()
    await msg.answer(
        f"✅ Ставка на чемпіона прийнята!\n\n"
        f"🏆 Команда: <b>{team}</b>\n"
        f"💰 Сума: <b>{amount} грн</b>\n"
        f"При перемозі отримаєш: <b>{amount * 2} грн</b>",
        parse_mode="HTML"
    )
    await notify_admins(
        f"🏆 <b>Нова ставка на чемпіона!</b>\n"
        f"👤 {msg.from_user.full_name}\n"
        f"🎯 {team} · {amount} грн"
    )

# ─── MATCH BETS ───────────────────────────────────────────────────────────────

@router.message(Command("bet"))
@router.callback_query(F.data == "make_bet")
async def cmd_bet(event):
    msg = event if isinstance(event, Message) else event.message
    user_id = event.from_user.id
    open_matches = db.get_open_matches_for_betting(user_id)
    if not open_matches:
        await msg.answer("😔 Немає доступних матчів або ти вже поставив на всі відкриті")
        return
    buttons = [[InlineKeyboardButton(
        text=f"⚽ {m['team1']} — {m['team2']} ({m['stage_name']})",
        callback_data=f"betmatch_{m['id']}"
    )] for m in open_matches[:15]]
    await msg.answer("🎯 <b>Вибери матч для ставки:</b>", parse_mode="HTML",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.callback_query(F.data.startswith("betmatch_"))
async def bet_match_selected(callback: CallbackQuery, state: FSMContext):
    match_id = int(callback.data.split("_")[1])
    match = db.get_match(match_id)
    if not match:
        await callback.answer("Матч не знайдено")
        return
    await state.set_state(BetStates.waiting_score)
    await state.update_data(match_id=match_id)
    await callback.message.answer(
        f"⚽ <b>{match['team1']} — {match['team2']}</b>\n"
        f"📍 {match['stage_name']} · Ставка: <b>{match['stake']} грн</b>\n\n"
        f"Введи прогноз у форматі <code>X:Y</code>\n"
        f"Наприклад: <code>2:1</code> або <code>0:0</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(BetStates.waiting_score)
async def process_bet_score(msg: Message, state: FSMContext):
    text = msg.text.strip().replace("-", ":").replace(" ", "")
    parts = text.split(":")
    if len(parts) != 2:
        await msg.answer("❌ Формат: <code>2:1</code>", parse_mode="HTML")
        return
    try:
        g1, g2 = int(parts[0]), int(parts[1])
        if g1 < 0 or g2 < 0 or g1 > 20 or g2 > 20:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Формат: <code>2:1</code>", parse_mode="HTML")
        return

    data = await state.get_data()
    match_id = data["match_id"]
    match = db.get_match(match_id)
    existing = db.get_user_bet(msg.from_user.id, match_id)
    if existing:
        db.update_bet(msg.from_user.id, match_id, g1, g2)
        action = "оновлена"
    else:
        db.place_bet(msg.from_user.id, match_id, g1, g2)
        action = "прийнята"

    await state.clear()
    await msg.answer(
        f"✅ Ставка {action}!\n\n"
        f"⚽ <b>{match['team1']} — {match['team2']}</b>\n"
        f"🎯 Твій прогноз: <b>{g1}:{g2}</b>\n"
        f"💰 Ставка: <b>{match['stake']} грн</b>",
        parse_mode="HTML"
    )
    total_bets = db.get_match_bet_count(match_id)
    total_players = len(db.get_all_users())
    await notify_admins(
        f"🎯 <b>Нова ставка!</b>\n"
        f"👤 {msg.from_user.full_name}\n"
        f"⚽ {match['team1']} — {match['team2']}: <b>{g1}:{g2}</b>\n"
        f"📈 Поставили: {total_bets}/{total_players}"
    )

# ─── BALANCE / STANDINGS / HISTORY ───────────────────────────────────────────

@router.message(Command("balance"))
async def cmd_balance(msg: Message):
    user = db.get_user_stats(msg.from_user.id)
    if not user:
        await msg.answer("Спочатку напиши /start")
        return
    champ = db.get_champion_bet(msg.from_user.id)
    champ_str = f"\n🏆 Чемпіон: <b>{champ['team']}</b> ({champ['amount']} грн)" if champ else ""
    sign = "+" if user['balance'] >= 0 else ""
    await msg.answer(
        f"💰 <b>Твій баланс</b>\n\n"
        f"👤 {msg.from_user.first_name}\n"
        f"📊 Баланс: <b>{sign}{user['balance']} грн</b>\n"
        f"🎯 Ставок: {user['total_bets']} · ✅ {user['wins']} · ❌ {user['losses']} · ↩️ {user['returns']}"
        f"{champ_str}",
        parse_mode="HTML"
    )

@router.message(Command("standings"))
async def cmd_standings(msg: Message):
    rows = db.get_standings()
    if not rows:
        await msg.answer("Поки що немає учасників")
        return
    text = "📊 <b>Таблиця учасників</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        balance = r['balance'] or 0
        sign = "+" if balance >= 0 else ""
        champ_str = f" 🏆{r['champ_team']}" if r.get('champ_team') else ""
        text += f"{medal} <b>{r['name']}</b>{champ_str} — {sign}{balance} грн ({r['total_bets'] or 0} ст.)\n"
    total_bank = db.get_bank_total()
    text += f"\n🏦 <b>Загальний банк: {total_bank} грн</b>"
    await msg.answer(text, parse_mode="HTML")

@router.message(Command("bets_stat"))
async def cmd_bets_stat(msg: Message):
    matches = db.get_matches_with_bet_stats()
    if not matches:
        await msg.answer("Ще немає ставок")
        return
    text = "🎯 <b>Статистика ставок по матчах</b>\n\n"
    for m in matches[:15]:
        if not m['bet_count']:
            continue
        text += f"<b>{m['team1']} — {m['team2']}</b> ({m['stage_name']})\n"
        if m['score1'] is not None:
            text += f"  🏁 Результат: {m['score1']}:{m['score2']}\n"
        text += f"  👥 Поставили: {m['bet_count']} осіб\n"
        for bet_str, cnt in (m['bet_distribution'] or []):
            bar = "▓" * cnt + "░" * (m['bet_count'] - cnt)
            text += f"  {bet_str} — {cnt} чол. {bar}\n"
        text += "\n"
    await msg.answer(text, parse_mode="HTML")

@router.message(Command("history"))
async def cmd_history(msg: Message):
    bets = db.get_user_history(msg.from_user.id)
    champ = db.get_champion_bet(msg.from_user.id)
    if not bets and not champ:
        await msg.answer("📋 Ще немає ставок")
        return
    text = "📋 <b>Твоя історія ставок</b>\n\n"
    if champ:
        if champ['result_delta'] is not None:
            d = champ['result_delta']
            cs = f"✅ +{d} грн" if d > 0 else f"❌ {d} грн"
        else:
            cs = "⏳ очікує"
        text += f"🏆 Чемпіон: <b>{champ['team']}</b> ({champ['amount']} грн) — {cs}\n\n"
    for b in (bets or [])[-15:]:
        if b['result_delta'] is None:
            status = "⏳"
        elif b['result_delta'] > 0:
            status = f"✅ +{b['result_delta']}грн"
        elif b['result_delta'] == 0:
            status = "↩️"
        else:
            status = f"❌ {b['result_delta']}грн"
        score_str = f" → {b['score1']}:{b['score2']}" if b['score1'] is not None else ""
        text += f"⚽ {b['team1']} — {b['team2']}: <b>{b['bet1']}:{b['bet2']}</b>{score_str} {status}\n"
    await msg.answer(text, parse_mode="HTML")

# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return
    await show_admin_menu(msg)

async def show_admin_menu(msg: Message, edit=False):
    pending = db.get_matches_pending_result()
    bank = db.get_bank_total()
    users_count = len(db.get_all_users())

    text = (
        f"🔧 <b>Панель адміна</b>\n\n"
        f"👥 Учасників: <b>{users_count}</b>\n"
        f"🏦 Банк: <b>{bank} грн</b>\n"
        f"⏳ Матчів без результату: <b>{len(pending)}</b>\n"
    )
    buttons = [
        [InlineKeyboardButton(text="⚽ Ввести результат матчу", callback_data="admin_results")],
        [InlineKeyboardButton(text="🏆 Оголосити чемпіона", callback_data="admin_champion")],
        [InlineKeyboardButton(text="➕ Додати матч плейофф", callback_data="admin_addmatch")],
        [InlineKeyboardButton(text="📋 Всі ставки на чемпіона", callback_data="admin_champbets")],
        [InlineKeyboardButton(text="📊 Таблиця учасників", callback_data="admin_standings")],
        [InlineKeyboardButton(text="📢 Розіслати повідомлення", callback_data="admin_broadcast")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    if edit:
        try:
            await msg.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        except Exception:
            await msg.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await msg.answer(text, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    await show_admin_menu(callback.message, edit=True)
    await callback.answer()

# ── Результати матчів ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_results")
async def admin_results(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    pending = db.get_matches_pending_result()
    if not pending:
        await callback.message.edit_text(
            "✅ Всі матчі вже мають результати!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")
            ]])
        )
        await callback.answer()
        return

    text = "⚽ <b>Матчі без результату</b>\n\nВибери матч:\n"
    buttons = []
    for m in pending[:20]:
        bets_count = db.get_match_bet_count(m['id'])
        buttons.append([InlineKeyboardButton(
            text=f"#{m['id']} {m['team1']} — {m['team2']} ({m['stage_name']}) · {bets_count} ст.",
            callback_data=f"admin_setresult_{m['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")])
    await callback.message.edit_text(text, parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_setresult_"))
async def admin_setresult(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    match_id = int(callback.data.split("_")[2])
    match = db.get_match(match_id)
    bets = db.get_match_bets_preview(match_id)

    preview = ""
    if bets:
        preview = "\n\n<b>Прогнози учасників:</b>\n"
        for b in bets:
            preview += f"  {b['name']}: {b['bet1']}:{b['bet2']}\n"

    await state.set_state(AdminStates.waiting_result)
    await state.update_data(match_id=match_id)
    await callback.message.answer(
        f"⚽ <b>{match['team1']} — {match['team2']}</b>\n"
        f"📍 {match['stage_name']} · {match['match_date']}"
        f"{preview}\n\n"
        f"Введи фінальний рахунок у форматі <code>X:Y</code>\n"
        f"Наприклад: <code>2:1</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.waiting_result)
async def admin_result_entered(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    text = msg.text.strip().replace("-", ":").replace(" ", "")
    parts = text.split(":")
    if len(parts) != 2:
        await msg.answer("❌ Формат: <code>2:1</code>", parse_mode="HTML")
        return
    try:
        s1, s2 = int(parts[0]), int(parts[1])
        if s1 < 0 or s2 < 0 or s1 > 20 or s2 > 20:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Формат: <code>2:1</code>", parse_mode="HTML")
        return

    data = await state.get_data()
    match_id = data["match_id"]
    match = db.get_match(match_id)

    # Кнопки підтвердження
    await state.update_data(s1=s1, s2=s2)
    await msg.answer(
        f"⚽ <b>{match['team1']} — {match['team2']}</b>\n"
        f"Рахунок: <b>{s1}:{s2}</b>\n\n"
        f"Підтверджуєш?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Так, зафіксувати", callback_data="admin_confirm_result"),
            InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_results"),
        ]])
    )

@router.callback_query(F.data == "admin_confirm_result")
async def admin_confirm_result(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    data = await state.get_data()
    match_id, s1, s2 = data["match_id"], data["s1"], data["s2"]
    match = db.get_match(match_id)
    await state.clear()

    db.set_match_result(match_id, s1, s2)
    results = db.calculate_and_save_results(match_id, s1, s2)

    # Зведення для адміна
    text = (
        f"🏁 <b>Результат зафіксовано!</b>\n\n"
        f"⚽ {match['team1']} — {match['team2']}: <b>{s1}:{s2}</b>\n\n"
        f"<b>Підсумки:</b>\n"
    )
    for r in results:
        sign = "+" if r['delta'] > 0 else ""
        emoji = "✅" if r['delta'] > 0 else ("↩️" if r['delta'] == 0 else "❌")
        text += f"{emoji} {r['name']}: {r['bet1']}:{r['bet2']} → {sign}{r['delta']} грн\n"

    total_bank = db.get_bank_total()
    text += f"\n🏦 Банк: <b>{total_bank} грн</b>"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚽ Ввести ще результат", callback_data="admin_results"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="admin_menu"),
    ]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_btn)
    await callback.answer("✅ Зафіксовано!")

    # Особисте сповіщення кожному
    results_by_user = {r['user_id']: r for r in results}
    for user in db.get_all_users():
        uid = user['user_id']
        if uid in ADMIN_IDS:
            continue
        r = results_by_user.get(uid)
        try:
            if r:
                sign = "+" if r['delta'] > 0 else ""
                label = r['label']
                if r['delta'] > 0:
                    if 'х3' in label:
                        mood = "😱 Нажаль ваша ставка зіграла, гроші ваші... та ще й утричі! Це взагалі законно?!"
                    elif 'х2' in label:
                        mood = "😔 Нажаль ваша ставка зіграла, гроші ваші. Удвічі. Сумно."
                    else:
                        mood = "🙁 Нажаль ваша ставка зіграла, гроші ваші."
                elif r['delta'] == 0:
                    mood = "🤝 Нічия — і ставка нічия. Повернення, так би мовити."
                else:
                    mood = "🥳 Юху, ставка не зіграла, грошики мої!"
                personal = (
                    f"🏁 <b>{match['team1']} — {match['team2']}</b>: {s1}:{s2}\n\n"
                    f"Твій прогноз: <b>{r['bet1']}:{r['bet2']}</b>\n"
                    f"Результат: <b>{sign}{r['delta']} грн</b>\n\n"
                    f"{mood}\n\n"
                    f"💰 Баланс: /balance"
                )
            else:
                personal = (
                    f"🏁 <b>{match['team1']} — {match['team2']}</b>: {s1}:{s2}\n"
                    f"⚪ Ти не ставив на цей матч. Наступного разу не пропусти!"
                )
            await bot.send_message(uid, personal, parse_mode="HTML")
        except Exception:
            pass

# ── Чемпіон ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_champion")
async def admin_champion(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    teams = db.get_all_teams()
    buttons = []
    row = []
    for team in teams:
        row.append(InlineKeyboardButton(text=team, callback_data=f"admin_champ_{team}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")])
    await callback.message.edit_text(
        "🏆 <b>Оголосити чемпіона</b>\n\nВибери команду-переможця:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_champ_"))
async def admin_champ_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    team = callback.data[12:]
    bets = db.get_all_champion_bets()
    count = sum(1 for b in bets if b['team'] == team)
    await callback.message.edit_text(
        f"🏆 Чемпіон: <b>{team}</b>\n\n"
        f"На цю команду поставили: {count} учасників\n\n"
        f"Підтверджуєш? Це розрахує всі ставки на чемпіона!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Так, оголосити!", callback_data=f"admin_champconfirm_{team}"),
            InlineKeyboardButton(text="❌ Назад", callback_data="admin_champion"),
        ]])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_champconfirm_"))
async def admin_champconfirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    winner = callback.data[19:]
    results = db.calculate_champion_results(winner)

    text = f"🏆 <b>Чемпіон — {winner}!</b>\n\n<b>Результати:</b>\n"
    for r in results:
        sign = "+" if r['delta'] > 0 else ""
        emoji = "🎉" if r['delta'] > 0 else "❌"
        text += f"{emoji} {r['name']}: {r['team']} → {sign}{r['delta']} грн\n"

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 Меню", callback_data="admin_menu")
        ]])
    )
    await callback.answer("🏆 Зафіксовано!")

    for r in results:
        try:
            sign = "+" if r['delta'] > 0 else ""
            emoji = "🎉" if r['delta'] > 0 else "❌"
            await bot.send_message(
                r['user_id'],
                f"🏆 <b>Чемпіон турніру — {winner}!</b>\n\n"
                f"Твоя ставка: <b>{r['team']}</b>\n"
                f"{emoji} Результат: <b>{sign}{r['delta']} грн</b>\n\n"
                f"💰 Баланс: /balance",
                parse_mode="HTML"
            )
        except Exception:
            pass

# ── Додати матч ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_addmatch")
async def admin_addmatch(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    await state.set_state(AdminStates.waiting_addmatch_teams)
    await callback.message.answer(
        "➕ <b>Додати матч плейофф</b>\n\n"
        "Введи назви команд через тире:\n"
        "<code>Бразилія - Аргентина</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.waiting_addmatch_teams)
async def addmatch_teams(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.replace("—", "-").split("-", 1)
    if len(parts) != 2:
        await msg.answer("❌ Формат: <code>Бразилія - Аргентина</code>", parse_mode="HTML")
        return
    team1, team2 = parts[0].strip(), parts[1].strip()
    await state.update_data(team1=team1, team2=team2)
    await state.set_state(AdminStates.waiting_addmatch_stage)
    await msg.answer(
        f"⚽ <b>{team1} — {team2}</b>\n\nВибери стадію:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1/32 (20 грн)", callback_data="stage_r32"),
             InlineKeyboardButton(text="1/16 (30 грн)", callback_data="stage_r16")],
            [InlineKeyboardButton(text="1/8 (40 грн)", callback_data="stage_qf"),
             InlineKeyboardButton(text="1/2 (50 грн)", callback_data="stage_sf")],
            [InlineKeyboardButton(text="🏆 Фінал (100 грн)", callback_data="stage_final")],
        ])
    )

@router.callback_query(F.data.startswith("stage_"))
async def addmatch_stage(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    stage = callback.data[6:]
    await state.update_data(stage=stage)
    await state.set_state(AdminStates.waiting_addmatch_date)
    await callback.message.answer(
        "📆 Введи дату матчу:\nНаприклад: <code>05.07</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminStates.waiting_addmatch_date)
async def addmatch_date(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    date = msg.text.strip()
    data = await state.get_data()
    await state.clear()

    stage_names = {"r32": "1/32", "r16": "1/16", "qf": "1/8", "sf": "1/2", "final": "Фінал"}
    stage_name = stage_names.get(data['stage'], data['stage'])
    stake = STAGE_STAKES.get(data['stage'], 20)

    match_id = db.add_match(data['team1'], data['team2'], data['stage'], stage_name, stake, date)
    await msg.answer(
        f"✅ Матч #{match_id} додано!\n\n"
        f"⚽ <b>{data['team1']} — {data['team2']}</b>\n"
        f"📍 {stage_name} · {stake} грн · {date}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏠 Меню адміна", callback_data="admin_menu")
        ]])
    )

# ── Інші кнопки адмінпанелі ────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_champbets")
async def admin_champbets(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    bets = db.get_all_champion_bets()
    if not bets:
        text = "🏆 Ставок на чемпіона ще немає"
    else:
        text = "🏆 <b>Ставки на чемпіона:</b>\n\n"
        for b in bets:
            text += f"👤 {b['name']}: <b>{b['team']}</b> — {b['amount']} грн\n"
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")
        ]])
    )
    await callback.answer()

@router.callback_query(F.data == "admin_standings")
async def admin_standings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    rows = db.get_standings()
    bank = db.get_bank_total()
    if not rows:
        text = "Поки що немає даних"
    else:
        text = "📊 <b>Таблиця учасників</b>\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(rows):
            medal = medals[i] if i < 3 else f"{i+1}."
            sign = "+" if r['balance'] >= 0 else ""
            champ_str = f" 🏆{r['champ_team']}" if r.get('champ_team') else ""
            text += f"{medal} <b>{r['name']}</b>{champ_str} — {sign}{r['balance']} грн ({r['total_bets']} ст.)\n"
        text += f"\n🏦 <b>Загальний банк: {bank} грн</b>"
    await callback.message.answer(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu")
        ]])
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔")
        return
    await state.set_state(AdminStates.waiting_addmatch_teams)  # reuse state for simplicity
    await callback.message.answer(
        "📢 Введи текст для розсилки всім учасникам:"
    )
    await callback.answer()

@router.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return
    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        await msg.answer("Формат: /broadcast Текст")
        return
    users = db.get_all_users()
    sent, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(user['user_id'], f"📢 {text}")
            sent += 1
        except Exception:
            failed += 1
    await msg.answer(f"✅ Відправлено: {sent}, не вдалось: {failed}")

@router.message(Command("reset_matches"))
async def cmd_reset_matches(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return
    db.reset_and_reseed_matches()
    await msg.answer("✅ Матчі перезавантажені з правильного розкладу!\n\nТепер /calendar покаже всі 72 матчі по хронології.")

@router.message(Command("bank"))
async def cmd_bank(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return
    total = db.get_bank_total()
    await msg.answer(f"🏦 <b>Загальний банк: {total} грн</b>", parse_mode="HTML")

# ─── MAIN ────────────────────────────────────────────────────────────────────

async def main():
    dp.include_router(router)
    db.init()
    db.seed_wc2026_matches()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
