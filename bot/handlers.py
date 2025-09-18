# bot/handlers.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from .states import PurchaseForm
from .config import AUTHORIZED_USERS
from .airtable_client import AirtableClient
# Импортируем календарь и работу с датами
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime, date

router = Router()
logger = logging.getLogger(__name__)

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

# Клавиатура для шага "Примечание" и "Срок выполнения" — с кнопкой "Пропустить" и "Отмена"
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
        await message.answer("🚫 У вас нет доступа к этому боту")
        return
    await message.answer(
        "Добро пожаловать!\nНажмите кнопку ниже, чтобы добавить покупку",
        reply_markup=main_kb
    )

# Обработчик кнопки "Добавить покупку"
@router.message(F.text == "Добавить покупку")
async def start_purchase_flow(message: Message, state: FSMContext):
    if not is_authorized(message.from_user):
        await message.answer("🚫 У вас нет доступа к этому действию")
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
        await message.answer("❌ Введите положительное число")
        return
    await state.update_data(quantity=quantity)
    await message.answer("Введите примечание:", reply_markup=skip_cancel_kb)
    await state.set_state(PurchaseForm.note)

# Вспомогательная функция для сохранения данных в Airtable и завершения диалога.
async def _save_data_and_finish(obj, state: FSMContext):
    """
    Вспомогательная функция для сохранения данных в Airtable и завершения диалога.
    Принимает obj — это может быть Message или CallbackQuery.
    """
    data = await state.get_data()
    try:
        # Определяем, откуда брать пользователя
        if isinstance(obj, Message):
            user = obj.from_user
        elif isinstance(obj, CallbackQuery):
            user = obj.from_user
            # Отправляем ответ, чтобы убрать "часики" у кнопки
            await obj.answer()
        else:
            raise ValueError("Неподдерживаемый тип объекта")

        sender_name = user.first_name
        if user.last_name:
            sender_name += " " + user.last_name
        data['sender_name'] = sender_name

        # Подготавливаем данные для Airtable
        record_data = {
            "Наименование": data['name'],
            "Количество": data['quantity'], 
            "Отправитель": data['sender_name']
        }
        
        # Добавляем "Примечание" только если оно не пустое
        if data.get('note'):
            record_data["Примечание"] = data['note']
            
        # Добавляем "Срок выполнения" только если он не пустой
        if data.get('deadline'):
            record_data["Срок выполнения"] = data['deadline']
            
        # Сохраняем в Airtable
        await airtable_client.create_record(record_data)
        
        # Формируем сообщение для ответа
        response_lines = [
            "✅ Запись добавлена:\n",
            f"<b>Наименование:</b> {data['name']}",
            f"<b>Количество:</b> {data['quantity']}"   
        ]
        
        # Добавляем "Примечание" в сообщение, только если оно не пустое
        if data.get('note'):
            response_lines.append(f"<b>Примечание:</b> {data['note']}")
            
        # Добавляем "Срок выполнения" в сообщение, только если он не пустой
        if data.get('deadline'):
            response_lines.append(f"<b>Срок выполнения:</b> {data['deadline']}")
            
        response_lines.append(f"<b>Отправитель:</b> {data['sender_name']}")
        response_text = "\n".join(response_lines)

        # Отправляем ответ в зависимости от типа объекта
        if isinstance(obj, Message):
            await obj.answer(response_text, reply_markup=main_kb)
        elif isinstance(obj, CallbackQuery):
            await obj.message.answer(response_text, reply_markup=main_kb)

    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}", exc_info=True)
        error_msg = f"Произошла ошибка при сохранении в Airtable:\n<code>{str(e)}</code>"
        if isinstance(obj, Message):
            await obj.answer(error_msg)
        elif isinstance(obj, CallbackQuery):
            await obj.message.answer(error_msg)
    finally:
        await state.clear()

# Обработчик кнопки "Пропустить" на шаге примечания
@router.message(PurchaseForm.note, F.text == "Пропустить")
async def skip_note(message: Message, state: FSMContext):
    await state.update_data(note="")
    # Показываем ТОЛЬКО одно сообщение с календарём
    await message.answer(
        "Выберите срок выполнения:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(PurchaseForm.deadline)

# Обработчик примечания — срабатывает, если текст НЕ "Пропустить"
@router.message(PurchaseForm.note, F.text != "Пропустить")
async def process_note(message: Message, state: FSMContext):
    note_text = message.text.strip()
    await state.update_data(note=note_text)
    # Показываем ТОЛЬКО одно сообщение с календарём
    await message.answer(
        "Выберите срок выполнения:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(PurchaseForm.deadline)

# Обработчик кнопки "Пропустить" на шаге срока выполнения
@router.message(PurchaseForm.deadline, F.text == "Пропустить")
async def skip_deadline(message: Message, state: FSMContext):
    await state.update_data(deadline=None) 
    await _save_data_and_finish(message, state)

@router.callback_query(SimpleCalendarCallback.filter(), PurchaseForm.deadline)
async def process_calendar(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date_obj = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        today = date.today()
        if date_obj.date() < today:
            # Дата в прошлом — просим выбрать заново
            await callback_query.message.answer(
                "❌ Нельзя выбрать дату в прошлом",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            return  # Не выходим из состояния, ждём новую дату

        # Форматируем дату в строку (например, "2024-05-21")
        deadline_str = date_obj.strftime("%Y-%m-%d")
        await state.update_data(deadline=deadline_str)
        await _save_data_and_finish(callback_query, state)
