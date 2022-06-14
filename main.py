from ast import Call
from distutils.command.build import build
from email.message import Message
import os
import logging
from subprocess import call
from turtle import update
from telegram import CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove, Update, ForceReply, ReplyKeyboardMarkup, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import requests
from dbhelper import DBHelper

API_KEY = os.getenv('API_KEY')

NAME, SERVINGS, INGREDIENTS, STEPS, SEND_RECIPE, CONFIRMATION, DELETION = range(7)
RECIPE_CHOICE, RECIPE_PART, EDIT_NAME, EDIT_SERVINGS, EDIT_INGREDIENTS, EDIT_STEPS, END_ROUTES = range(7,14)
ADD_INGREDIENT, UPDATE_INGREDIENT, SAVE_INGREDIENT, DELETE_INGREDIENT = range(14,18)
ADD_STEP, UPDATE_STEP, SAVE_STEP, DELETE_STEP = range(18,22)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = DBHelper()

def build_keyboard(items):
    keyboard = [[item] for item in items]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    return markup

def build_inline_keyboard(buttons):
    keyboard = [[InlineKeyboardButton(col, callback_data=col) for col in row] for row in buttons]
    markup = InlineKeyboardMarkup(keyboard)
    return markup

def get_ingredient_list(user_id, recipe_name):
    ingredient_list = 'Ingredients\n'
    for ingredient in db.get_ingredients(user_id, recipe_name):
        ingredient_list = ingredient_list + "- " + ingredient + "\n"
    return ingredient_list

def get_step_list(user_id, recipe_name):
    step_list = 'Directions\n'
    count = 1
    for step in db.get_steps(user_id, recipe_name):
        step_list = step_list + str(count) + ". " + step + "\n"
        count+=1
    return step_list

def full_recipe(user_id, recipe_name):
    servings = db.get_servings(user_id, recipe_name)
    ingredients = get_ingredient_list(user_id, recipe_name)
    steps = get_step_list(user_id, recipe_name)
    if len(servings) == 0:
        msg = recipe_name + "\n\n" + ingredients + "\n" + steps
    else:
        msg = recipe_name + "\n\n" + "Serves " + servings[0] + "\n\n" + ingredients + "\n" + steps
    return msg

def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr"Hi {user.mention_markdown_v2()}\! I'm BotMaMa\! "
        fr"I can help you manage your recipes and even search for new ones from all over the web\.{os.linesep}"
        fr"{os.linesep}To add a new recipe, use /add\."
        fr"{os.linesep}To view your recipes, use /view\."
        fr"{os.linesep}To edit your recipes, use /edit\."
        fr"{os.linesep}To delete one of your recipes, use /delete\."
        fr"{os.linesep}Search for new recipes from the internet by using /search along with your search query\."
    )

def add_recipe(update: Update, _: CallbackContext) -> int:
    """Asks user for the recipe name."""
    update.message.reply_text(
        "Please tell me the name of your new recipe or type /cancel if you change your mind anytime!"
    )
    
    return NAME

def name(update: Update, _: CallbackContext) -> int:
    """Stores given name and asks for the yield of the recipe."""
    user_id = update.message.from_user.id
    recipes = db.get_recipes(user_id)
    recipe_name = update.message.text
    if recipe_name in recipes:
        update.message.reply_text("Recipe name already exists! Please choose a different name.")
        return NAME
    else:
        db.add_recipe(user_id, recipe_name) 
        _.user_data['recipe name'] = recipe_name
        update.message.reply_text(
            "Perfect! Next, please state the yield of your recipe. Type /skip if you are not sure." 
        )

    return SERVINGS

def servings(update: Update, _: CallbackContext) -> int:
    """Stores the yield of the recipe and asks for the ingredients needed."""
    servings = update.message.text
    recipe_name = _.user_data['recipe name']
    db.add_servings(update.message.from_user.id, recipe_name, servings)
    update.message.reply_text(
        "Okay! Your recipe serves " + servings + ".\n"
        "Please tell Mama what ingredients are needed next.\nType /done when you have entered all the ingredients."
    )
    return INGREDIENTS

def skip_servings(update: Update, _: CallbackContext) -> int:
    """Skips the recipe yield and asks for the ingredients needed."""
    update.message.reply_text(
        "It's okay. Please tell Mama what ingredients are needed next.\n"
        "Type /done when you have entered all the ingredients.")
    return INGREDIENTS

