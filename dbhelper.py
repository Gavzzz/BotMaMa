import sqlite3

class DBHelper:
    def __init__(self, dbname="recipes.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        stmt = (''' CREATE TABLE IF NOT EXISTS user
                    (user_id INT,
                     chat_id INT,
                     username TEXT,
                     PRIMARY KEY(user_id, chat_id)
                    );''')
        self.conn.execute(stmt)
        stmt = (''' CREATE TABLE IF NOT EXISTS recipe
                   (recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_name TEXT NOT NULL,
                    picture_url TEXT,
                    servings TEXT,
                    user_id INT NOT NULL,
                    public INT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES user(user_id) ON UPDATE CASCADE ON DELETE CASCADE
                   );''')
        self.conn.execute(stmt)
        stmt = (''' CREATE TABLE IF NOT EXISTS ingredient
                   (ingredient_name TEXT NOT NULL,
                    recipe_id INT NOT NULL,
                    FOREIGN KEY(recipe_id) REFERENCES recipe(recipe_id) ON UPDATE NO ACTION ON DELETE CASCADE
                   );''')
        self.conn.execute(stmt)
        stmt = (''' CREATE TABLE IF NOT EXISTS step
                   (details TEXT NOT NULL,
                    recipe_id INT NOT NULL,
                    FOREIGN KEY(recipe_id) REFERENCES recipe(recipe_id) ON UPDATE NO ACTION ON DELETE CASCADE
                   );''')
        self.conn.execute(stmt)
        self.conn.commit()


    def add_user(self, user_id, chat_id, username):
        stmt = "INSERT OR IGNORE INTO user (user_id, chat_id, username) VALUES (?, ?, ?)"
        args = (user_id, chat_id, username)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def update_username(self, user_id, username):
        stmt = "UPDATE user SET username = (?) WHERE user_id = (?) AND username NOT IN (?)"
        args = (username, user_id, (username))
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_user_id(self, username):
        stmt = "SELECT user_id FROM user WHERE username = (?)"
        args = (username, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_all_chat_id(self):
        stmt = "SELECT chat_id FROM user"
        return [x[0] for x in self.conn.execute(stmt)]

    def change_privacy(self, user_id, recipe_name, privacy):
        stmt = "UPDATE recipe SET public = (?) WHERE user_id = (?) AND recipe_name = (?)"
        args = (privacy, user_id, recipe_name)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_recipe(self, user_id, recipe_name):
        stmt = "INSERT INTO recipe (recipe_name, user_id, public) VALUES (?, ?, ?)"
        args = (recipe_name, user_id, 1)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def is_public(self, user_id, recipe_name):
        stmt = "SELECT public FROM recipe WHERE recipe_name = (?) AND user_id = (?)"
        args = (recipe_name, user_id)
        l = [x[0] for x in self.conn.execute(stmt, args)]
        return l[0] == 1

    def get_recipe_id(self, user_id, recipe_name):
        stmt = "SELECT recipe_id FROM recipe WHERE recipe_name = (?) AND user_id = (?)"
        args = (recipe_name, user_id)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def update_name(self, user_id, old_name, new_name):
        stmt = "UPDATE recipe SET recipe_name = (?) WHERE recipe_name = (?) AND user_id = (?)"
        args = (new_name, old_name, user_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_picture_url(self, user_id, recipe_name, picture_url):
        stmt = "UPDATE recipe SET picture_url = (?) WHERE recipe_name = (?) AND user_id = (?)"
        args = (picture_url, recipe_name, user_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_picture_url(self, user_id, recipe_name):
        stmt = "SELECT picture_url FROM recipe WHERE recipe_name = (?) AND user_id = (?) AND picture_url IS NOT NULL"
        args = (recipe_name, user_id)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def delete_picture_url(self, user_id, recipe_name):
        stmt = "UPDATE recipe SET picture_url = NULL where recipe_name = (?) AND user_id = (?)"
        args = (recipe_name, user_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_servings(self, user_id, recipe_name, servings):
        stmt = "UPDATE recipe SET servings = (?) WHERE recipe_name = (?) AND user_id = (?)"
        args = (servings, recipe_name, user_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_servings(self, user_id, recipe_name):
        stmt = "SELECT servings FROM recipe WHERE recipe_name = (?) AND user_id = (?) AND servings IS NOT NULL"
        args = (recipe_name, user_id)
        return [x[0] for x in self.conn.execute(stmt, args)]

    def delete_servings(self, user_id, recipe_name):
        stmt = "UPDATE recipe SET servings = NULL where recipe_name = (?) AND user_id = (?)"
        args = (recipe_name, user_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_ingredient(self, user_id, recipe_name, ingredient):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "INSERT INTO ingredient (ingredient_name, recipe_id) VALUES (?, ?)"
        args = (ingredient, recipe_id)
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def get_ingredients(self, user_id, recipe_name):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt =  "SELECT ingredient_name FROM ingredient WHERE recipe_id = (?)"
        args = (recipe_id, )
        return [x[0] for x in self.conn.execute(stmt, args)]
    
    def update_ingredient(self, user_id, recipe_name, current_ingredient, new_ingredient):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "UPDATE ingredient SET ingredient_name = (?) WHERE ingredient_name = (?) AND recipe_id = (?)"
        args = (new_ingredient, current_ingredient, recipe_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_ingredient(self, user_id, recipe_name, ingredient):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "DELETE FROM ingredient WHERE ingredient_name = (?) AND recipe_id = (?)"
        args = (ingredient, recipe_id)
        self.conn.execute(stmt, args)
        self.conn.commit

    def add_step(self, user_id, recipe_name, step):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "INSERT INTO step (details, recipe_id) VALUES (?, ?)"
        args = (step, recipe_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_steps(self, user_id, recipe_name):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "SELECT details FROM step WHERE recipe_id = (?)"
        args = (recipe_id, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def update_step(self, user_id, recipe_name, current_step, new_step):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "UPDATE step SET details = (?) WHERE details = (?) AND recipe_id = (?)"
        args = (new_step, current_step, recipe_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_step(self, user_id, recipe_name, step):
        recipe_id = self.get_recipe_id(user_id, recipe_name)[0]
        stmt = "DELETE FROM step WHERE details = (?) AND recipe_id = (?)"
        args = (step, recipe_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_recipe(self, user_id, recipe_name):
        stmt = "DELETE FROM recipe WHERE recipe_name = (?) AND user_id = (?)"
        args = (recipe_name, user_id)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_recipes(self, user_id):
        stmt = "SELECT recipe_name FROM recipe WHERE user_id = (?)"
        args = (user_id, )
        return [x[0] for x in self.conn.execute(stmt, args)]
    
    def get_public_recipes(self, user_id):
        stmt = "SELECT recipe_name FROM recipe WHERE user_id = (?) AND public = (?)"
        args = (user_id, 1)
        return [x[0] for x in self.conn.execute(stmt, args)]

        