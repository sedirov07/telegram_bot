import logging
from aiogram.utils import executor
from create_bot import dispatcher
from handlers import client, admin
from data_base import sqlite_db


# Оповещение в терминале о запуске бота
async def on_startup(_):
    """
    This async function is called when the bot starts up.
    It simply prints "Бот онлайн" to indicate that the bot is online.

    Args:
        _: Unused argument.
    Return:
        None
    """
    print("Бот онлайн")


# Закрытие базы данных при выключении бота
async def on_shutdown(_):
    """
    This async function is called when the bot is shutting down.
    It closes the SQLite database connection to ensure that
    no data is lost or corrupted when the bot stops running.

    Args:
        _: Unused argument.
    Return:
        None
    """
    sqlite_db.db.close()


# Регистрация хендлеров
client.register_handlers_client(dispatcher)
admin.register_handlers_admin(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dispatcher, skip_updates=True, on_startup=on_startup)
    logging.basicConfig(level=logging.INFO)
