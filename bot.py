import os
import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = os.getenv("8264886297:AAEs4iAZ2toT6j2-rohAmsxg0RosEeVnUT0", "")
ADMIN_CHAT_ID = int(os.getenv("451706092", "0"))
CHANNEL_URL = "https://t.me/bloome_woman"

TEXT_1 = (
    "Сат Нам! Здесь вы можете записаться на консультацию или занятия с учителем "
    "Кундалини йоги - Ади Навприт.\n"
    "Какой формат работы вы хотели бы начать ?"
)
TEXT_2 = "Оставьте ссылку на ваш телеграм, чтобы Ади Навприт связалась с вами в ближайшее время."
TEXT_3 = (
    "Благодарю! В ближайшее время Ади Навприт свяжется с вами!\n"
    f"А пока подписывайтесь на телеграм канал BLOOME - Кундалини йога для женщин ({CHANNEL_URL})."
)

OPTIONS = [
    ("Консультация", "opt_consult"),
    ("40 дней сопровождения", "opt_40days"),
    ("Сопровождение беременности", "opt_pregnancy"),
    ("Индивидуальный занятия для женщин", "opt_individual"),
]

def options_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=data)]
            for title, data in OPTIONS
        ]
    )

class Form(StatesGroup):
    choosing = State()
    waiting_contact = State()

TG_RE = re.compile(r"^(@[\w\d_]{3,}|https?://t\.me/[\w\d_]{3,}|t\.me/[\w\d_]{3,})$", re.IGNORECASE)

def normalize_tg(value: str) -> str:
    v = value.strip()
    if v.lower().startswith("t.me/"):
        v = "https://" + v
    return v

dp = Dispatcher()

@dp.message(F.text.startswith("/start"))
async def start(message: Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    start_param = parts[1] if len(parts) > 1 else ""
    await state.clear()
    await state.update_data(start_param=start_param)
    await message.answer(TEXT_1, reply_markup=options_kb())
    await state.set_state(Form.choosing)

@dp.callback_query(Form.choosing)
async def choose_option(call: CallbackQuery, state: FSMContext):
    title_map = {data: title for title, data in OPTIONS}
    selected_title = title_map.get(call.data, call.data)
    await state.update_data(selected=selected_title)
    await call.message.answer(TEXT_2)
    await call.answer()
    await state.set_state(Form.waiting_contact)

@dp.message(Form.waiting_contact, F.text)
async def receive_contact(message: Message, state: FSMContext):
    tg = normalize_tg(message.text)
    if not TG_RE.match(tg):
        await message.answer(
            "Пожалуйста, отправьте ваш Telegram в одном из форматов:\n"
            "- @username\n- https://t.me/username\n- t.me/username"
        )
        return

    data = await state.get_data()
    selected_title = data.get("selected", "-")
    start_param = data.get("start_param", "")

    u = message.from_user
    user_line = f"{u.full_name} (id: {u.id})"
    if u.username:
        user_line += f" @{u.username}"

    admin_text = (
        "🆕 New Kundalini Lead\n\n"
        f"👤 User: {user_line}\n"
        f"📌 Format: {selected_title}\n"
        f"🔗 Contact (TG): {tg}\n"
    )
    if start_param:
        admin_text += f"🏷 start param: {start_param}\n"

    await message.bot.send_message(ADMIN_CHAT_ID, admin_text)
    await message.answer(TEXT_3)
    await state.clear()

@dp.message(Form.waiting_contact)
async def receive_non_text(message: Message):
    await message.answer("Пожалуйста, отправьте ссылку или @username текстом 🙂")

# ADMIN CHAT ID bulmak için mini komut (3. aşamada kullanacağız)
@dp.message(F.text == "/id")
async def myid(message: Message):
    await message.answer(f"Your ID: {message.from_user.id}\nChat ID: {message.chat.id}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

