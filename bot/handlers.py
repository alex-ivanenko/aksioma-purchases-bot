# bot/handlers.py
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart

from .states import PurchaseForm
from .config import AUTHORIZED_USERS
from .airtable_client import AirtableClient

router = Router()
logger = logging.getLogger(__name__)  # ← Добавлен логгер

# Создаём клиент Airtable (один на всё приложение)
airtable_client = AirtableClient()

# Основная клавиатура — появляется в /start и в конце диалога
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Добавить покупку")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура с кнопкой "Отмена" — во время диалога
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для шага "Примечание" — с кнопкой "Пропустить" и "Отмена"
skip_cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пропустить")],
        [KeyboardButton(text="Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Фильтр: только для авторизованных пользователей
def is_authorized(user) -> bool:
    return user.id in AUTHORIZED_USERS

# Команда /start — только приветствие
@router.message(CommandStart())
async def cmd_start(message: Message):
    if not is_authorized(message.from_user):
        await message.answer("У вас нет доступа к этому боту!")
        return
    await message.answer(
        "Добро пожаловать!\nНажмите кнопку ниже, чтобы добавить покупку",
        reply_markup=main_kb
    )

# Обработчик кнопки "Добавить покупку"
@router.message(F.text == "Добавить покупку")
async def start_purchase_flow(message: Message, state: FSMContext):
    if not is_authorized(message.from_user):
        await message.answer("У вас нет доступа к этому действию!")
        return
    await message.answer("Введите наименование:", reply_markup=cancel_kb)
    await state.set_state(PurchaseForm.name)

# Обработчик кнопки "Отмена"
@router.message(F.text == "Отмена")
async def handle_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного диалога", reply_markup=main_kb)
        return

    await state.clear()
    await message.answer("Диалог отменён", reply_markup=main_kb)

# Обработчик наименования
@router.message(PurchaseForm.name, F.text)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите количество:", reply_markup=cancel_kb)
    await state.set_state(PurchaseForm.quantity)

# Обработчик количества — с валидацией
@router.message(PurchaseForm.quantity, F.text)
async def process_quantity(message: Message, state: FSMContext):
    # Получаем текст и заменяем запятую на точку
    quantity_text = message.text.strip().replace(",", ".")

    try:
        # Преобразуем в float
        quantity = float(quantity_text)
        if quantity <= 0:
            raise ValueError

    except ValueError:
        await message.answer("Введите положительное число!")
        return

    await state.update_data(quantity=quantity)
    await message.answer("Введите примечание или нажмите <b>Пропустить</b>:", reply_markup=skip_cancel_kb)
    await state.set_state(PurchaseForm.note)
    
async def _save_data_and_finish(message: Message, state: FSMContext):
    """
    Вспомогательная функция для сохранения данных в Airtable и завершения диалога.
    """
    data = await state.get_data()

    try:
        user = message.from_user
        sender_name = user.first_name
        if user.last_name:
            sender_name += " " + user.last_name
            
        data['sender_name'] = sender_name

        # Сохраняем в Airtable
        await airtable_client.create_record({
            "Наименование": data['name'],
            "Количество": data['quantity'],
            "Примечание": data['note'],  
            "Отправитель": data['sender_name']
        })

        await message.answer(
            f"Данные приняты:\n\n"
            f"<b>Наименование:</b> {data['name']}\n"
            f"<b>Количество:</b> {data['quantity']}\n"
            f"<b>Примечание:</b> {data['note']}\n"
            f"<b>Отправитель:</b> {data['sender_name']}\n\n"
            f"Запись успешно добавлена в Airtable",
            reply_markup=main_kb
        )

    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}", exc_info=True)
        await message.answer(
            f"Произошла ошибка при сохранении в Airtable:\n<code>{str(e)}</code>"
        )
    finally:
        await state.clear()

# Обработчик кнопки "Пропустить" на шаге примечания
@router.message(PurchaseForm.note, F.text == "Пропустить")
async def skip_note(message: Message, state: FSMContext):
    await state.update_data(note="")
    await _save_data_and_finish(message, state)
    
# Обработчик примечания — срабатывает, если текст НЕ "Пропустить"
@router.message(PurchaseForm.note, F.text != "Пропустить")
async def process_note(message: Message, state: FSMContext):
    note_text = message.text.strip() if message.text else ""
    await state.update_data(note=note_text)
    await _save_data_and_finish(message, state)
