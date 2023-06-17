from aiogram import types, Dispatcher
from create_bot import bot, admin_id
from keyboards import client_kb, kb_admin_objects, objects_keyboard,  kb_yes_no
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_base import sqlite_db


# Определение состояний FSM для работы с объектами
class AdminEdit(StatesGroup):
    select_action = State()
    select_object_type = State()
    set_object_type = State()
    choose_object = State()
    delete_object = State()
    add_object = State()


# Вывод возможноых действий администратора
async def edit_objects(message: types.Message):
    await message.answer("Выберите:", reply_markup=kb_admin_objects)
    await AdminEdit.select_action.set()


async def select_action(message: types.Message, state: FSMContext):
    action = message.text
    # Отправляем сообщение с выбором локации объекта
    await message.answer('Выберите локацию объекта:', reply_markup=objects_keyboard)
    # Сохраняем выбранное действие в контексте пользователя
    async with state.proxy() as data:
        data['action'] = action
    await AdminEdit.set_object_type.set()


# Сохранение локации объекта
async def set_object_type(message: types.Message, state: FSMContext):
    object_type = message.text
    if object_type == 'Квартира':
        object_type = 'apartment'
    else:
        object_type = 'factory'

    async with state.proxy() as data:
        data['object_type'] = object_type
        action = data['action']

    if action == 'Посмотреть объекты' or action == 'Удалить описание объекта':
        await client_kb.kb_all_objects(1, data['object_type'])
        await message.answer('Выберите:', reply_markup=client_kb.keyboard)
        await AdminEdit.choose_object.set()
    elif action == 'Добавить объект':
        await message.answer('Введите название объекта, который вы хотите добавить.')
        await AdminEdit.add_object.set()


# Обработчик нажатий кнопки переключения страницы / объекта
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    data_kb = callback_query.data.split('_')
    # Получаем номер страницы или объекта
    page = int(data_kb[1])
    obj_id = ' '.join(data_kb[2:])

    # Если была нажата кнопка объекта
    if obj_id:
        async with state.proxy() as data:
            data['obj_id'] = obj_id
            object_type = data['object_type']
            # Получение информации об объекте
            obj_info = list(sqlite_db.db.get_object(object_type, obj_id))
            obj_name = obj_info[0]
            if obj_info[1] and ';' in obj_info[1]:
                obj_descr = obj_info[1].split(';')
            else:
                obj_descr = obj_info[1]
            if obj_info[2] and ';' in obj_info[2]:
                obj_photos = obj_info[2].split(';')
            else:
                obj_photos = obj_info[2]

            # Если была нажата кнопка с объектом, то выводим администратору описание объекта
            await bot.send_message(callback_query.message.chat.id, f'{obj_name}')
            if obj_descr:
                if type(obj_descr) == list:
                    row = len(obj_descr)
                else:
                    row = 1
                for i in range(row):
                    if type(obj_descr) == list:
                        await bot.send_message(callback_query.message.chat.id, f'Описание № {i+1}: {obj_descr[i]}')
                    else:
                        await bot.send_message(callback_query.message.chat.id, f'Описание № {i + 1}: {obj_descr}')
                    if obj_photos and type(obj_photos) == list and i < len(obj_photos):
                        await bot.send_photo(callback_query.message.chat.id, photo=obj_photos[i])
                    elif obj_photos and i < 1:
                        await bot.send_photo(callback_query.message.chat.id, photo=obj_photos)
                    else:
                        await bot.send_message(callback_query.message.chat.id, 'Фотография отсутствует.')
            else:
                await bot.send_message(callback_query.message.chat.id, f'Описание и фотография отсутствуют.')
                await state.finish()
                # Возвращаем администратора в главное меню
                await edit_objects(callback_query.message)
                return

            # Удаляем предыдущую клавиатуру
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        # Если было выбрано действие "Посмотреть объекты", то после вывода описания объекта, то завершаем FSM и
        # возвращаем администратора в главное меню
        if data['action'] == 'Посмотреть объекты':
            await state.finish()
            # Возвращаем администратора в главное меню
            await edit_objects(callback_query.message)

        # Если было выбрано действие "Удалить описание объекта"
        elif data['action'] == 'Удалить описание объекта':
            await bot.send_message(callback_query.message.chat.id, 'Вы действительно хотите удалить описание объекта?',
                                   reply_markup=kb_yes_no)
            await AdminEdit.delete_object.set()

    # Если была нажата кнопка с номером страницы
    elif page is not None:
        # Обновление списка объектов с новой страницей
        async with state.proxy() as data:
            await client_kb.kb_all_objects(page + 1, data['object_type'])
            await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                                message_id=callback_query.message.message_id,
                                                reply_markup=client_kb.keyboard)


# Удаление описания объекта
async def delete_object(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        object_type = data['object_type']
        obj_id = data['obj_id']

    if message.text == 'Да':
        sqlite_db.db.delete_description(object_type, obj_id)
        await message.answer('Описание было удалено')
    await state.finish()
    await edit_objects(message)


# Добавление нового объекта
async def add_object(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['obj'] = message.text
        object_type = data['object_type']
    if sqlite_db.db.add_object(object_type, message.text):
        await message.answer('Объект успешно добавлен!')
    else:
        await message.answer('Такой объект уже есть')
    await state.finish()
    await edit_objects(message)


# Регистрация хендлеров
def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(edit_objects, user_id=admin_id)
    dp.register_message_handler(select_action, user_id=admin_id, state=AdminEdit.select_action)
    dp.register_message_handler(set_object_type, text=['Квартира', 'Завод'], user_id=admin_id,
                                state=AdminEdit.set_object_type)
    dp.register_callback_query_handler(process_callback_page, lambda c: True, state=AdminEdit.choose_object)
    dp.register_message_handler(delete_object, text=['Да', 'Нет'], user_id=admin_id,
                                state=AdminEdit.delete_object)
    dp.register_message_handler(add_object, user_id=admin_id, state=AdminEdit.add_object)
