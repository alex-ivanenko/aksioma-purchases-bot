# bot/states.py
from aiogram.fsm.state import State, StatesGroup

class PurchaseForm(StatesGroup):
    name = State()      # Наименование
    quantity = State()  # Количество
    note = State()      # Примечание
