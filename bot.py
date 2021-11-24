from payments import Payments
from pathlib import Path
from typing import Dict
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
    CallbackContext,
)
import logging
import sys 
import re
import os


TOKEN = os.getenv('TELEGRAM_TOKEN')
MODE = os.getenv('MODE')
directory = 'pdf_files'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)

# Select environment
if MODE == "DEV":
    def run(updater: Update):
        # Start the Bot
        updater.start_polling()
        updater.idle()
        logger.info("Starting in development mode") 
elif MODE == "PROD":
    def run(updater: Update):
        PORT = int(os.environ.get('PORT', '8443'))
        HEROKU_APP_NAME = os.environ.get('HEROKU_APP_NAME')
        updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
        updater.bot.set_webhook(f'https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}')
        logger.info("Starting in production mode") 
else:
    logger.info("Missing mode")
    sys.exit()

# For custome keyboards
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Última quincena', 'Quincena #'],
    ['Configurar'],
]

config_keyboard = [['CURP', 'CURT'], ['Listo']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

config_markup = ReplyKeyboardMarkup(config_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation, display any stored data and ask user for input."""
    reply_text = "Hola, puedo ayudarte a descargar tus talones de pago si trabajas para la Secretaría de Educación en Colima."
    if context.user_data:
        reply_text += " Si deseas cambiar CURP o CURT podemos hacerlo en configuración."
        update.message.reply_text(reply_text, reply_markup=markup)
    else:
        reply_text += " \nNecesito me indiques:\n"
        if 'curp' not in context.user_data.keys():
            reply_text += "- CURP\n" 
        if 'curt' not in context.user_data.keys():
            reply_text += "- CURT\n" 
        update.message.reply_text(reply_text, reply_markup=config_markup)

    return CHOOSING


def regular_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text.upper()
    context.user_data['choice'] = text
    if context.user_data.get(text):
        reply_text = (
            f'Tu {text.upper}? Actualmente tengo estos datos: {context.user_data[text]}'
        )
    else:
        reply_text = f'Tu {text}? Excelente, espero tu respuesta'
    update.message.reply_text(reply_text)

    return TYPING_REPLY


def received_information(update: Update, context: CallbackContext) -> int:
    """Store info provided by user and ask for the next category."""
    text = update.message.text
    category = context.user_data['choice']
    context.user_data[category] = text.upper()
    del context.user_data['choice']

    update.message.reply_text(
        "Muy bien, ahora sé lo siguiente:"
        f"{facts_to_str(context.user_data)}"
        "Puedes cambiarlos cuando quieras en el apartado de configuración",
        reply_markup=config_markup,
    )

    return CHOOSING


def show_data(update: Update, context: CallbackContext) -> None:
    """Display the gathered info."""
    update.message.reply_text(
        f"This is what you already told me: {facts_to_str(context.user_data)}"
    )


def done(update: Update, context: CallbackContext) -> int:
    """Display the gathered info and end the conversation."""
    if 'choice' in context.user_data:
        del context.user_data['choice']

    update.message.reply_text(
        f"Se han guardado tus siguientes datos: {facts_to_str(context.user_data)}",
        reply_markup=markup,
    )
    return ConversationHandler.END


def last_payment(update: Update, context: CallbackContext) -> None:
    curp = context.user_data['CURP']
    curt = context.user_data['CURT']
    chat_id = update.effective_user.id

    update.message.reply_text('Preparando envío...', reply_markup=markup)
    payment = Payments(curp, curt)
    # Downoload the last payment
    filenames = payment.download_last()
    # Sending all pdf files
    for filename in filenames:
        with open(filename, "rb") as file:
            context.bot.send_document(chat_id=chat_id, document=file)

def payment(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Próximamente...', reply_markup=markup)


"""Run the bot."""
# Create the Updater and pass it your bot's token.
persistence = PicklePersistence(filename='conversationbot')
updater = Updater(TOKEN, persistence=persistence)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher

# Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSING: [
            MessageHandler(
                Filters.regex(re.compile('^(CURP|CURT)$', re.IGNORECASE)), regular_choice
            )
        ],
        TYPING_CHOICE: [
            MessageHandler(
                Filters.text & ~(Filters.command | Filters.regex('^Listo$')), regular_choice
            )
        ],
        TYPING_REPLY: [
            MessageHandler(
                Filters.text & ~(Filters.command | Filters.regex('^Listo$')),
                received_information,
            )
        ],
    },
    fallbacks=[MessageHandler(Filters.regex('^Listo$'), done)],
    name="my_conversation",
    persistent=True,
)

dispatcher.add_handler(conv_handler)

show_data_handler = CommandHandler('show_data', show_data)
dispatcher.add_handler(show_data_handler)

last_payment_handler = MessageHandler(Filters.regex(re.compile('^(última quincena|ultima quincena)$', re.IGNORECASE)), last_payment)
dispatcher.add_handler(last_payment_handler)

payment_handler = MessageHandler(Filters.regex(re.compile('^(Quincena #)$', re.IGNORECASE)), payment)
dispatcher.add_handler(payment_handler)

# Start depending environment mode
run(updater)

