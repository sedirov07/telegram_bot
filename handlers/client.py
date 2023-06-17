from aiogram import types, Dispatcher
from handlers import admin
from create_bot import bot, admin_id
from keyboards import kb_client, kb_objects, kb_client_reg, kb_yes_no, client_kb
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_base import sqlite_db


# Определение состояний FSM для регистрации
class Registration(StatesGroup):
    name = State()
    post = State()


# Определение состояний FSM для работы с объектами
class Objects(StatesGroup):
    ChooseCategory = State()
    ChooseObj = State()
    AddDescription = State()
    AddDescriptionText = State()
    AddPhoto = State()
    AddPhotoText = State()
    EditObject = State()


# Приветствие администратора с выведением меню действий
async def command_start(message: types.Message):
    user_id = message.from_user.id
    if user_id == admin_id:
        await message.answer("Добро пожаловать, администратор!")
        await admin.edit_objects(message)
        return
    await message.answer("Добро пожаловать!", reply_markup=kb_client_reg)


# Проверка регистрации пользователя в базе данных
async def check_registration(message: types.Message):
    user_id = message.from_user.id
    if sqlite_db.db.is_registered(user_id):
        # Возвращаем пользователя в главное меню если он уже зарегистрирован
        await message.answer("Вы уже зарегистрированы.", reply_markup=kb_client)
        return True
    return False


# Начало регистрации с запросом ФИО
async def register_start(message: types.Message):
    # Проверка регистрации пользователя в базе данных по telegram-ID
    if await check_registration(message):
        return

    await message.answer("Для регистрации укажите свои ФИО:")
    await Registration.name.set()


# Сохранение ФИО клиента, запрос должности клиента
async def register_name(message: types.Message, state: FSMContext):
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


# Сохранение должности клиента, машины состояний регистрации клиента
async def register_post(message: types.Message, state: FSMContext):
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
    user_id = message.from_user.id
    # Проверка регистрации пользователя
    if sqlite_db.db.is_registered(user_id):
        # Выбор локации объекта
        await message.answer('Выберите:', reply_markup=kb_objects)
        await Objects.ChooseCategory.set()
    else:
        await message.answer('Вы не зарегистрированы.', reply_markup=kb_client_reg)


async def choose_object(message: types.Message, state: FSMContext):
    # Сохранение локации объекта в хранилище FSM
    async with state.proxy() as data:
        if message.text == 'Квартира':
            data['obj'] = 'apartment'
        else:
            data['obj'] = 'factory'
    # Запрос на вывод первой страницы списка объектов выбранной локации
    await client_kb.kb_all_objects(1, data['obj'])
    await message.answer('Выберите:', reply_markup=client_kb.keyboard)
    await Objects.ChooseObj.set()


# Обработчик нажатий кнопки переключения страницы / объекта
async def process_callback_page(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')
    # Получаем номер страницы или объекта
    page = int(data[1])
    obj_id = ' '.join(data[2:])

    # Если была нажата кнопка объекта
    if obj_id:
        async with state.proxy() as data:
            data['obj_id'] = obj_id
        # Запрос добавления описания объекта
        await bot.send_message(callback_query.message.chat.id, 'Вы хотите добавить описание объекта?',
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
                                                reply_markup=client_kb.keyboard)


# Добавление описания объекта
async def add_description(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await message.answer('Пришлите описание объекта')
        # Если пользователь согласился добавить описание, то переводим его в состояние AddDescriptionText
        await Objects.AddDescriptionText.set()
    else:
        # Если пользователь не хочет добавлять описание, то завершаем диалог и возвращаем его в главное меню
        await state.finish()
        await bot.send_message(message.chat.id, 'Вы возвращены в главное меню')
        await message.answer('Выберите', reply_markup=kb_client)
        return


async def add_description_text(message: types.Message, state: FSMContext):
    # Записываем описание объекта в данные состояния
    async with state.proxy() as data:
        data['description'] = message.text

    # Спрашиваем пользователя, хочет ли он добавить фото
    await message.answer('Вы хотите добавить фото?', reply_markup=kb_yes_no)

    # Переводим пользователя в состояние AddPhoto
    await Objects.AddPhoto.set()


async def add_photo(message: types.Message, state: FSMContext):
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
    # Обрабатываем ответ пользователя
    photo_id = message.photo[0].file_id
    async with state.proxy() as data:
        data['photo'] = photo_id
    await message.answer('Вы хотите изменить описание?', reply_markup=kb_yes_no)
    # Переводим пользователя в состояние EditObject
    await Objects.EditObject.set()


# Изменение отправленного описания
async def edit_object(message: types.Message, state: FSMContext):
    # Обрабатываем ответ пользователя
    if message.text == 'Да':
        await message.answer('Введите новое описание')
        await Objects.AddDescriptionText.set()
    else:
        # Сохранение описания и фото в базу данных
        async with state.proxy() as data:
            sqlite_db.db.edit_table(data['obj'], data['obj_id'], data['description'], data['photo'])
            await bot.send_message(chat_id=admin_id, text=f"Добавлено описание для {data['obj_id']}"
                                                          f"в разделе {data['obj']}")
        await message.answer('Данные сохранены')
        await state.finish()

        # Возвращаем пользователя в главное меню
        await message.answer('Выберите', reply_markup=kb_client)


# Регистрация хендлеров
def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=["start"])
    dp.register_message_handler(register_start, lambda message: message.text == 'Регистрация', state="*")
    dp.register_message_handler(register_name, state=Registration.name)
    dp.register_message_handler(register_post, state=Registration.post)
    dp.register_message_handler(show_profile, lambda message: message.text == 'Профиль')
    dp.register_message_handler(objects, lambda message: message.text == 'Объекты', state="*")
    dp.register_message_handler(choose_object, state=Objects.ChooseCategory)
    dp.register_callback_query_handler(process_callback_page, lambda c: True, state=Objects.ChooseObj)
    dp.register_message_handler(add_description, state=Objects.AddDescription)
    dp.register_message_handler(add_description_text, state=Objects.AddDescriptionText)
    dp.register_message_handler(add_photo, state=Objects.AddPhoto)
    dp.register_message_handler(add_photo_text, content_types=['photo'], state=Objects.AddPhotoText)
    dp.register_message_handler(edit_object, state=Objects.EditObject)