def ingredients(update: Update, _: CallbackContext) -> int:
    """Stores the ingredients and asks for the steps."""
    user_id = update.message.from_user.id
    recipe_name = _.user_data['recipe name']
    ingredient = update.message.text
    ingredient_list = db.get_ingredients(user_id, recipe_name)

    if ingredient == "/done":
        update.message.reply_text(
        "Impressive! Now please write down the steps to the recipe. Type /done when you have entered all the steps you need."
    )
        return STEPS
    elif ingredient in ingredient_list:
        update.message.reply_text("Ingredient has already been added.\nType /done if you have entered all the ingredients needed.")
        return INGREDIENTS
    else:
        db.add_ingredient(user_id, recipe_name, ingredient)
        update.message.reply_text(get_ingredient_list(user_id, recipe_name))
        return INGREDIENTS

def steps(update: Update, _: CallbackContext) -> int:
    """Stores the steps of the recipe and ends the conversation."""
    user_id = update.message.from_user.id
    recipe_name = _.user_data['recipe name']
    step = update.message.text

    if step == "/done":
        text = full_recipe(user_id, recipe_name)
        _.user_data.clear()
        update.message.reply_text("Terrific! This is your new recipe:\n\n" + text)
        return ConversationHandler.END
    else:
        db.add_step(user_id, recipe_name, step)
        update.message.reply_text(get_step_list(user_id, recipe_name))
        return STEPS

