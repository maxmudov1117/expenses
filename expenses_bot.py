import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.filters import Command
import asyncio

# ==== Telegram Bot Token ====
TOKEN = "8002240284:AAFeoh7s5uFTjf6B2Cs290n4-JBc8m4HMA8"

# ==== SQLite bazasi ====
DB_NAME = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Xarajatlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            created_at TEXT,
            description TEXT,
            amount INTEGER,
            category TEXT
        )
    """)

    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT
        )
    """)

    conn.commit()
    conn.close()

# ==== FUNKSIYALAR ====
def is_registered(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return bool(user)

def register_user(user_id: int, full_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
    conn.commit()
    conn.close()

def add_expense(user_id: int, description: str, amount: int, category: str) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, created_at, description, amount, category) VALUES (?, ?, ?, ?, ?)",
        (user_id, str(datetime.now())[:10], description, amount, category)
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return f"✅ Xarajat qo'shildi (ID: {expense_id})"

def list_expenses_inline(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, description, amount, category FROM expenses WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return [("Hech qanday xarajat topilmadi.", None)]

    result = []
    for row in rows:
        text = (
            f"🆔 <b>ID:</b> {row[0]}\n"
            f"📅 <b>Sana:</b> {row[1]}\n"
            f"📝 <b>Tavsif:</b> {row[2]}\n"
            f"💵 <b>Summa:</b> {row[3]} so'm\n"
            f"🏷 <b>Kategoriya:</b> {row[4]}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"delete_{row[0]}")]
            ]
        )
        result.append((text, keyboard))
    return result

def total_summary(user_id: int) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return f"💰 Umumiy xarajatlar: {total if total else 0} so'm"

def monthly_summary(user_id: int, month: int) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%m', created_at) = ?",
        (user_id, f"{month:02}")
    )
    total = cursor.fetchone()[0]
    conn.close()

    oylar = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
        5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
        9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
    }
    oy_nomi = oylar.get(month, "Nomaʼlum oy")
    return f"📅 {oy_nomi} uchun umumiy xarajatlar: {total if total else 0} so'm"

def category_summary(user_id: int) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Hech qanday kategoriya bo‘yicha xarajat topilmadi."

    text = "🏷 <b>Kategoriya bo‘yicha xarajatlar:</b>\n"
    for row in rows:
        text += f"- {row[0]}: {row[1]} so'm\n"
    return text

def delete_expense(user_id: int, expense_id: int) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted:
        return f"🗑️ ID {expense_id} bo'lgan xarajat o'chirildi."
    else:
        return "❌ Bunday ID topilmadi yoki sizga tegishli emas."

# ==== FILTRLASH FUNKSIYASI ====
def filter_expenses(user_id: int, filter_type: str, start_date=None, end_date=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if filter_type == "today":
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT created_at, description, amount, category FROM expenses WHERE user_id = ? AND created_at = ?", (user_id, today))
    elif filter_type == "week":
        today = datetime.now()
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute("SELECT created_at, description, amount, category FROM expenses WHERE user_id = ? AND created_at >= ?", (user_id, week_ago))
    elif filter_type == "range" and start_date and end_date:
        cursor.execute("SELECT created_at, description, amount, category FROM expenses WHERE user_id = ? AND created_at BETWEEN ? AND ?", (user_id, start_date, end_date))
    else:
        conn.close()
        return "❌ Noto‘g‘ri filtr tanlandi."

    rows = cursor.fetchall()
    total = sum(row[2] for row in rows) if rows else 0
    conn.close()

    if not rows:
        return "Hech qanday xarajat topilmadi."

    text = ""
    for row in rows:
        text += (
            f"📅 <b>Sana:</b> {row[0]}\n"
            f"📝 <b>Tavsif:</b> {row[1]}\n"
            f"💵 <b>Summa:</b> {row[2]} so'm\n"
            f"🏷 <b>Kategoriya:</b> {row[3]}\n"
            f"------------------------\n"
        )
    text += f"\n<b>Jami:</b> {total} so'm"
    return text

# ==== REPLY KEYBOARDLAR ====
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Add Expense")],
            [KeyboardButton(text="📋 List Expenses")],
            [KeyboardButton(text="📊 Summary"), KeyboardButton(text="🏷 Category Summary")],
            [KeyboardButton(text="🗓 Monthly Summary")],
            [KeyboardButton(text="🔍 Filtrlangan Ro'yxatlar")]
        ],
        resize_keyboard=True
    )

def filter_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugungi xarajatlar")],
            [KeyboardButton(text="📆 Shu haftadagi xarajatlar")],
            [KeyboardButton(text="📍 Sana oralig‘i bo‘yicha")],
            [KeyboardButton(text="🔙 Back")]
        ],
        resize_keyboard=True
    )

def register_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📝 Ro'yxatdan o'tish")]],
        resize_keyboard=True
    )

def back_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Back")]],
        resize_keyboard=True
    )

def category_buttons():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Oziq-ovqat"), KeyboardButton(text="Transport")],
            [KeyboardButton(text="Ko‘ngilochar"), KeyboardButton(text="Uy-ro‘zg‘or")],
            [KeyboardButton(text="Boshqa")]
        ],
        resize_keyboard=True
    )

# ==== HOLATLAR ====
class AddExpenseState(StatesGroup):
    description = State()
    amount = State()
    category = State()

class MonthState(StatesGroup):
    month = State()

