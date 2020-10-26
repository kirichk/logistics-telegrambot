import logging
import os
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from tools.validators import logger_factory


logger = logging.getLogger(__name__)
GROUP = os.getenv("GROUP")
debug_requests = logger_factory(logger=logger)


@debug_requests
def cancel_handler(update: Update, context: CallbackContext):
    """ Отменить весь процесс диалога. Данные будут утеряны
    """
    update.message.reply_text('Отмена. Для начала с нуля нажмите /start')
    return ConversationHandler.END


@debug_requests
def echo_handler(update: Update, context: CallbackContext):
    try:
        update.message.reply_text(
            'Нажмите /start для заполнения анкеты!',
        )
    except AttributeError:
        pass
