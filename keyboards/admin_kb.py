from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Создаем стартовую клавиатуру администратора с выбором действий
b_edit_objects = KeyboardButton(text="Удалить описание объекта")
b_show_objects = KeyboardButton(text="Посмотреть объекты")
b_add_object = KeyboardButton(text="Добавить объект")
kb_admin_objects = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_admin_objects.add(b_edit_objects, b_show_objects, b_add_object)