class DateRangeState(StatesGroup):
    start = State()
    end = State()

# ==== ROUTER ====
router = Router()

# ==== START ====
@router.message(Command("start"))
async def start(message: types.Message):
    if is_registered(message.from_user.id):
        await message.answer("Xush kelibsiz! Asosiy menyudan foydalanishingiz mumkin.", reply_markup=main_menu())
    else:
        await message.answer("Botdan foydalanish uchun ro'yxatdan o'ting:", reply_markup=register_menu())

# ==== RO‘YXATDAN O‘TISH ====
@router.message(F.text == "📝 Ro'yxatdan o'tish")
async def register(message: types.Message):
    register_user(message.from_user.id, message.from_user.full_name)
    await message.answer("✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=main_menu())

# ==== LIST EXPENSES ====
@router.message(F.text == "📋 List Expenses")
async def show_list(message: types.Message):
    if not is_registered(message.from_user.id):
        await message.answer("Iltimos, avval ro'yxatdan o'ting!", reply_markup=register_menu())
        return

    expenses = list_expenses_inline(message.from_user.id)
    for text, keyboard in expenses:
        if keyboard:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(text)

# ==== INLINE DELETE ====
@router.callback_query(F.data.startswith("delete_"))
async def inline_delete(callback: types.CallbackQuery):
    expense_id = int(callback.data.split("_")[1])
    result = delete_expense(callback.from_user.id, expense_id)
    await callback.message.edit_text(f"{callback.message.text}\n\n<b>{result}</b>", parse_mode="HTML")
    await callback.answer("O‘chirildi!")

# ==== SUMMARY ====
@router.message(F.text == "📊 Summary")
async def show_summary(message: types.Message):
    await message.answer(total_summary(message.from_user.id))

# ==== CATEGORY SUMMARY ====
@router.message(F.text == "🏷 Category Summary")
async def show_category_summary(message: types.Message):
    await message.answer(category_summary(message.from_user.id), parse_mode="HTML")

# ==== MONTHLY SUMMARY ====
@router.message(F.text == "🗓 Monthly Summary")
async def ask_month(message: types.Message, state: FSMContext):
    await message.answer("Qaysi oy uchun umumiy xarajatlarni ko‘rmoqchisiz? (1-12)", reply_markup=back_button())
    await state.set_state(MonthState.month)

@router.message(MonthState.month)
async def show_month(message: types.Message, state: FSMContext):
    try:
        month = int(message.text)
        await message.answer(monthly_summary(message.from_user.id, month), reply_markup=main_menu())
    except:
        await message.answer("Noto‘g‘ri raqam kiritildi. 1-12 oralig‘ida raqam kiriting.")
    await state.clear()

# ==== ADD EXPENSE ====
@router.message(F.text == "➕ Add Expense")
async def ask_description(message: types.Message, state: FSMContext):
    await message.answer("Xarajat tavsifini kiriting:", reply_markup=back_button())
    await state.set_state(AddExpenseState.description)

@router.message(AddExpenseState.description)
async def ask_amount(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Xarajat summasini kiriting:", reply_markup=back_button())
    await state.set_state(AddExpenseState.amount)

@router.message(AddExpenseState.amount)
async def ask_category(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        await state.update_data(amount=amount)
        await message.answer("Kategoriya tanlang:", reply_markup=category_buttons())
        await state.set_state(AddExpenseState.category)
    except ValueError:
        await message.answer("Noto‘g‘ri summa kiritildi. Faqat raqam kiriting.")

@router.message(AddExpenseState.category)
async def save_expense(message: types.Message, state: FSMContext):
    data = await state.get_data()
    description = data['description']
    amount = data['amount']
    category = message.text
    await message.answer(add_expense(message.from_user.id, description, amount, category), reply_markup=main_menu())
    await state.clear()

# ==== FILTRLANGAN RO‘YXATLAR ====
@router.message(F.text == "🔍 Filtrlangan Ro'yxatlar")
async def show_filter_menu(message: types.Message):
    await message.answer("Filtr turini tanlang:", reply_markup=filter_menu())

@router.message(F.text == "📅 Bugungi xarajatlar")
async def today_expenses(message: types.Message):
    text = filter_expenses(message.from_user.id, "today")
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())

@router.message(F.text == "📆 Shu haftadagi xarajatlar")
async def week_expenses(message: types.Message):
    text = filter_expenses(message.from_user.id, "week")
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())

@router.message(F.text == "📍 Sana oralig‘i bo‘yicha")
async def ask_start_date(message: types.Message, state: FSMContext):
    await message.answer("Boshlanish sanasini kiriting (YYYY-MM-DD):", reply_markup=back_button())
    await state.set_state(DateRangeState.start)

@router.message(DateRangeState.start)
async def ask_end_date(message: types.Message, state: FSMContext):
    await state.update_data(start=message.text)
    await message.answer("Tugash sanasini kiriting (YYYY-MM-DD):", reply_markup=back_button())
    await state.set_state(DateRangeState.end)

@router.message(DateRangeState.end)
async def show_range_expenses(message: types.Message, state: FSMContext):
    data = await state.get_data()
    start_date = data['start']
    end_date = message.text
    text = filter_expenses(message.from_user.id, "range", start_date, end_date)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())
    await state.clear()

# ==== BOTNI ISHGA TUSHIRISH ====
async def main():
    print("Bot ishga tushdi!")
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
