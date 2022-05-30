from ast import Call
import os
import logging
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, RegexHandler
import requests
from dbhelper import DBHelper

API_KEY = os.getenv('API_KEY')

NAME, INGREDIENTS, STEPS = range(3)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = DBHelper()

def build_keyboard(items):
    keyboard = [[item] for item in items]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    return markup

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
        fr"{os.linesep}Search for new recipes from the internet by using /search along with your search query\.",
        reply_markup=ForceReply(selective=True),
    )

def add_recipe(update: Update, _: CallbackContext) -> int:
    """Asks user for the recipe name."""
    update.message.reply_text(
        "Please tell me the name of your new recipe or type /cancel if you change your mind anytime!"
    )
    
    return NAME

def name(update: Update, _: CallbackContext) -> int:
    """Stores given name and requests for a picture."""
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
            "Perfect! Please tell Mama what ingredients are needed next.\nType /done when you have entered all the ingredients."
        )

    return INGREDIENTS

def ingredients(update: Update, _: CallbackContext) -> int:
    """Stores the ingredients and asks for the steps."""
    user_id = update.message.from_user.id
    recipe_name = _.user_data['recipe name']
    ingredient = update.message.text
    ingredient_list = db.get_ingredients(user_id, recipe_name)

    if ingredient == "/done":
        update.message.reply_text(
        "Impressive! Now please write down the steps to the recipe. "
    )
        return STEPS
    elif ingredient in ingredient_list:
        update.message.reply_text("Ingredient has already been added.")
        return INGREDIENTS
    else:
        db.add_ingredient(user_id, recipe_name, ingredient)
        ingredient_list = ''
        for i in "\n".join(db.get_ingredients(user_id, recipe_name)):
            ingredient_list = (
                f'{ingredient_list}'
                f'\{i}'
            )
        update.message.reply_markdown_v2(
            f"*Ingredients{os.linesep}*"
            f"{ingredient_list}"
        )
        return INGREDIENTS

def steps(update: Update, _: CallbackContext) -> int:
    """Stores the steps of the recipe and ends the conversation."""
    user_id = update.message.from_user.id
    recipe_name = _.user_data['recipe name']
    step = update.message.text

    if step == "/done":
        ingredient_list = ''
        for i in "\n".join(db.get_ingredients(user_id, recipe_name)):
            ingredient_list = (
                f'{ingredient_list}'
                f'\{i}'
            )
        step_list = ''
        for i in "\n".join(db.get_steps(user_id, recipe_name)):
            step_list = (
                f'{step_list}'
                f'\{i}'
            )

        msg = (
            f'Terrific\! This is your new recipe:{os.linesep}{os.linesep}'
            f'*Recipe Name*{os.linesep}'
            f'{recipe_name}{os.linesep}{os.linesep}'
            f'*Ingredients*{os.linesep}'
            f'{ingredient_list}{os.linesep}'
            f'{os.linesep}*Directions*{os.linesep}'
            f'{step_list}'
        )
        update.message.reply_markdown_v2(msg)

        _.user_data.clear()
        return ConversationHandler.END
    else:
        db.add_step(user_id, recipe_name, step)
        step_list = ''
        for i in "\n".join(db.get_steps(user_id, recipe_name)):
            step_list = (
                f'{step_list}'
                f'\{i}'
            )
        update.message.reply_markdown_v2(
            f'*Directions*{os.linesep}'
            f'{step_list}'
        )
        return STEPS

def view_recipe(update: Update, _: CallbackContext) -> None:
    """Allows user to view an existing recipe."""
    user_id = update.message.from_user.id
    recipes = db.get_recipes(user_id)
    keyboard = build_keyboard(recipes)
    update.message.reply_text("Which recipe would you like to view?", reply_markup=keyboard)

def edit_recipe(update: Update, _: CallbackContext) -> None:
    """Allows user to edit the details of a stored recipe."""

def delete_recipe(update: Update, _: CallbackContext) -> None:
    """Deletes an entire recipe."""
    user_id = update.message.from_user.id
    recipes = db.get_items(user_id)
    keyboard = build_keyboard(recipes)
    update.message.reply_text("Select a recipe to delete", reply_markup=keyboard)

def search_recipes(update: Update, _: CallbackContext) -> None:
    """Returns the related recipes from the given keywords."""
    input = update.message.text
    keywords_list = list(map(lambda x: str(x), input.split(" ")[1:]))

def cancel(update: Update, _: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text(
        "It's OK! You can always come back to Mama when you are ready to add your recipe!"
    )

    user_id = update.message.from_user.id
    if 'recipe name' in _.user_data:
        db.delete_recipe(user_id, _.user_data['recipe name'])
    _.user_data.clear()
    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_KEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Create the Conversation Handler
    conv_handler_1 = ConversationHandler(
        entry_points=[CommandHandler("add", add_recipe)],
        states={
            NAME: [MessageHandler(Filters.text & (~ Filters.command), name)],
            INGREDIENTS: [MessageHandler(Filters.text & (~ Filters.command) | Filters.regex('/done'), ingredients)],
            STEPS: [MessageHandler(Filters.text & (~ Filters.command) | Filters.regex('/done'), steps)]

        },
        fallbacks=[CommandHandler("cancel", cancel)]

    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler_1)
    dispatcher.add_handler(CommandHandler("view", view_recipe))
    dispatcher.add_handler(CommandHandler("edit", edit_recipe))
    dispatcher.add_handler(CommandHandler("delete", delete_recipe))
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