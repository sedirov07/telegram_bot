import math
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,\
    InlineKeyboardButton, InlineKeyboardMarkup
from ..data_base import sqlite_db


KEYBOARD = None


# Создание клавиатуры из списка объектов выбранной локации по разделению на страницы
async def kb_all_objects(page_now, objects):
    global KEYBOARD
    data = sqlite_db.db.get_objects(objects)
    # Разбиваем данные на страницы по 5 строк
    page_size = 5
    pages_count = math.ceil(len(data) / page_size)
    pages = [list(data.items())[i:i + page_size] for i in range(0, len(data), page_size)]

    # Создаение клавиатуры
    keyboard = InlineKeyboardMarkup(row_width=1)
    # Вывод только первой страницы
    for i, page in enumerate(pages[page_now-1:page_now]):
        for key in page:
            button = InlineKeyboardButton(key, callback_data=f'page_{i}_{key}')
            keyboard.add(button)

    # Добавление кнопки для переключения страниц
    if pages_count > 1:
        for i in range(pages_count):
            if i + 1 != page_now:
                button_text = str(i + 1)
                button = InlineKeyboardButton(button_text, callback_data=f'page_{i}_')
                keyboard.add(button)

    # Assign the generated keyboard to the global variable KEYBOARD
    KEYBOARD = keyboard

# Создание кнопок
b_reg = KeyboardButton(text="Регистрация")
b_profile = KeyboardButton(text="Профиль")
b_objects = KeyboardButton(text="Объекты")
b_objects_ap = KeyboardButton(text="Квартира")
b_objects_fab = KeyboardButton(text="Завод")
b_yes = KeyboardButton(text="Да")
b_no = KeyboardButton(text="Нет")

# Создание клавиатуры регистрации клиента
kb_client_reg = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_client_reg.add(b_reg)

# Создание клавиатуры выбора действий для клиента
kb_client = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_client.add(b_profile).add(b_objects)

# Создание клавиатуры выбора локации объекта
kb_objects = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_objects.add(b_objects_ap).add(b_objects_fab)

# Создание клавиатуры согласия / отказа
kb_yes_no = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_yes_no.add(b_yes).add(b_no)
