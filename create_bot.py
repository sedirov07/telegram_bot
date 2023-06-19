from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config_reader import config


# Создание памяти для FSM
storage = MemoryStorage()

# Инициализация бота и диспетчера
bot = Bot(token=config.bot_token.get_secret_value())
dispatcher = Dispatcher(bot, storage=storage)

# Добавление id администратора
ADMIN_ID = 530261570
