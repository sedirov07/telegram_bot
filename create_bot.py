from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from config_reader import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Создание памяти для FSM
storage = MemoryStorage()

# Инициализация бота и диспетчера
bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher(bot, storage=storage)

# Добавление id администратора
admin_id = 530261570
