import sqlite3 as sq


class Database:
    """
    A class that provides methods for interacting with a SQLite database.
    """

    def __init__(self):
        """
        Initializes a new instance of the Database class.
        """
        self.conn = sq.connect("data_base/chat_bot.db")
        self.cursor = self.conn.cursor()
        if self.conn:
            print('Data base chat_bot connected OK!')
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users\n"
                            "        (user_id PRIMARY KEY, name TEXT, post TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS apartment\n"
                            "            (object PRIMARY KEY, description TEXT, photo TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS factory\n"
                            "            (object PRIMARY KEY, description TEXT, photo TEXT)")
        self.conn.commit()

    def register_user(self, user_id: int, name: str, post: str):
        """
        Registers a new user with the specified ID, name, and post.

        :param user_id: The ID of the user to register.
        :param name: The name of the user.
        :param post: The post of the user.
        """
        self.cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, name, post))
        self.conn.commit()

    def is_registered(self, user_id: int) -> bool:
        """
        Checks if a user with the specified ID is registered.

        :param user_id: The ID of the user to check.
        :return: True if the user is registered, False otherwise.
        """
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def get_user_info(self, user_id: int) -> tuple:
        """
        Gets the name and post of the user with the specified ID.

        :param user_id: The ID of the user to get information for.
        :return: A tuple containing the name and post of the user, or None if the user is not found.
        """
        self.cursor.execute("SELECT name, post FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def get_objects(self, table_name):
        """
        Gets all objects in the specified table.

        :param table_name: The name of the table to get objects from.
        :return: A dictionary where the keys are object IDs and
        the values are tuples of the remaining columns.
        """
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        table_dict = {}
        for row in rows:
            key = row[0]
            values = row[1:]
            table_dict[key] = values
        return table_dict

    def get_object(self, table_name, obj_id):
        """
        Gets the object with the specified ID from the specified table.

        :param table_name: The name of the table to get the object from.
        :param obj_id: The ID of the object to get.
        :return: A tuple representing the object, or None if it is not found.
        """
        query = f"SELECT * FROM {table_name} WHERE object=?"
        self.cursor.execute(query, (obj_id,))
        row = self.cursor.fetchone()
        return row

    def edit_table(self, table_name, obj_id, description, photo=''):
        """
        Edits an object in the specified table.

        :param table_name: The name of the table to edit the object in.
        :param obj_id: The ID of the object to edit.
        :param description: The description of object.
        :param photo: The photo of object
        :return: None
        """
        query = f"UPDATE {table_name} SET "
        if description:
            query += f"description='{description}', "
        if photo:
            query += f"photo='{photo}', "
        query = query.rstrip(', ') + f" WHERE object='{obj_id}'"
        self.cursor.execute(query)
        self.conn.commit()

    def delete_description(self, table_name, obj_id):
        """
        A method that deletes the description and photo of an
        object with a given ID in a specified table.
        :param table_name: the name of the table to update.
        :param obj_id: the ID of the object to update.
        :return: None.
        """
        query = f'''UPDATE {table_name}
                    SET description = NULL, photo = NULL
                    WHERE object = ?'''
        self.cursor.execute(query, (obj_id,))
        self.conn.commit()

    def add_object(self, table_name, obj_id):
        """
        A method that adds a new object with a given ID to a specified table,
        if it doesn't already exist.
        :param table_name: the name of the table to update.
        :param obj_id: the ID of the object to add.
        :return: True if the object was successfully added.
                    False if the object already exists.
        """
        select_query = f"SELECT * FROM {table_name} WHERE object = ?"
        self.cursor.execute(select_query, (obj_id,))

        result = self.cursor.fetchone()  # получаем первую строку результата запроса

        if result is None:
            query = f"INSERT INTO {table_name} (object) VALUES (?)"
            self.cursor.execute(query, (obj_id,))
            self.conn.commit()
            return True
        return False

    def close(self):
        """
        A method that closes the connection to the database.
        :return: None
        """
        self.conn.close()


db = Database()
