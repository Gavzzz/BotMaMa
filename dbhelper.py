import sqlite3

class DBHelper:
    def __init__(self, dbname="recipes.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS recipes ( id INT, name TEXT)"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_item(self, id, recipe_name):
        stmt = "INSERT INTO recipes (id, name) VALUES (?, ?)"
        args = (id, recipe_name)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_item(self, id, recipe_name):
        stmt = "DELETE FROM recipes WHERE id = (?) AND name = (?)"
        args = (id, recipe_name)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items(self, id):
        stmt = "SELECT name FROM recipes WHERE id = (?)"
        args = (id, )
        return [x[0] for x in self.conn.execute(stmt, args)]

        