import sqlite3 as sq


class Database:
    def __init__(self):
        self.conn = sq.connect("data_base\chat_bot.db")
        self.cursor = self.conn.cursor()
        if self.conn:
            print('Data base chat_bot connected OK!')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS users\n'
                            '        (user_id PRIMARY KEY, name TEXT, post TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS apartment\n'
                            '            (object PRIMARY KEY, description TEXT, photo TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS factory\n'
                            '            (object PRIMARY KEY, description TEXT, photo TEXT)')
        self.conn.commit()

    def register_user(self, user_id: int, name: str, post: str):
        self.cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, name, post))
        self.conn.commit()

    def is_registered(self, user_id: int) -> bool:
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def get_user_info(self, user_id: int) -> tuple:
        self.cursor.execute("SELECT name, post FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

    def get_objects(self, table_name):
        self.cursor.execute("SELECT * FROM {}".format(table_name))
        rows = self.cursor.fetchall()
        table_dict = {}
        for row in rows:
            key = row[0]
            values = row[1:]
            table_dict[key] = values
        return table_dict

    def get_object(self, table_name, obj_id):
        query = "SELECT * FROM {} WHERE object=?".format(table_name)
        self.cursor.execute(query, (obj_id,))
        row = self.cursor.fetchone()
        return row

    def edit_table(self, table_name, obj_id, description, photo=''):
        query = f"UPDATE {table_name} SET "
        if description:
            query += f"description='{description}', "
        if photo:
            query += f"photo='{photo}', "
        query = query.rstrip(', ') + f" WHERE object='{obj_id}'"
        self.cursor.execute(query)
        self.conn.commit()

    def delete_description(self, table_name, obj_id):
        query = '''UPDATE {} SET description = NULL, photo = NULL WHERE object = ?'''.format(table_name)
        self.cursor.execute(query, (obj_id,))
        self.conn.commit()

    def add_object(self, table_name, obj_id):
        select_query = "SELECT * FROM {} WHERE object = ?".format(table_name)
        self.cursor.execute(select_query, (obj_id,))

        result = self.cursor.fetchone()  # получаем первую строку результата запроса

        if result is None:
            query = 'INSERT INTO {} (object) VALUES (?)'.format(table_name)
            self.cursor.execute(query, (obj_id,))
            self.conn.commit()
            return True
        return False


db = Database()
