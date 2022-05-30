import sqlite3

class DBHelper:
    def __init__(self, dbname="recipes.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS recipes (id INT, name TEXT, ingredient TEXT, step TEXT)"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_recipe(self, id, recipe_name):
        stmt = "INSERT INTO recipes (id, name) VALUES (?, ?)"
        args = (id, recipe_name)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_ingredient(self, id, recipe_name, ingredient):
        stmt = "INSERT INTO recipes (id, name, ingredient) VALUES (?, ?, ?)"
        args = (id, recipe_name, ingredient)
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def get_ingredients(self, id, recipe_name):
        stmt =  "SELECT ingredient FROM recipes WHERE id = (?) AND name = (?) AND ingredient IS NOT NULL"
        args = (id, recipe_name)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def add_step(self, id, recipe_name, step):
        stmt = "INSERT INTO recipes (id, name, step) VALUES (?, ?, ?)"
        args = (id, recipe_name, step)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_steps(self, id, recipe_name):
        stmt = "SELECT step FROM recipes WHERE id = (?) AND name = (?) AND step IS NOT NULL"
        args = (id, recipe_name)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def delete_recipe(self, id, recipe_name):
        stmt = "DELETE FROM recipes WHERE id = (?) AND name = (?)"
        args = (id, recipe_name)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_recipes(self, id):
        stmt = "SELECT name FROM recipes WHERE id = (?)"
        args = (id, )
        return [x[0] for x in self.conn.execute(stmt, args)]

        