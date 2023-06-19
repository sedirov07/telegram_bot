from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from ..handlers import admin
from ..create_bot import bot, ADMIN_ID
from ..keyboards import kb_client, kb_objects, kb_client_reg, kb_yes_no, client_kb
from ..data_base import sqlite_db


# Определение состояний FSM для регистрации
class Registration(StatesGroup):
    """
    A class representing the states of the registration process for new users.

    States:
        `name`: The state where the user is asked to provide their full name.
        `post`: The state where the user is asked to provide their job position.
    """
    name = State()
    post = State()


# Определение состояний FSM для работы с объектами
class Objects(StatesGroup):
    """
    A class representing the states of the object management process.

    States:
        `ChooseCategory`: The state where the user is asked to
        choose a category of objects.
        `ChooseObj`: The state where the user is asked to choose
        an object from the selected category.
        `AddDescription`: The state where the user is asked to
        add a description for the object.
        `AddDescriptionText`: The state where the user is asked to
        provide the text for the object's description.
        `AddPhoto`: The state where the user is asked to add a photo for the object.
        `AddPhotoText`: The state where the user is asked to provide
        a caption for the object's photo.
        `EditObject`: The state where the user can edit an existing object.
    """
    ChooseCategory = State()
    ChooseObj = State()
    AddDescription = State()
    AddDescriptionText = State()
    AddPhoto = State()
    AddPhotoText = State()
    EditObject = State()


# Приветствие администратора с выведением меню действий
async def command_start(message: types.Message):
    """
    A function that handles the "/start" command from users.

    If the user is an administrator, it welcomes them and displays a menu of admin actions.
    Otherwise, it welcomes the user and displays a keyboard with options.

    Args:
        message: A `types.Message` object representing the user's message.

    Returns:
        None
    """
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("Добро пожаловать, администратор!")
        await admin.edit_objects(message)
        return
    await message.answer("Добро пожаловать!", reply_markup=kb_client_reg)


# Проверка регистрации пользователя в базе данных
async def check_registration(message: types.Message):
    """
    A function that checks whether a user is already registered
    in the database based on their Telegram ID.

    If the user is already registered, it sends a message to let
    them know and returns True.
    Otherwise, it returns False.

    Args:
        message: A `types.Message` object representing the user's message.

    Returns:
        A boolean value indicating whether the user is already registered.
    """
    user_id = message.from_user.id
    if sqlite_db.db.is_registered(user_id):
        # Возвращаем пользователя в главное меню если он уже зарегистрирован
        await message.answer("Вы уже зарегистрированы.", reply_markup=kb_client)
        return True
    return False


# Начало регистрации с запросом ФИО
async def register_start(message: types.Message):
    """
    A function that starts the registration process for a new user.

    If the user is already registered, it doesn't do anything.
    Otherwise, it asks the user to provide their full name and sets the state to 'name'.

    Args:
        message: A `types.Message` object representing the user's message.

    Returns:
        None
    """
    # Проверка регистрации пользователя в базе данных по telegram-ID
    if await check_registration(message):
        return

    await message.answer("Для регистрации укажите свои ФИО:")
    await Registration.name.set()


# Сохранение ФИО клиента, запрос должности клиента
async def register_name(message: types.Message, state: FSMContext):
    """
     A function that handles the user's response to the registration
     prompt for their full name.

    If the name entered is not in the correct format
    (3 words without digits), it sends an error message.
    Otherwise, it saves the name in the FSM context and prompts
    the user to enter their job position.

    Args:
        message: A `types.Message` object representing the user's
        message containing their full name.
        state: An `FSMContext` object representing the current
        state of the conversation.

    Returns:
        None
    """
    name = message.text.strip().title()
    # Проверка введенного ФИО
    if not name.replace(" ", "").isalpha() or len(name.split()) != 3:
        await message.answer("ФИО должно состоять из 3-х слов без цифр. Попробуйте еще раз.")
        return
    # Сохранение введенного ФИО
    async with state.proxy() as data:
        data['name'] = name
    await message.answer("Укажите Вашу должность:")
    await Registration.post.set()


