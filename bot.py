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

class AdminStates(StatesGroup):
    waiting_result = State()
    waiting_custom_match = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ─── USER COMMANDS ──────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message):
    db.register_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username)
    import os
    photo_path = os.path.join(os.path.dirname(__file__), "welcome.png")
    if os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await msg.answer_photo(photo)
    await msg.answer(
        f"Вас вітає Лєвчік, у вузьких кругах — Старий, у ще вужчих — Старий Намахувач 🎲\n\n"
        f"<b>Команди:</b>\n"
        f"📅 /calendar — календар матчів\n"
        f"🎯 /bet — зробити ставку\n"
        f"💰 /balance — мій баланс\n"
        f"🏆 /standings — таблиця учасників\n"
        f"📋 /history — моя історія ставок\n"
        f"📖 /rules — правила\n",
        parse_mode="HTML"
    )

@router.message(Command("rules"))
async def cmd_rules(msg: Message):
    await msg.answer(
        "📖 <b>Правила ставок</b>\n\n"
        "❌ <b>Не вгадав результат</b> — все в банк\n"
        "✅ <b>Вгадав переможця / нічию</b> — повертаєш 50% від суми ставки\n"
        "↩️ <b>Вгадав різницю голів</b> (напр. 3:1 → 2:0) — повернення суми\n"
        "✨ <b>Точний рахунок 1:0, 1:1, 2:1, 2:2</b> — виграш х2\n"
        "🔥 <b>Точний рахунок де голів &gt;4</b> (4:3, 7:1...) — виграш х3\n\n"
        "💵 <b>Розмір ставок:</b>\n"
        "Група — 10 грн\n"
        "1/32 — 20 грн\n"
        "1/16 — 30 грн\n"
        "1/8 — 40 грн\n"
        "1/2 — 50 грн\n"
        "Фінал — 100 грн\n\n"
        "🏆 <b>Ставка на чемпіона</b> — до початку турніру, виграш х2",
        parse_mode="HTML"
    )

@router.message(Command("calendar"))
async def cmd_calendar(msg: Message):
    matches = db.get_upcoming_matches_with_bets(msg.from_user.id)
    if not matches:
        await msg.answer("📅 Матчів не знайдено або всі вже зіграні")
        return

    text = "📅 <b>Найближчі матчі</b>\n\n"
    for m in matches[:10]:
        bet_info = f"  ✏️ Твоя ставка: {m['user_bet']}" if m.get('user_bet') else "  ⚪ Ставки немає"
        result_info = f"  🏁 Результат: {m['score1']}:{m['score2']}" if m['score1'] is not None else ""
        text += (
            f"<b>#{m['id']} {m['team1']} — {m['team2']}</b>\n"
            f"  📍 {m['stage_name']} · {m['stake']} грн\n"
            f"  📆 {m['match_date']}\n"
            f"{bet_info}\n"
            f"{result_info}\n\n"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Зробити ставку", callback_data="make_bet")]
    ])
    await msg.answer(text, parse_mode="HTML", reply_markup=keyboard)

