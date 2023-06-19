from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from ..create_bot import bot, ADMIN_ID
from ..keyboards import client_kb, kb_admin_objects, kb_objects,  kb_yes_no
from ..data_base import sqlite_db


# Определение состояний FSM для работы с объектами
class AdminEdit(StatesGroup):
    """
    A state machine for editing objects in an administrative panel.

    This state machine allows administrators to select an action (delete or add),
    select an object type (e.g. user, product), choose an object to edit, and perform
    the corresponding action on that object. It uses the `aiogram.dispatcher.filters.state`
    module to manage the state transitions.
    """
    select_action = State()
    select_object_type = State()
    set_object_type = State()
    choose_object = State()
    delete_object = State()
    add_object = State()


# Вывод возможноых действий администратора
async def edit_objects(message: types.Message):
    """
    Sends a message to the user asking them to choose an option using a custom keyboard,
    and sets the state of the AdminEdit state machine to select_action.

    Args:
        message (:obj:`types.Message`): The incoming message from the user.

    Returns:
        None
    """
    await message.answer("Выберите:", reply_markup=kb_admin_objects)
    await AdminEdit.select_action.set()


async def select_action(message: types.Message, state: FSMContext):
    """
    Handles the user input for selecting an action (delete or add)
    in the AdminEdit state machine.
    The function saves the selected action in the user's context,
    sends a message to the user asking them
    to choose a location for the object, and sets the state of the
    AdminEdit state machine to set_object_type.

    Args:
        message (:obj:`types.Message`): The incoming message from the user.
        state (:obj:`FSMContext`): The current state of the AdminEdit state machine.

    Returns:
        None
    """
    action = message.text
    # Отправляем сообщение с выбором локации объекта
    await message.answer('Выберите локацию объекта:', reply_markup=kb_objects)
    # Сохраняем выбранное действие в контексте пользователя
    async with state.proxy() as data:
        data['action'] = action
    await AdminEdit.set_object_type.set()


# Сохранение локации объекта
async def set_object_type(message: types.Message, state: FSMContext):
    """
    Handles the user input for selecting an object type
    (e.g. apartment or factory) in the AdminEdit state machine.
    The function saves the selected object type in the user's context,
    and checks the selected action to determine
    what the next state should be.

    Args:
        message (:obj:`types.Message`): The incoming message from the user.
        state (:obj:`FSMContext`): The current state of the AdminEdit state machine.

    Returns:
        None
    """
    object_type = message.text
    if object_type == 'Квартира':
        object_type = 'apartment'
    else:
        object_type = 'factory'

    async with state.proxy() as data:
        data['object_type'] = object_type
        action = data['action']

    if action in ('Посмотреть объекты', 'Удалить описание объекта'):
        await client_kb.kb_all_objects(1, data['object_type'])
        await message.answer('Выберите:', reply_markup=client_kb.KEYBOARD)
        await AdminEdit.choose_object.set()
    elif action == 'Добавить объект':
        await message.answer('Введите название объекта, который вы хотите добавить.')
        await AdminEdit.add_object.set()


# Обработчик нажатий кнопки переключения страницы / объекта
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Handles the user input for selecting an object page or object
    in the AdminEdit state machine.
    The function retrieves information about the selected object
    and sends it to the user if necessary.
    If the selected action is "Посмотреть объекты", the function
    ends the FSM and returns the user to the main menu.
    If the selected action is "Удалить описание объекта",
    the function prompts the user to confirm the deletion.

    Args:
        callback_query (:obj:`types.CallbackQuery`): The incoming callback query from the user.
        state (:obj:`FSMContext`): The current state of the AdminEdit state machine.

    Returns:
        None
    """
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
                if isinstance(obj_descr, list):
                    row = len(obj_descr)
                else:
                    row = 1
                for i in range(row):
                    if isinstance(obj_descr, list):
                        await bot.send_message(callback_query.message.chat.id,
                                               f'Описание № {i+1}: {obj_descr[i]}')
                    else:
                        await bot.send_message(callback_query.message.chat.id,
                                               f'Описание № {i + 1}: {obj_descr}')
                    if obj_photos and isinstance(obj_photos, list) and i < len(obj_photos):
                        await bot.send_photo(callback_query.message.chat.id,
                                             photo=obj_photos[i])
                    elif obj_photos and i < 1:
                        await bot.send_photo(callback_query.message.chat.id,
                                             photo=obj_photos)
                    else:
                        await bot.send_message(callback_query.message.chat.id,
                                               'Фотография отсутствует.')
            else:
                await bot.send_message(callback_query.message.chat.id,
                                       'Описание и фотография отсутствуют.')
                await state.finish()
                # Возвращаем администратора в главное меню
                await edit_objects(callback_query.message)
                return

            # Удаляем предыдущую клавиатуру
            await bot.delete_message(callback_query.message.chat.id,
                                     callback_query.message.message_id)

        # Если было выбрано действие "Посмотреть объекты",
        # то после вывода описания объекта, то завершаем FSM и
        # возвращаем администратора в главное меню
        if data['action'] == 'Посмотреть объекты':
            await state.finish()
            # Возвращаем администратора в главное меню
            await edit_objects(callback_query.message)

        # Если было выбрано действие "Удалить описание объекта"
        elif data['action'] == 'Удалить описание объекта':
            await bot.send_message(callback_query.message.chat.id,
                                   'Вы действительно хотите удалить описание объекта?',
                                   reply_markup=kb_yes_no)
            await AdminEdit.delete_object.set()

    # Если была нажата кнопка с номером страницы
    elif page is not None:
        # Обновление списка объектов с новой страницей
        async with state.proxy() as data:
            await client_kb.kb_all_objects(page + 1, data['object_type'])
            await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                                message_id=callback_query.message.message_id,
                                                reply_markup=client_kb.KEYBOARD)


# Удаление описания объекта
async def delete_object(message: types.Message, state: FSMContext):
    """
    Deletes the description of an object from the database if the user confirms deletion.

    Args:
        message (:obj:`types.Message`): The incoming message object from the user.
        state (:obj:`FSMContext`): The current state of the AdminEdit state machine.

    Returns:
        None
    """
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
    """
    Adds a new object to the database if it does not already exist.

    Args:
        message (:obj:`types.Message`): The incoming message object from the user.
        state (:obj:`FSMContext`): The current state of the AdminEdit state machine.

    Returns:
        None
    """
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
def register_handlers_admin(dispatcher: Dispatcher):
    """
    Registers the message handlers for the admin panel.

    Args:
        dispatcher (:obj:`Dispatcher`): The Dispatcher instance.

    Returns:
        None
    """
    dispatcher.register_message_handler(edit_objects, user_id=ADMIN_ID)
    dispatcher.register_message_handler(select_action, user_id=ADMIN_ID,
                                        state=AdminEdit.select_action)
    dispatcher.register_message_handler(set_object_type, text=['Квартира', 'Завод'],
                                        user_id=ADMIN_ID,
                                        state=AdminEdit.set_object_type)
    dispatcher.register_callback_query_handler(process_callback_page, lambda c: True,
                                               state=AdminEdit.choose_object)
    dispatcher.register_message_handler(delete_object, text=['Да', 'Нет'], user_id=ADMIN_ID,
                                        state=AdminEdit.delete_object)
    dispatcher.register_message_handler(add_object, user_id=ADMIN_ID, state=AdminEdit.add_object)