def cancel_add(update: Update, _: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text(
        "It's OK! You can always come back to Mama whenever you are ready!",
        reply_markup=ReplyKeyboardRemove()
    )

    user_id = update.message.from_user.id
    if 'recipe name' in _.user_data:
        db.delete_recipe(user_id, _.user_data['recipe name'])
    _.user_data.clear()
    return ConversationHandler.END

def view_recipe(update: Update, _: CallbackContext) -> int:
    """Allows user to view an existing recipe."""
    user_id = update.message.from_user.id
    recipes = db.get_recipes(user_id)
    if len(recipes) == 0:
        update.message.reply_text("You currently do not have any recipes stored. Use /add to leave your recipes with Mama!")
        return ConversationHandler.END
    else:
        keyboard = build_keyboard(recipes)
        update.message.reply_text("Which recipe would you like to view?", reply_markup=keyboard)
        return SEND_RECIPE

def send_recipe(update: Update, _: CallbackContext) -> int:
    """Sends the chosen recipe to the user."""
    user_id = update.message.from_user.id
    recipe_name = update.message.text
    if recipe_name in db.get_recipes(user_id):
        update.message.reply_text(full_recipe(user_id, recipe_name), reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("Sorry, Mama couldn't find the recipe.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def edit_recipe(update: Update, _: CallbackContext) -> int:
    """Allows user to edit the details of a stored recipe."""
    user_id = update.message.from_user.id
    _.user_data['user id'] = user_id
    recipes = db.get_recipes(user_id)
    if len(recipes) == 0:
        update.message.reply_text("Hmm, it seems like you do not have any recipes stored currently. Type /add to start adding new recipes!")
        return ConversationHandler.END
    else:
        keyboard = build_inline_keyboard([[recipe] for recipe in recipes])
        update.message.reply_text("Which recipe would you like to edit?", reply_markup=keyboard)
        return RECIPE_CHOICE

def edit_recipe_inline(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    recipes = db.get_recipes(_.user_data['user id'])
    keyboard = build_inline_keyboard([[recipe] for recipe in recipes])
    query.edit_message_text("Which recipe would you like to edit?")
    query.edit_message_reply_markup(keyboard)
    return RECIPE_CHOICE

def recipe_choice(update: Update, _: CallbackContext) -> int:
    """Stores the name of the recipe to be edited."""
    recipe_name = update.callback_query
    recipe_name.answer()
    _.user_data['recipe name'] = recipe_name.data
    user_id = _.user_data['user id']
    servings = db.get_servings(user_id, recipe_name.data)
    recipe = full_recipe(user_id, recipe_name.data)
    if len(servings) == 0:
        keyboard = build_inline_keyboard([["recipe name", "ingredients", "directions"], ["<< back to list of recipes"]])
    else:
        keyboard = build_inline_keyboard([["recipe name", "servings", "ingredients", "directions"], ["<< back to list of recipes"]])
    
    recipe_name.edit_message_text(
        recipe + "\nYou are currently editing '" + recipe_name.data + "'.\n"
        "Which part of the recipe would you like to edit?"
    )
    recipe_name.edit_message_reply_markup(keyboard)
    return RECIPE_PART

def edit_name(update: Update, _: CallbackContext) -> int:
    """Asks user for the new name of the recipe."""
    query = update.callback_query
    query.answer()
    current_name = _.user_data['recipe name']
    keyboard = [[InlineKeyboardButton("<< back", callback_data=current_name)]]

    query.edit_message_text(
        "Your recipe name is currently '" + current_name + "'.\n"
        "What would you like the new name of your recipe to be?"
    )
    query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
    return EDIT_NAME

def change_name(update: Update, _: CallbackContext) -> int:
    """Updates the recipe's name in the database."""
    new_name = update.message.text
    user_id = _.user_data['user id']
    current_name = _.user_data['recipe name']

    if new_name == current_name or new_name in db.get_recipes(user_id):
        keyboard = [[InlineKeyboardButton("<< back", callback_data=current_name)]]
        update.message.reply_text(
            "Sorry, please choose a different name.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDIT_NAME

    db.update_name(user_id, current_name, new_name)
    _.user_data['recipe name'] = new_name
    servings = db.get_servings(user_id, new_name)
    if len(servings) == 0:
        keyboard = build_inline_keyboard([["recipe name", "ingredients", "directions"], ["<< back to list of recipes"]])
    else:
        keyboard = build_inline_keyboard([["recipe name", "servings", "ingredients", "directions"], ["<< back to list of recipes"]])

    update.message.reply_text(
        "The name of your recipe has been changed from '" + current_name + "' to '" + new_name + "'.\n"
        "What else would you like to edit?",
        reply_markup=keyboard
    )
    return RECIPE_PART

def edit_servings(update: Update, _: CallbackContext) -> int:
    """Asks user for the new recipe yield."""
    query = update.callback_query
    query.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    current_serving = db.get_servings(user_id, recipe_name)
    keyboard = [[InlineKeyboardButton("back", callback_data=recipe_name)]]

    query.edit_message_text(
        "Your recipe currently serves " + current_serving[0] + ".\n"
        "What is the new yield of your recipe?"
    )
    query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
    return EDIT_SERVINGS

def change_servings(update: Update, _: CallbackContext) -> int:
    """Updates the serving stored in the database."""
    new_serving = update.message.text
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    current_serving = db.get_servings(user_id, recipe_name)[0]
    db.add_servings(user_id, recipe_name, new_serving)
    keyboard = build_inline_keyboard([["recipe name", "servings", "ingredients", "directions"], ["back to list of recipes"]])

    update.message.reply_text(
        "Your recipe now serves " + new_serving + " instead of " + current_serving + ".\n"
        "What else would you like to edit?",
        reply_markup=keyboard
    )
    return RECIPE_PART

def edit_ingredients(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    ingredient_list = get_ingredient_list(user_id, recipe_name)
    keyboard = [[
        InlineKeyboardButton("add an ingredient", callback_data="add"),
        InlineKeyboardButton("edit an ingredient", callback_data="edit"),
        InlineKeyboardButton("delete an ingredient", callback_data="delete")
    ], [
        InlineKeyboardButton("<< back", callback_data=recipe_name)
    ]]

    query.edit_message_text(
        ingredient_list + "\n"
        "What would you like to do with the list of ingredients?"
    )
    query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
    return EDIT_INGREDIENTS

def ingredients_list_operation(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    if query.data == "add":
        keyboard = build_inline_keyboard([["<< back"]])
        query.edit_message_text("Please tell Mama what ingredient you would like to add.")
        query.edit_message_reply_markup(keyboard)
        return ADD_INGREDIENT
    else:
        ingredients = db.get_ingredients(user_id, recipe_name)
        buttons = [[ingredient] for ingredient in ingredients]
        buttons.append(["<< back"])
        keyboard = build_inline_keyboard(buttons)
        if query.data == "edit":
            query.edit_message_text("Please select an ingredient to edit:")
            query.edit_message_reply_markup(keyboard)
            return UPDATE_INGREDIENT
        else:
            query.edit_message_text("Please select an ingredient to delete:")
            query.edit_message_reply_markup(keyboard)
            return DELETE_INGREDIENT

def add_ingredient(update: Update, _:CallbackContext) -> int:
    ingredient = update.message.text
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    if ingredient in db.get_ingredients(user_id, recipe_name):
        keyboard = build_inline_keyboard([["<< back"]])
        update.message.reply_text("Ingredient already exists! Please enter a different ingredient.", reply_markup=keyboard)
        return ADD_INGREDIENT
    else:
        keyboard = [[
            InlineKeyboardButton("add an ingredient", callback_data="add"),
            InlineKeyboardButton("edit an ingredient", callback_data="edit"),
            InlineKeyboardButton("delete an ingredient", callback_data="delete")
        ], [
            InlineKeyboardButton("<< back", callback_data=recipe_name)
        ]] 
        db.add_ingredient(user_id, recipe_name, ingredient)
        update.message.reply_text(
            "List of ingredients has been updated!\n\n" + get_ingredient_list(user_id, recipe_name) + "\nWhat else would you like to do?",
            reply_markup=InlineKeyboardMarkup(keyboard) 
        )
        return EDIT_INGREDIENTS

def update_ingredient(update: Update, _: CallbackContext) -> int:
    ingredient = update.callback_query
    ingredient.answer()
    _.user_data['ingredient'] = ingredient.data
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("<< back", callback_data="edit")]])

    ingredient.edit_message_text("What would you like to change " + ingredient.data + " to?")
    ingredient.edit_message_reply_markup(keyboard)
    return SAVE_INGREDIENT

def save_ingredient(update: Update, _: CallbackContext) -> int:
    new_ingredient = update.message.text
    current_ingredient = _.user_data['ingredient']
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    if new_ingredient in db.get_ingredients(user_id, recipe_name):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("<< back", callback_data="edit")]])
        update.message.reply_text(
            "This ingredient already exists in the ingredient list. Please send a different one.",
            reply_markup=keyboard
        )
        return SAVE_INGREDIENT
    else:
        db.update_ingredient(user_id, recipe_name, current_ingredient, new_ingredient)
        ingredients = db.get_ingredients(user_id, recipe_name)
        buttons = [[ingredient] for ingredient in ingredients]
        buttons.append(["<< back"])
        keyboard = build_inline_keyboard(buttons)
        update.message.reply_text(
            "List of ingredients has been updated!\n\n" + get_ingredient_list(user_id, recipe_name) + "\n"
            "Select another ingredient to update, or press back to return to the previous menu.",
            reply_markup=keyboard
        )
        return UPDATE_INGREDIENT

def delete_ingredient(update: Update, _: CallbackContext) -> int:
    ingredient = update.callback_query
    ingredient.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    db.delete_ingredient(user_id, recipe_name, ingredient.data)
    ingredients = db.get_ingredients(user_id, recipe_name)
    buttons = [[ingredient] for ingredient in ingredients]
    buttons.append(["<< back"])
    keyboard = build_inline_keyboard(buttons)
    ingredient.edit_message_text(
        "List of ingredients has been updated!\n\n" + get_ingredient_list(user_id, recipe_name) + "\n"
        "Select another ingredient to delete, or press back to return to the previous menu."
    )
    ingredient.edit_message_reply_markup(keyboard)
    return DELETE_INGREDIENT

def edit_steps(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    step_list = get_step_list(user_id, recipe_name)
    keyboard = [[
        InlineKeyboardButton("add a step", callback_data="add"),
        InlineKeyboardButton("edit a step", callback_data="edit"),
        InlineKeyboardButton("delete a step", callback_data="delete")
    ], [
        InlineKeyboardButton("<< back", callback_data=recipe_name)
    ]]

    query.edit_message_text(
        step_list + "\n"
        "What would you like to do with the directions?"
    )
    query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
    return EDIT_STEPS

def steps_list_operation(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    if query.data == "add":
        steps = db.get_steps(user_id, recipe_name)
        keyboard = ([[InlineKeyboardButton("<< back", callback_data="<< back")]])
        query.edit_message_text("Please tell Mama what's the next step to the recipe.")
        query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
        return ADD_STEP
    else:
        steps = db.get_steps(user_id, recipe_name)
        x = 1
        buttons = []
        for step in steps:
            buttons.append([InlineKeyboardButton(str(x), callback_data=step)])
            x+=1
        buttons.append([InlineKeyboardButton("<< back", callback_data="<< back")])
        if query.data == "edit":
            query.edit_message_text(get_step_list(user_id, recipe_name) + "\nPlease select a step to edit:")
            query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
            return UPDATE_STEP
        else:
            query.edit_message_text(get_step_list(user_id, recipe_name) + "\nPlease select a step to delete:")
            query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
            return DELETE_STEP

def add_step(update: Update, _:CallbackContext) -> int: # only allows user to append to the end of the directions
    step = update.message.text
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    keyboard = [[
        InlineKeyboardButton("add a step", callback_data="add"),
        InlineKeyboardButton("edit a step", callback_data="edit"),
        InlineKeyboardButton("delete a step", callback_data="delete")
    ], [
        InlineKeyboardButton("<< back", callback_data=recipe_name)
    ]] 
    db.add_step(user_id, recipe_name, step)
    update.message.reply_text(
        "The directions have been updated!\n\n" + get_step_list(user_id, recipe_name) + "\nWhat else would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard) 
    )
    return EDIT_STEPS

def update_step(update: Update, _: CallbackContext) -> int:
    step = update.callback_query
    step.answer()
    _.user_data['step'] = step.data
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("<< back", callback_data="edit")]])
    step.edit_message_text("What would you like to change the step '" + step.data + "' to?")
    step.edit_message_reply_markup(keyboard)
    return SAVE_STEP