@router.message(Command("bet"))
@router.callback_query(F.data == "make_bet")
async def cmd_bet(event):
    msg = event if isinstance(event, Message) else event.message
    user_id = event.from_user.id

    open_matches = db.get_open_matches_for_betting(user_id)
    if not open_matches:
        await msg.answer("😔 Немає доступних матчів для ставок (або ти вже поставив на всі відкриті)")
        return

    buttons = []
    for m in open_matches[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"⚽ {m['team1']} — {m['team2']} ({m['stage_name']})",
            callback_data=f"betmatch_{m['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer("🎯 <b>Вибери матч для ставки:</b>", parse_mode="HTML", reply_markup=keyboard)
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
        await msg.answer("❌ Невірний формат. Введіть як <code>2:1</code>", parse_mode="HTML")
        return
    try:
        g1, g2 = int(parts[0]), int(parts[1])
        if g1 < 0 or g2 < 0 or g1 > 20 or g2 > 20:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Невірний формат. Введіть як <code>2:1</code>", parse_mode="HTML")
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

@router.message(Command("balance"))
async def cmd_balance(msg: Message):
    user = db.get_user_stats(msg.from_user.id)
    if not user:
        await msg.answer("Спочатку напиши /start")
        return

    balance = user['balance']
    sign = "+" if balance >= 0 else ""
    await msg.answer(
        f"💰 <b>Твій баланс</b>\n\n"
        f"👤 {msg.from_user.first_name}\n"
        f"📊 Баланс: <b>{sign}{balance} грн</b>\n"
        f"🎯 Ставок зроблено: {user['total_bets']}\n"
        f"✅ Виграно: {user['wins']}\n"
        f"❌ Програно: {user['losses']}\n"
        f"↩️ Повернень: {user['returns']}",
        parse_mode="HTML"
    )

@router.message(Command("standings"))
async def cmd_standings(msg: Message):
    rows = db.get_standings()
    if not rows:
        await msg.answer("Поки що немає даних")
        return

    text = "🏆 <b>Таблиця учасників</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        sign = "+" if r['balance'] >= 0 else ""
        text += f"{medal} <b>{r['name']}</b> — {sign}{r['balance']} грн  ({r['total_bets']} ставок)\n"

    total_bank = db.get_bank_total()
    text += f"\n🏦 <b>Загальний банк: {total_bank} грн</b>"
    await msg.answer(text, parse_mode="HTML")

@router.message(Command("history"))
async def cmd_history(msg: Message):
    bets = db.get_user_history(msg.from_user.id)
    if not bets:
        await msg.answer("📋 Ще немає завершених ставок")
        return

    text = "📋 <b>Твоя історія ставок</b>\n\n"
    for b in bets[-15:]:
        if b['result_delta'] is None:
            status = "⏳ Очікує"
        elif b['result_delta'] > 0:
            status = f"✅ +{b['result_delta']} грн"
        elif b['result_delta'] == 0:
            status = f"↩️ Повернення"
        else:
            status = f"❌ {b['result_delta']} грн"
        text += f"⚽ {b['team1']} — {b['team2']}: прогноз <b>{b['bet1']}:{b['bet2']}</b>"
        if b['score1'] is not None:
            text += f" (рахунок {b['score1']}:{b['score2']})"
        text += f" {status}\n"

    await msg.answer(text, parse_mode="HTML")

# ─── ADMIN COMMANDS ──────────────────────────────────────────────────────────

@router.message(Command("result"))
async def cmd_result(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    parts = msg.text.split()
    if len(parts) != 4:
        await msg.answer("Формат: /result <match_id> <голів1> <голів2>\nПриклад: /result 5 2 1")
        return

    try:
        match_id, s1, s2 = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        await msg.answer("❌ Невірний формат")
        return

    match = db.get_match(match_id)
    if not match:
        await msg.answer(f"Матч #{match_id} не знайдено")
        return

    db.set_match_result(match_id, s1, s2)
    results = db.calculate_and_save_results(match_id, s1, s2)

    text = (
        f"🏁 <b>Результат зафіксовано!</b>\n\n"
        f"⚽ {match['team1']} — {match['team2']}: <b>{s1}:{s2}</b>\n\n"
        f"<b>Підсумки ставок:</b>\n"
    )
    for r in results:
        sign = "+" if r['delta'] > 0 else ""
        text += f"👤 {r['name']}: {r['bet1']}:{r['bet2']} → {sign}{r['delta']} грн ({r['label']})\n"

    await msg.answer(text, parse_mode="HTML")

@router.message(Command("addmatch"))
async def cmd_addmatch(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    parts = msg.text.split("|")
    if len(parts) < 3:
        await msg.answer(
            "Формат: /addmatch Команда1 | Команда2 | стадія | дата\n"
            "Стадії: group, r32, r16, qf, sf, final\n"
            "Приклад: /addmatch Бразилія | Аргентина | sf | 2026-07-07"
        )
        return

    cmd_parts = parts[0].split(None, 1)
    team1 = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""
    team2 = parts[1].strip()
    stage = parts[2].strip().lower() if len(parts) > 2 else "group"
    date = parts[3].strip() if len(parts) > 3 else "TBD"

    stage_names = {"group": "Група", "r32": "1/32", "r16": "1/16", "qf": "1/4", "sf": "1/2", "final": "Фінал"}
    stage_name = stage_names.get(stage, stage)
    stake = STAGE_STAKES.get(stage, 10)

    match_id = db.add_match(team1, team2, stage, stage_name, stake, date)
    await msg.answer(f"✅ Матч #{match_id} додано: {team1} — {team2} ({stage_name}, {stake} грн, {date})")

@router.message(Command("matches"))
async def cmd_matches(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    matches = db.get_all_matches()
    if not matches:
        await msg.answer("Матчів немає")
        return

    text = "📋 <b>Всі матчі:</b>\n\n"
    for m in matches:
        result = f" → {m['score1']}:{m['score2']}" if m['score1'] is not None else " → ⏳"
        text += f"#{m['id']} {m['team1']} — {m['team2']} ({m['stage_name']}){result}\n"

    await msg.answer(text, parse_mode="HTML")

@router.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        await msg.answer("Формат: /broadcast Текст повідомлення")
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

@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    await msg.answer(
        "🔧 <b>Команди адміна:</b>\n\n"
        "/matches — список всіх матчів\n"
        "/result <id> <г1> <г2> — ввести результат\n"
        "  Приклад: /result 5 2 1\n\n"
        "/addmatch Команда1 | Команда2 | стадія | дата\n"
        "  Стадії: group, r32, r16, qf, sf, final\n\n"
        "/broadcast Текст — розіслати всім\n"
        "/bank — стан банку\n",
        parse_mode="HTML"
    )

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
@router.message(CommandStart())
async def cmd_start(msg: Message):
    db.register_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username)
    await msg.answer(
        f"🎲 <b>Старий намахувач!</b>\n\n"
        f"Вітаємо, <b>{msg.from_user.first_name}</b>!\n"
        f"Час намахувати на ЧС 2026 🏆\n\n"
        f"<b>Команди:</b>\n"
        f"📅 /calendar — календар матчів\n"
        f"🎯 /bet — зробити ставку\n"
        f"💰 /balance — мій баланс\n"
        f"🏆 /standings — таблиця учасників\n"
        f"📋 /history — моя історія ставок\n"
        f"📖 /rules — правила\n",
        parse_mode="HTML"
    )

@router.message(Command("rules"))
async def cmd_rules(msg: Message):
    await msg.answer(
        "📖 <b>Правила ставок</b>\n\n"
        "❌ <b>Не вгадав результат</b> — все в банк\n"
        "✅ <b>Вгадав переможця / нічию</b> — повертаєш 50% від суми ставки\n"
        "↩️ <b>Вгадав різницю голів</b> (напр. 3:1 → 2:0) — повернення суми\n"
        "✨ <b>Точний рахунок 1:0, 1:1, 2:1, 2:2</b> — виграш х2\n"
        "🔥 <b>Точний рахунок де голів &gt;4</b> (4:3, 7:1...) — виграш х3\n\n"
        "💵 <b>Розмір ставок:</b>\n"
        "Група — 10 грн\n"
        "1/32 — 20 грн\n"
        "1/16 — 30 грн\n"
        "1/8 — 40 грн\n"
        "1/2 — 50 грн\n"
        "Фінал — 100 грн\n\n"
        "🏆 <b>Ставка на чемпіона</b> — до початку турніру, виграш х2",
        parse_mode="HTML"
    )

@router.message(Command("calendar"))
async def cmd_calendar(msg: Message):
    matches = db.get_upcoming_matches_with_bets(msg.from_user.id)
    if not matches:
        await msg.answer("📅 Матчів не знайдено або всі вже зіграні")
        return

    text = "📅 <b>Найближчі матчі</b>\n\n"
    for m in matches[:10]:
        bet_info = f"  ✏️ Твоя ставка: {m['user_bet']}" if m.get('user_bet') else "  ⚪ Ставки немає"
        result_info = f"  🏁 Результат: {m['score1']}:{m['score2']}" if m['score1'] is not None else ""
        text += (
            f"<b>#{m['id']} {m['team1']} — {m['team2']}</b>\n"
            f"  📍 {m['stage_name']} · {m['stake']} грн\n"
            f"  📆 {m['match_date']}\n"
            f"{bet_info}\n"
            f"{result_info}\n\n"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Зробити ставку", callback_data="make_bet")]
    ])
    await msg.answer(text, parse_mode="HTML", reply_markup=keyboard)

@router.message(Command("bet"))
@router.callback_query(F.data == "make_bet")
async def cmd_bet(event):
    msg = event if isinstance(event, Message) else event.message
    user_id = event.from_user.id

    open_matches = db.get_open_matches_for_betting(user_id)
    if not open_matches:
        await msg.answer("😔 Немає доступних матчів для ставок (або ти вже поставив на всі відкриті)")
        return

    buttons = []
    for m in open_matches[:10]:
        buttons.append([InlineKeyboardButton(
            text=f"⚽ {m['team1']} — {m['team2']} ({m['stage_name']})",
            callback_data=f"betmatch_{m['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer("🎯 <b>Вибери матч для ставки:</b>", parse_mode="HTML", reply_markup=keyboard)
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
        await msg.answer("❌ Невірний формат. Введіть як <code>2:1</code>", parse_mode="HTML")
        return
    try:
        g1, g2 = int(parts[0]), int(parts[1])
        if g1 < 0 or g2 < 0 or g1 > 20 or g2 > 20:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Невірний формат. Введіть як <code>2:1</code>", parse_mode="HTML")
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

@router.message(Command("balance"))
async def cmd_balance(msg: Message):
    user = db.get_user_stats(msg.from_user.id)
    if not user:
        await msg.answer("Спочатку напиши /start")
        return

    balance = user['balance']
    sign = "+" if balance >= 0 else ""
    await msg.answer(
        f"💰 <b>Твій баланс</b>\n\n"
        f"👤 {msg.from_user.first_name}\n"
        f"📊 Баланс: <b>{sign}{balance} грн</b>\n"
        f"🎯 Ставок зроблено: {user['total_bets']}\n"
        f"✅ Виграно: {user['wins']}\n"
        f"❌ Програно: {user['losses']}\n"
        f"↩️ Повернень: {user['returns']}",
        parse_mode="HTML"
    )

@router.message(Command("standings"))
async def cmd_standings(msg: Message):
    rows = db.get_standings()
    if not rows:
        await msg.answer("Поки що немає даних")
        return

    text = "🏆 <b>Таблиця учасників</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        sign = "+" if r['balance'] >= 0 else ""
        text += f"{medal} <b>{r['name']}</b> — {sign}{r['balance']} грн  ({r['total_bets']} ставок)\n"

    total_bank = db.get_bank_total()
    text += f"\n🏦 <b>Загальний банк: {total_bank} грн</b>"
    await msg.answer(text, parse_mode="HTML")

@router.message(Command("history"))
async def cmd_history(msg: Message):
    bets = db.get_user_history(msg.from_user.id)
    if not bets:
        await msg.answer("📋 Ще немає завершених ставок")
        return

    text = "📋 <b>Твоя історія ставок</b>\n\n"
    for b in bets[-15:]:
        if b['result_delta'] is None:
            status = "⏳ Очікує"
        elif b['result_delta'] > 0:
            status = f"✅ +{b['result_delta']} грн"
        elif b['result_delta'] == 0:
            status = f"↩️ Повернення"
        else:
            status = f"❌ {b['result_delta']} грн"
        text += f"⚽ {b['team1']} — {b['team2']}: прогноз <b>{b['bet1']}:{b['bet2']}</b>"
        if b['score1'] is not None:
            text += f" (рахунок {b['score1']}:{b['score2']})"
        text += f" {status}\n"

    await msg.answer(text, parse_mode="HTML")

# ─── ADMIN COMMANDS ──────────────────────────────────────────────────────────

@router.message(Command("result"))
async def cmd_result(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    parts = msg.text.split()
    if len(parts) != 4:
        await msg.answer("Формат: /result <match_id> <голів1> <голів2>\nПриклад: /result 5 2 1")
        return

    try:
        match_id, s1, s2 = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        await msg.answer("❌ Невірний формат")
        return

    match = db.get_match(match_id)
    if not match:
        await msg.answer(f"Матч #{match_id} не знайдено")
        return

    db.set_match_result(match_id, s1, s2)
    results = db.calculate_and_save_results(match_id, s1, s2)

    text = (
        f"🏁 <b>Результат зафіксовано!</b>\n\n"
        f"⚽ {match['team1']} — {match['team2']}: <b>{s1}:{s2}</b>\n\n"
        f"<b>Підсумки ставок:</b>\n"
    )
    for r in results:
        sign = "+" if r['delta'] > 0 else ""
        text += f"👤 {r['name']}: {r['bet1']}:{r['bet2']} → {sign}{r['delta']} грн ({r['label']})\n"

    await msg.answer(text, parse_mode="HTML")

@router.message(Command("addmatch"))
async def cmd_addmatch(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    parts = msg.text.split("|")
    if len(parts) < 3:
        await msg.answer(
            "Формат: /addmatch Команда1 | Команда2 | стадія | дата\n"
            "Стадії: group, r32, r16, qf, sf, final\n"
            "Приклад: /addmatch Бразилія | Аргентина | sf | 2026-07-07"
        )
        return

    cmd_parts = parts[0].split(None, 1)
    team1 = cmd_parts[1].strip() if len(cmd_parts) > 1 else ""
    team2 = parts[1].strip()
    stage = parts[2].strip().lower() if len(parts) > 2 else "group"
    date = parts[3].strip() if len(parts) > 3 else "TBD"

    stage_names = {"group": "Група", "r32": "1/32", "r16": "1/16", "qf": "1/4", "sf": "1/2", "final": "Фінал"}
    stage_name = stage_names.get(stage, stage)
    stake = STAGE_STAKES.get(stage, 10)

    match_id = db.add_match(team1, team2, stage, stage_name, stake, date)
    await msg.answer(f"✅ Матч #{match_id} додано: {team1} — {team2} ({stage_name}, {stake} грн, {date})")

@router.message(Command("matches"))
async def cmd_matches(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    matches = db.get_all_matches()
    if not matches:
        await msg.answer("Матчів немає")
        return

    text = "📋 <b>Всі матчі:</b>\n\n"
    for m in matches:
        result = f" → {m['score1']}:{m['score2']}" if m['score1'] is not None else " → ⏳"
        text += f"#{m['id']} {m['team1']} — {m['team2']} ({m['stage_name']}){result}\n"

    await msg.answer(text, parse_mode="HTML")

@router.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        await msg.answer("Формат: /broadcast Текст повідомлення")
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

@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Тільки для адміна")
        return

    await msg.answer(
        "🔧 <b>Команди адміна:</b>\n\n"
        "/matches — список всіх матчів\n"
        "/result <id> <г1> <г2> — ввести результат\n"
        "  Приклад: /result 5 2 1\n\n"
        "/addmatch Команда1 | Команда2 | стадія | дата\n"
        "  Стадії: group, r32, r16, qf, sf, final\n\n"
        "/broadcast Текст — розіслати всім\n"
        "/bank — стан банку\n",
        parse_mode="HTML"
    )

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
