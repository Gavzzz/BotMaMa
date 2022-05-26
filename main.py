import os
import logging
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import requests

API_KEY = os.getenv('API_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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

def add_recipe(update: Update, _: CallbackContext) -> None:
    """Allows user to add a new recipe."""

def view_recipe(update: Update, _: CallbackContext) -> None:
    """Allows user to view an existing recipe."""

def edit_recipe(update: Update, _: CallbackContext) -> None:
    """Allows user to edit the details of a stored recipe."""

def delete_recipe(update: Update, _: CallbackContext) -> None:
    """Deletes an entire recipe."""

def search_recipes(update: Update, _: CallbackContext) -> None:
    """Returns the related recipes from the given keywords"""
    input = update.message.text
    keywords_list = list(map(lambda x: str(x), input.split(" ")[1:]))

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(API_KEY)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add", add_recipe))
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
    main()