# Сохранение должности клиента, завершение машины состояний регистрации клиента
async def register_post(message: types.Message, state: FSMContext):
    """
    A function that handles the user's response to the registration
    prompt for their job position.

    It saves the previously-entered full name and job position in
    the database and sends a success message.

    Args:
        message: A `types.Message` object representing the user's
        message containing their job position.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    post = message.text.strip().title()
    user_id = message.from_user.id
    async with state.proxy() as data:
        name = data["name"]
    # Сохранение введенных ФИО и должности в базу данных
    sqlite_db.db.register_user(user_id, name, post)
    # Возвращаем пользователя в главное меню
    await message.answer("Вы успешно зарегистрированы!", reply_markup=kb_client)
    await state.finish()


# Команда просмотра профиля для клиента
async def show_profile(message: types.Message):
    """
    A function that displays the user's profile information,
    including their full name and job position.

    If the user is not registered, it sends an error message.

    Args:
        message: A `types.Message` object representing the user's message.

    Returns:
        None
    """
    user_id = message.from_user.id
    if not sqlite_db.db.is_registered(user_id):
        await message.answer("Вы не зарегистрированы.", reply_markup=kb_client_reg)
        return
    # Запрос ФИО и должности пользователя из базы данных
    name, post = sqlite_db.db.get_user_info(user_id)
    await message.answer(f"ФИО: {name}\nНазвание компании: {post}")

    # Возвращаем пользователя в главное меню
    await message.answer('Выберите', reply_markup=kb_client)


# Команда просмотра объектов с выбором локации
async def objects(message: types.Message):
    """
    A function that displays the available object categories and
    prompts the user to select one.

    If the user is not registered, it sends an error message.

    Args:
        message: A `types.Message` object representing the user's message.

    Returns:
        None
    """
    user_id = message.from_user.id
    # Проверка регистрации пользователя
    if sqlite_db.db.is_registered(user_id):
        # Выбор локации объекта
        await message.answer('Выберите:', reply_markup=kb_objects)
        await Objects.ChooseCategory.set()
    else:
        await message.answer('Вы не зарегистрированы.', reply_markup=kb_client_reg)


async def choose_object(message: types.Message, state: FSMContext):
    """
    A function that handles the user's selection of an object category
    and saves it in the FSM context.

    It then displays the list of available objects in the selected category
    and prompts the user to select one.

    Args:
        message: A `types.Message` object representing the user's message containing
        the selected object category.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    # Сохранение локации объекта в хранилище FSM
    async with state.proxy() as data:
        if message.text == 'Квартира':
            data['obj'] = 'apartment'
        else:
            data['obj'] = 'factory'
    # Запрос на вывод первой страницы списка объектов выбранной локации
    await client_kb.kb_all_objects(1, data['obj'])
    await message.answer('Выберите:', reply_markup=client_kb.KEYBOARD)
    await Objects.ChooseObj.set()


# Обработчик нажатий кнопки переключения страницы / объекта
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    """
        A function that handles the user's selection of a page or object from
        the list of available objects.

        If the user selects a page number, it updates the list of available objects
        with the new page.
        If the user selects an object, it saves the selected object ID in the FSM context
        and prompts the user to add a description.

        Args:
            callback_query: A `types.CallbackQuery` object representing the user's callback query.
            state: An `FSMContext` object representing the current state of the conversation.

        Returns:
            None
        """
    data = callback_query.data.split('_')
    # Получаем номер страницы или объекта
    page = int(data[1])
    obj_id = ' '.join(data[2:])

    # Если была нажата кнопка объекта
    if obj_id:
        async with state.proxy() as data:
            data['obj_id'] = obj_id
        # Запрос добавления описания объекта
        await bot.send_message(callback_query.message.chat.id,
                               'Вы хотите добавить описание объекта?',
                               reply_markup=kb_yes_no)
        await Objects.AddDescription.set()

        # Удаление предыдущей клавиатуры
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    # Если была нажата кнопка страницы
    elif page is not None:
        # Обновление списка объектов с новой страницей
        async with state.proxy() as data:
            await client_kb.kb_all_objects(page + 1, data['obj'])
            await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                                message_id=callback_query.message.message_id,
                                                reply_markup=client_kb.KEYBOARD)


# Добавление описания объекта
async def add_description(message: types.Message, state: FSMContext):
    """
     A function that handles the user's response to whether they want to add
     a description for the selected object.

    If the user agrees, it prompts them to enter the description and sets
    the conversation state to AddDescriptionText.
    Otherwise, it ends the conversation and returns the user to the main menu.

    Args:
        message: A `types.Message` object representing the user's message containing their response.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    if message.text == 'Да':
        await message.answer('Пришлите описание объекта')
        # Если пользователь согласился добавить описание,
        # то переводим его в состояние AddDescriptionText
        await Objects.AddDescriptionText.set()
    else:
        # Если пользователь не хочет добавлять описание,
        # то завершаем диалог и возвращаем его в главное меню
        await state.finish()
        await bot.send_message(message.chat.id, 'Вы возвращены в главное меню')
        await message.answer('Выберите', reply_markup=kb_client)
        return


async def add_description_text(message: types.Message, state: FSMContext):
    """
    A function that handles the user's submission of a description for the selected object.

    It saves the description in the FSM context and prompts the user to add a photo.

    Args:
        message: A `types.Message` object representing the user's message containing
        the object description.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    # Записываем описание объекта в данные состояния
    async with state.proxy() as data:
        data['description'] = message.text

    # Спрашиваем пользователя, хочет ли он добавить фото
    await message.answer('Вы хотите добавить фото?', reply_markup=kb_yes_no)

    # Переводим пользователя в состояние AddPhoto
    await Objects.AddPhoto.set()


