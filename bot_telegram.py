import logging
from aiogram.utils import executor
from create_bot import dp
from handlers import client, admin
from data_base import sqlite_db


# Оповещение в терминале о запуске бота
async def on_startup(_):
    print("Бот онлайн")


# Закрытие базы данных при выключении бота
async def on_shutdown(_):
    sqlite_db.db.close()


# Регистрация хендлеров
client.register_handlers_client(dp)
admin.register_handlers_admin(dp)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    logging.basicConfig(level=logging.INFO)