def save_step(update: Update, _: CallbackContext) -> int:
    new_step = update.message.text
    current_step = _.user_data['step']
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    db.update_step(user_id, recipe_name, current_step, new_step)
    steps = db.get_steps(user_id, recipe_name)

    x = 1
    buttons = []
    for step in steps:
        buttons.append([InlineKeyboardButton(str(x), callback_data=step)])
        x+=1
    buttons.append([InlineKeyboardButton("<< back", callback_data="<< back")])
    update.message.reply_text(
        "The directions have been updated!\n\n" + get_step_list(user_id, recipe_name) + "\n"
        "Select another step to update, or press back to return to the previous menu.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return UPDATE_STEP

def delete_step(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = _.user_data['user id']
    recipe_name = _.user_data['recipe name']
    db.delete_step(user_id, recipe_name, query.data)
    steps = db.get_steps(user_id, recipe_name)

    x = 1
    buttons = []
    for step in steps:
        buttons.append([InlineKeyboardButton(str(x), callback_data=step)])
        x+=1
    buttons.append([InlineKeyboardButton("<< back", callback_data="<< back")])
    query.edit_message_text(
        "The directions have been updated!\n\n" + get_step_list(user_id, recipe_name) + "\n"
        "Select another step to delete, or press back to return to the previous menu."
    )
    query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
    return DELETE_STEP

def edit_timeout(update: Update, _: CallbackContext) -> int:
    update.message.reply_text("Editing has been cancelled.")
    return ConversationHandler.END

def delete_recipe(update: Update, _: CallbackContext) -> int:
    """Asks user for a recipe to delete."""
    user_id = update.message.from_user.id
    _.user_data['user id'] = user_id
    recipes = db.get_recipes(user_id)
    if len(recipes) == 0:
        update.message.reply_text("Your recipe book is already empty.")
        return ConversationHandler.END
    else:
        keyboard = build_inline_keyboard([[recipe] for recipe in recipes])
        update.message.reply_text("Please select a recipe to delete.", reply_markup=keyboard)
        return CONFIRMATION

def confirmation(update: Update, _: CallbackContext) -> int:
    """Makes sure user deletes the correct recipe."""
    recipe_name = update.callback_query
    recipe_name.answer()
    _.user_data["recipe name"] = recipe_name.data
    keyboard = build_inline_keyboard([["yes", "no"]])
    recipe_name.edit_message_text(
        "Are you sure you want to delete '" + recipe_name.data + "'? Mama won't be able to recover any deleted recipes!"
    )
    recipe_name.edit_message_reply_markup(keyboard)
    return DELETION

def deletion(update: Update, _: CallbackContext) -> None:
    """Deletes recipe from the database."""
    answer = update.callback_query
    answer.answer()
    if answer.data == "yes":
        user_id = _.user_data['user id']
        recipe_name = _.user_data["recipe name"]
        db.delete_recipe(user_id, recipe_name)
        _.user_data.clear()
        answer.edit_message_text(recipe_name + " has been deleted from your recipes.")
    elif answer.data == "no":
        _.user_data.clear()
        answer.edit_message_text("Seems like you've changed your mind!")

def search_recipes(update: Update, _: CallbackContext) -> None:
    """Returns the related recipes from the given keywords."""
    input = update.message.text
    keywords_list = list(map(lambda x: str(x), input.split(" ")[1:]))

def exit(update: Update, _: CallbackContext) -> int:
    """Exits current conversation handler when a new valid command is sent."""
    _.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_KEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Create the Conversation Handler
    add_recipe_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_recipe)],
        states={
            NAME: [MessageHandler(Filters.text & (~ Filters.command), name)],
            SERVINGS: [MessageHandler(Filters.text & (~ Filters.command), servings), CommandHandler("skip", skip_servings)],
            INGREDIENTS: [MessageHandler(Filters.text & (~ Filters.command) | Filters.regex('/done'), ingredients)],
            STEPS: [MessageHandler(Filters.text & (~ Filters.command) | Filters.regex('/done'), steps)]
        },
        fallbacks=[CommandHandler("cancel", cancel_add)]
    )

    view_recipe_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("view", view_recipe)],
        states = {
            SEND_RECIPE: [MessageHandler(Filters.text & (~ Filters.command), send_recipe)]
        },
        fallbacks=[MessageHandler(Filters.command, exit)],
        allow_reentry=True
    )

    edit_recipe_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_recipe)],
        states = {
            RECIPE_CHOICE: [CallbackQueryHandler(recipe_choice, pattern="(?!^edit done|I'm done editing$)(^.*$)")], 
            RECIPE_PART: [
                CallbackQueryHandler(edit_name, pattern="^recipe name$"),
                CallbackQueryHandler(edit_servings, pattern="^servings$"),
                CallbackQueryHandler(edit_ingredients, pattern="^ingredients$"),
                CallbackQueryHandler(edit_steps, pattern="^directions$"),
                CallbackQueryHandler(edit_recipe_inline, pattern="^<< back to list of recipes$")
            ],
            EDIT_NAME: [
                CallbackQueryHandler(recipe_choice), MessageHandler(Filters.text, change_name)],
            EDIT_SERVINGS: [CallbackQueryHandler(recipe_choice), MessageHandler(Filters.text, change_servings)],
            EDIT_INGREDIENTS: [
                CallbackQueryHandler(ingredients_list_operation, pattern="^add|edit|delete$"),
                CallbackQueryHandler(recipe_choice)
            ],
            ADD_INGREDIENT: [CallbackQueryHandler(edit_ingredients), MessageHandler(Filters.text, add_ingredient)],
            UPDATE_INGREDIENT: [
                CallbackQueryHandler(edit_ingredients, pattern="^<< back$"),
                CallbackQueryHandler(update_ingredient)
            ],
            SAVE_INGREDIENT: [CallbackQueryHandler(ingredients_list_operation), MessageHandler(Filters.text, save_ingredient)],
            DELETE_INGREDIENT: [
                CallbackQueryHandler(edit_ingredients, pattern="^<< back$"),
                CallbackQueryHandler(delete_ingredient)
            ],
            EDIT_STEPS: [
                CallbackQueryHandler(steps_list_operation, pattern="^add|edit|delete$"),
                CallbackQueryHandler(recipe_choice)
            ],
            ADD_STEP: [CallbackQueryHandler(edit_steps), MessageHandler(Filters.text, add_step)],
            UPDATE_STEP: [
                CallbackQueryHandler(edit_steps, pattern="^<< back$"),
                CallbackQueryHandler(update_step)
            ],
            SAVE_STEP: [CallbackQueryHandler(steps_list_operation), MessageHandler(Filters.text, save_step)],
            DELETE_STEP: [
                CallbackQueryHandler(edit_steps, pattern="^<< back$"),
                CallbackQueryHandler(delete_step)
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, edit_timeout)]
        },
        fallbacks=[
            CommandHandler("exit", exit), 
            MessageHandler(Filters.command, exit)
        ],
        conversation_timeout=300,
        allow_reentry=True
    )

    delete_recipe_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_recipe)],
        states = {
            CONFIRMATION: [CallbackQueryHandler(confirmation)],
            DELETION: [CallbackQueryHandler(deletion)]
        },
        fallbacks=[MessageHandler(Filters.command, exit)],
        allow_reentry=True
    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(add_recipe_conv_handler, 4)
    dispatcher.add_handler(view_recipe_conv_handler, 3)
    dispatcher.add_handler(edit_recipe_conv_handler, 2)
    dispatcher.add_handler(delete_recipe_conv_handler, 1)
    dispatcher.add_handler(CommandHandler("search", search_recipes))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    db.setup()
    main()