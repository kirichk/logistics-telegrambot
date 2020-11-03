import logging
from telegram import Bot
import re
import os
from telegram.ext import (CallbackQueryHandler, Updater, MessageHandler,
                            CommandHandler, ConversationHandler, Filters)
from telegram.utils.request import Request
from tools.database import create_users_table, create_orders_table
from handlers import (start_buttons_handler, phone_handler, name_handler,
                            role_handler, ownership_handler,
                            company_name_handler,menu_handler,
                            menu_choice_handler, startpoint_handler,
                            endpoint_handler, weight_handler,
                            weight_limitations_handler, mileage_handler,
                            cargo_handler, calendar_handler, price_handler, payment_handler,
                            confirmation_handler, order_acception_handler,
                            done_orders_handler, confirmed_orders_handler)
from tools.additional_handlers import cancel_handler, echo_handler


logger = logging.getLogger(__name__)

MODE = os.getenv("MODE")
TOKEN = os.getenv('TOKEN')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
PORT = int(os.environ.get("PORT", "8443"))

(PHONE, NAME, ROLE , OWNERSHIP, COMPANY_NAME,
MENU, MENU_CHOICE, STARTPOINT, ENDPOINT, WEIGHT, MILEAGE, WEIGHT_LIMITATIONS,
CARGO, CALENDAR, PRICE, PAYMENT, CONFIRMATION) = range(17)


def main():
    logger.info('Started')
    create_users_table()
    create_orders_table()
    req = Request(
        connect_timeout=30.0,
        read_timeout=1.0,
        con_pool_size=8,
    )
    bot = Bot(
        token=TOKEN,
        request=req,
    )
    updater = Updater(
        bot=bot,
        use_context=True,
    )

    # Проверить что бот корректно подключился к Telegram API
    info = bot.get_me()
    logger.info(f'Bot info: {info}')

    # Навесить обработчики команд
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_buttons_handler),
            CommandHandler('menu', menu_handler),
            CallbackQueryHandler(order_acception_handler,
                                    pattern=r'(order).[0-9]+',
                                    pass_user_data=True),
            CallbackQueryHandler(order_acception_handler,
                                    pattern=r'(customer).[0-9]+',
                                    pass_user_data=True),
            CallbackQueryHandler(done_orders_handler,
                                    pattern=r'(done).[0-9]+',
                                    pass_user_data=True),
            CallbackQueryHandler(confirmed_orders_handler,
                                    pattern=r'(confirm).[0-9]+',
                                    pass_user_data=True),
            CallbackQueryHandler(menu_handler,
                                    pattern=r'(menu)',
                                    pass_user_data=True),
            CallbackQueryHandler(menu_choice_handler,
                                    pattern=r'(active_orders)',
                                    pass_user_data=True),
            CallbackQueryHandler(menu_choice_handler,
                                    pattern=r'(new_order)',
                                    pass_user_data=True),
            CallbackQueryHandler(menu_choice_handler,
                                    pattern=r'(previous_orders)',
                                    pass_user_data=True),
        ],
        states={
            PHONE: [MessageHandler(Filters.all, phone_handler,
                                    pass_user_data=True),],
            NAME: [MessageHandler(Filters.all, name_handler,
                                    pass_user_data=True),],
            ROLE : [CallbackQueryHandler(role_handler,
                                    pass_user_data=True),],
            OWNERSHIP: [CallbackQueryHandler(ownership_handler,
                                    pass_user_data=True),],
            COMPANY_NAME: [MessageHandler(Filters.all, company_name_handler,
                                    pass_user_data=True),],
            MENU: [CallbackQueryHandler(menu_handler,
                                    pass_user_data=True),],
            MENU_CHOICE: [CallbackQueryHandler(menu_choice_handler,
                                    pass_user_data=True),],
            STARTPOINT: [MessageHandler(Filters.all, startpoint_handler,
                                    pass_user_data=True),],
            ENDPOINT: [MessageHandler(Filters.all, endpoint_handler,
                                    pass_user_data=True),],
            WEIGHT: [MessageHandler(Filters.all, weight_handler,
                                    pass_user_data=True),],
            MILEAGE: [MessageHandler(Filters.all, mileage_handler,
                                    pass_user_data=True),],
            WEIGHT_LIMITATIONS: [CallbackQueryHandler(
                                    weight_limitations_handler,
                                    pass_user_data=True),
                                MessageHandler(Filters.all,
                                    weight_limitations_handler,
                                    pass_user_data=True),],
            CARGO: [MessageHandler(Filters.all, cargo_handler,
                                    pass_user_data=True),],
            CALENDAR: [CallbackQueryHandler(calendar_handler,
                                    pass_user_data=True),],
            PRICE: [CallbackQueryHandler(price_handler,
                                    pass_user_data=True),],
            PAYMENT: [MessageHandler(Filters.all, payment_handler,
                                    pass_user_data=True),],
            CONFIRMATION: [CallbackQueryHandler(confirmation_handler,
                                    pass_user_data=True),],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handler),
        ],
    )
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(MessageHandler(Filters.all, echo_handler))

    # Начать бесконечную обработку входящих сообщений
    if MODE == "dev":
        updater.start_polling()
        updater.idle()
        logger.info('Stopped')
    elif MODE == "prod":
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))


if __name__ == '__main__':
    main()