async def add_photo(message: types.Message, state: FSMContext):
    """
    A function that handles the user's response to whether they want
    to add a photo for the selected object.

    If the user agrees, it prompts them to send a photo and
    sets the conversation state to AddPhotoText.
    Otherwise, it saves the object information (description and empty photo)
    in the database and ends the conversation.

    Args:
        message: A `types.Message` object representing the user's message containing their response.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    # Обрабатываем ответ пользователя
    if message.text == 'Да':
        await message.answer('Пришлите фото объекта')
        # Переводим пользователя в состояние EditObject
        await Objects.AddPhotoText.set()
    else:
        async with state.proxy() as data:
            data['photo'] = ''
            # Сохраняем данные в базу данных
            sqlite_db.db.edit_table(data['obj'], data['obj_id'], data['description'], data['photo'])
        await message.answer('Данные сохранены')
        await state.finish()

        # Возвращаем пользователя в главное меню
        await objects(message)


async def add_photo_text(message: types.Message, state: FSMContext):
    """
    A function that handles the user's submission of a photo for the selected object.

    It saves the photo ID in the FSM context and prompts the user to confirm
    if they want to edit the description.

    Args:
        message: A `types.Message` object representing the user's message containing
        the object photo.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    # Обрабатываем ответ пользователя
    photo_id = message.photo[0].file_id
    async with state.proxy() as data:
        data['photo'] = photo_id
    await message.answer('Вы хотите изменить описание?', reply_markup=kb_yes_no)
    # Переводим пользователя в состояние EditObject
    await Objects.EditObject.set()


# Изменение отправленного описания
async def edit_object(message: types.Message, state: FSMContext):
    """
     A function that handles the user's response to whether they want to edit
     the object description.

    If the user agrees, it prompts them to enter a new description and sets
    the conversation state to AddDescriptionText.
    Otherwise, it saves the object information (description and photo) in
    the database and ends the conversation.

    Args:
        message: A `types.Message` object representing the user's message containing their response.
        state: An `FSMContext` object representing the current state of the conversation.

    Returns:
        None
    """
    # Обрабатываем ответ пользователя
    if message.text == 'Да':
        await message.answer('Введите новое описание')
        await Objects.AddDescriptionText.set()
    else:
        # Сохранение описания и фото в базу данных
        async with state.proxy() as data:
            sqlite_db.db.edit_table(data['obj'], data['obj_id'], data['description'], data['photo'])
            await bot.send_message(chat_id=ADMIN_ID, text=f"Добавлено описание для {data['obj_id']}"
                                                          f"в разделе {data['obj']}")
        await message.answer('Данные сохранены')
        await state.finish()

        # Возвращаем пользователя в главное меню
        await message.answer('Выберите', reply_markup=kb_client)


# Регистрация хендлеров
def register_handlers_client(dispatcher: Dispatcher):
    """
     A function that registers all client-side message handlers with
     the given `Dispatcher` object.

    Args:
        dispatcher: A `Dispatcher` object representing the bot message dispatcher.

    Returns:
        None
    """
    dispatcher.register_message_handler(command_start, commands=["start"])
    dispatcher.register_message_handler(register_start,
                                        lambda message: message.text == 'Регистрация', state="*")
    dispatcher.register_message_handler(register_name, state=Registration.name)
    dispatcher.register_message_handler(register_post, state=Registration.post)
    dispatcher.register_message_handler(show_profile, lambda message: message.text == 'Профиль')
    dispatcher.register_message_handler(objects, lambda message: message.text == 'Объекты',
                                        state="*")
    dispatcher.register_message_handler(choose_object, state=Objects.ChooseCategory)
    dispatcher.register_callback_query_handler(process_callback_page, lambda c: True,
                                               state=Objects.ChooseObj)
    dispatcher.register_message_handler(add_description, state=Objects.AddDescription)
    dispatcher.register_message_handler(add_description_text, state=Objects.AddDescriptionText)
    dispatcher.register_message_handler(add_photo, state=Objects.AddPhoto)
    dispatcher.register_message_handler(add_photo_text, content_types=['photo'],
                                        state=Objects.AddPhotoText)
    dispatcher.register_message_handler(edit_object, state=Objects.EditObject)
