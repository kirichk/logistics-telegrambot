import logging
import os
from telegram import (Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update,
                        ReplyKeyboardMarkup, KeyboardButton)
from telegram.ext import (CallbackContext, CallbackQueryHandler, Updater,
                        MessageHandler, CommandHandler, ConversationHandler,
                        Filters)
from telegram.utils.request import Request

from tools.database import (post_sql_query, create_users_table,
                        register_user, create_orders_table, register_order)
from tools.validators import (USER_MAP, OWNERSHIP_MAP, PAYMENT_MAP,
                                MENU_CHOICES, gender_hru, validate_id,
                                validate_float, validate_chosed_weight,
                                logger_factory)
from tools.calendar import telegramcalendar
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)
ADMIN = os.getenv("ADMIN")
GROUP = os.getenv("GROUP")
TG_APP_NAME = os.getenv('TG_APP_NAME')
debug_requests = logger_factory(logger=logger)

(PHONE, NAME, ROLE , OWNERSHIP, COMPANY_NAME, ID_CODE,
MENU, MENU_CHOICE, STARTPOINT, ENDPOINT, WEIGHT, MILEAGE, WEIGHT_LIMITATIONS,
CARGO, CALENDAR, PRICE, PAYMENT, CONFIRMATION) = range(18)


@debug_requests
def start_buttons_handler(update: Update, context: CallbackContext):
    contact_keyboard = KeyboardButton('Поделиться номером',
                                        request_contact=True,)
    reply_markup = ReplyKeyboardMarkup(keyboard=[[ contact_keyboard ]],
                                        resize_keyboard=True,
                                        one_time_keyboard=True)
    update.message.reply_text(
                    'Здравствуйте! Для того чтобы начать регистрацию'\
                    ' пожалуйста нажмите "Поделиться номером".',
                    reply_markup=reply_markup)
    return PHONE


@debug_requests
def phone_handler(update: Update, context: CallbackContext):
    """ Начало взаимодействия по клику на inline-кнопку
    """
    try:
        context.user_data[PHONE] = update.message.contact.phone_number
    except AttributeError:
        pass
    # Спросить имя
    update.message.reply_text(
        text='Спасибо! Теперь введите Ваше ФИО чтобы продолжить.',
    )
    return NAME


@debug_requests
def name_handler(update: Update, context: CallbackContext):
    context.user_data[NAME] = update.message.text
    logger.info('user_data: %s', context.user_data)

    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=value, callback_data=key)]
                                    for key, value in USER_MAP.items()
        ],
    )
    update.message.reply_text(
        text='Выберите тип пользователя.',
        reply_markup=inline_buttons,
    )
    return ROLE


@debug_requests
def role_handler(update: Update, context: CallbackContext):
    role = int(update.callback_query.data)
    context.user_data[ROLE] = role
    logger.info('user_data: %s', context.user_data)
    current_user = update.callback_query.message.chat.username
    now = datetime.now()

    if role == 2:
        register_user(username=current_user,
                        full_name=context.user_data[NAME],
                        role=context.user_data[ROLE],
                        ownership='',
                        company_name='',
                        id_code='',
                        phone=context.user_data[PHONE],
                        reg_date=now.strftime("%m/%d/%Y, %H:%M:%S"),
                        chat_id=update.callback_query.message.chat.id)

        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Перейти в меню',
                                        callback_data='id')],
            ],
        )
        update.callback_query.message.reply_text(
            text='Вы успешно зарегистрированы. Чтобы просматривать все заявки, подпишитесь на канал @LogisticsTransBotOrders',
            reply_markup=inline_buttons,
        )
        context.bot.send_message(chat_id=ADMIN,
                                text=f'Новый пользователь @{current_user}.\n'\
                                f'Роль: {USER_MAP[role]}.')
        return MENU
    else:
        # Спросить возраст
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=value, callback_data=key)
                                    for key, value in OWNERSHIP_MAP.items()],
            ],
        )
        update.callback_query.message.reply_text(
            text='Выберите форму собственности.',
            reply_markup=inline_buttons,
        )
        return OWNERSHIP


@debug_requests
def ownership_handler(update: Update, context: CallbackContext):
    context.user_data[OWNERSHIP] = update.callback_query.data
    logger.info('user_data: %s', context.user_data)

    update.callback_query.message.reply_text(
        text=f'Введите название компании.',
    )
    return COMPANY_NAME


@debug_requests
def company_name_handler(update: Update, context: CallbackContext):
    context.user_data[COMPANY_NAME] = update.message.text
    logger.info('user_data: %s', context.user_data)
    update.message.reply_text(
        text='Введите ИНН или ЕДРПО.',
    )
    return ID_CODE


@debug_requests
def id_code_handler(update: Update, context: CallbackContext):

    id = validate_id(update.message.text)
    while id is None:
        update.message.reply_text(
            text='Некорректный ИНН или ЕДРПО! Пожалуйста повторите попытку.',
        )
        return ID_CODE

    context.user_data[ID_CODE] = id
    logger.info('user_data: %s', context.user_data)
    current_user = update.message.chat.username
    now = datetime.now()

    register_user(username=current_user,
                    full_name=context.user_data[NAME],
                    role=context.user_data[ROLE],
                    ownership=context.user_data[OWNERSHIP],
                    company_name=context.user_data[COMPANY_NAME],
                    id_code=context.user_data[ID_CODE],
                    phone=context.user_data[PHONE],
                    reg_date=now.strftime("%m/%d/%Y, %H:%M:%S"),
                    chat_id=update.message.chat.id)

    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Перейти в меню', callback_data='id')],
        ],
    )
    update.message.reply_text(
        text='Вы успешно зарегистрированы. Чтобы просматривать все заявки, подпишитесь на канал @LogisticsTransBotOrders',
        reply_markup=inline_buttons,
    )
    context.bot.send_message(chat_id=ADMIN,
                            text=f'Новый пользователь @{current_user}.\n'\
                            f'Роль: {USER_MAP[int(context.user_data[ROLE])]}.')
    return MENU


@debug_requests
def menu_handler(update: Update, context: CallbackContext):
    try:
        request = update.callback_query.message
    except AttributeError:
        request = update.message
    current_user = request.chat.username
    try:
        user_role = post_sql_query(f'SELECT role FROM USERS WHERE username ='\
                                f' "{current_user}"')[0][0]
    except IndexError:
        request.reply_text(
            'Нажмите /start для заполнения анкеты!',
        )
        return ConversationHandler.END
    if int(user_role) == 3 or int(user_role) == 2:
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Создать заявку',
                                    callback_data='new_order')],
                [InlineKeyboardButton(text='Предыдущие заявки',
                                    callback_data='previous_orders')],
                [InlineKeyboardButton(text='Активные заявки',
                                    callback_data='active_orders')],
            ],
        )
    else:
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Предыдущие заявки',
                                    callback_data='previous_orders')],
                [InlineKeyboardButton(text='Активные заявки',
                                    callback_data='active_orders')],
            ],
        )
    request.reply_text(
        text=f'Вы в главном меню, чтобы вернуться сюда в любой момент '\
                'нажмите или введите /menu.\nВыберите действие которое нужно '\
                'выполнить.',
        reply_markup=inline_buttons,
    )
    return MENU_CHOICE


@debug_requests
def menu_choice_handler(update: Update, context: CallbackContext):
    current_user = update.callback_query.message.chat.username
    choice = update.callback_query.data
    try:
        user_role = post_sql_query(f'SELECT role FROM USERS WHERE username ='\
                                f' "{current_user}"')[0][0]
    except IndexError:
        request.reply_text(
            'Нажмите /start для заполнения анкеты!',
        )
        return ConversationHandler.END

    if choice == 'new_order':
        update.callback_query.message.reply_text(
            text='Введите пункт погрузки (область, город/cело/смт и тд.)'
        )
        return STARTPOINT
    elif choice == 'previous_orders':
        query_customer = post_sql_query(f'SELECT * FROM ORDERS WHERE status = '\
                        f'"Выполнен" AND username = "{current_user}"')
        query_carrier = post_sql_query(f'SELECT * FROM ORDERS WHERE status = '\
                        f'"Выполнен" AND carrier_username = "{current_user}"')
        if int(user_role) == 2 or int(user_role) == 3:
            for row in query_customer:
                update.callback_query.message.reply_text(
                    text=f'Пункт погрузки: {row[2]}\n'\
                    f'Пункт выгрузки: {row[3]}\n'\
                    f'Расстояние: {row[12]}км\n'\
                    f'Вес и тип: {row[4]}т {row[5]}\n'\
                    f'Ограничения: {row[11]}\n'
                    f'Тариф: {row[7]} грн/т, {row[8]}\n'\
                    f'Дата отгрузки: {row[6]}\n'\
                    f'Исполнитель: @{row[9]}'
                )
        else:
            for row in query_carrier:
                update.callback_query.message.reply_text(
                    text=f'Пункт погрузки: {row[2]}\n'\
                    f'Пункт выгрузки: {row[3]}\n'\
                    f'Расстояние: {row[12]}км\n'\
                    f'Вес и тип: {row[4]}т, {row[5]}\n'\
                    f'Ограничения: {row[11]}\n'
                    f'Тариф: {row[7]} грн/т {row[8]}\n'\
                    f'Дата отгрузки: {row[6]}\n'\
                    f'Заказчик: @{row[1]}'
                )
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Вернуться в меню',
                                        callback_data='menu')],
            ],
        )
        update.callback_query.message.reply_text(
            text='Выше перечень всех предыдущих заказов.',
            reply_markup=inline_buttons,
        )
        return MENU
    elif choice == 'active_orders':
        query_customer = post_sql_query(f'SELECT * FROM ORDERS WHERE status != '\
                        f'"Выполнен" AND username = "{current_user}"')
        query_carrier = post_sql_query(f'SELECT * FROM ORDERS WHERE status != '\
                        f'"Выполнен" AND carrier_username = "{current_user}"')
        if int(user_role) == 2 or int(user_role) == 3:
            for row in query_customer:
                update.callback_query.message.reply_text(
                    text=f'Пункт погрузки: {row[2]}\n'\
                    f'Пункт выгрузки: {row[3]}\n'\
                    f'Расстояние: {row[12]}км\n'\
                    f'Вес и тип: {row[4]}т {row[5]}\n'\
                    f'Ограничения: {row[11]}\n'
                    f'Тариф: {row[7]} грн/т, {row[8]}\n'\
                    f'Дата отгрузки: {row[6]}\n'\
                    f'Исполнитель: @{row[9]}'
                )
        else:
            for row in query_carrier:
                update.callback_query.message.reply_text(
                    text=f'Пункт погрузки: {row[2]}\n'\
                    f'Пункт выгрузки: {row[3]}\n'\
                    f'Расстояние: {row[12]}км\n'\
                    f'Вес и тип: {row[4]}т, {row[5]}\n'\
                    f'Ограничения: {row[11]}\n'
                    f'Тариф: {row[7]} грн/т {row[8]}\n'\
                    f'Дата отгрузки: {row[6]}\n'\
                    f'Заказчик: @{row[1]}'
                )
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Вернуться в меню',
                                        callback_data='menu')],
            ],
        )
        update.callback_query.message.reply_text(
            text='Выше перечень всех активных заказов.',
            reply_markup=inline_buttons,
        )
    return ConversationHandler.END


@debug_requests
def startpoint_handler(update: Update, context: CallbackContext):

    context.user_data[STARTPOINT] = update.message.text
    logger.info('user_data: %s', context.user_data)

    update.message.reply_text(
        text='Введите пункт выгрузки (область, город/cело/смт и тд.)'
    )

    return ENDPOINT


@debug_requests
def endpoint_handler(update: Update, context: CallbackContext):

    context.user_data[ENDPOINT] = update.message.text
    logger.info('user_data: %s', context.user_data)
    update.message.reply_text(
        text='Введите общий обьем груза в тоннах.'
    )
    return WEIGHT


@debug_requests
def weight_handler(update: Update, context: CallbackContext):
    weight = validate_float(update.message.text)
    while weight is None:
        update.message.reply_text(
            text='Некорректный вес! Пожалуйста повторите попытку.',
        )
        return WEIGHT
    context.user_data[WEIGHT] = weight
    logger.info('user_data: %s', context.user_data)

    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Нет ограничений',
                                    callback_data='no_limits')],
        ],
    )
    update.message.reply_text(
        text=f'Укажите какие либо ограничения на погрузке '\
            f'(высота/длина машины, самосвалы и тд.) Если ограничений нет, '\
            f'нажмите "Нет ограничений".',
        reply_markup=inline_buttons,
    )

    return WEIGHT_LIMITATIONS


@debug_requests
def weight_limitations_handler(update: Update, context: CallbackContext):
    try:
        request = update.callback_query.message
        weight_limitations = 'Нет ограничений'
    except AttributeError:
        request = update.message
        weight_limitations  = request.text

    context.user_data[WEIGHT_LIMITATIONS] = weight_limitations
    logger.info('user_data: %s', context.user_data)

    request.reply_text(
        text='Введите растояние между точками погрузки и выгрузки (км).'
    )
    return MILEAGE


@debug_requests
def mileage_handler(update: Update, context: CallbackContext):
    mileage = validate_float(update.message.text)
    while mileage is None:
        update.message.reply_text(
            text='Некорректный километраж! Пожалуйста повторите попытку.',
        )
        return MILEAGE
    context.user_data[MILEAGE] = mileage
    logger.info('user_data: %s', context.user_data)

    update.message.reply_text(
        text='Введите тип груза (ячмень, пшеница, и тд).'
    )
    return CARGO


@debug_requests
def cargo_handler(update: Update, context: CallbackContext):

    context.user_data[CARGO] = update.message.text
    logger.info('user_data: %s', context.user_data)

    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Выбрать дату',
                                    callback_data='new_order')],
        ],
    )
    update.message.reply_text(
        text='Выберите дату погрузки',
        reply_markup=inline_buttons,
    )

    return CALENDAR


@debug_requests
def calendar_handler(update: Update, context: CallbackContext):

    update.callback_query.message.reply_text(u'\U00002b07',
                        reply_markup=telegramcalendar.create_calendar())
    return PRICE


@debug_requests
def price_handler(update: Update, context: CallbackContext):
    selected,date = telegramcalendar.process_calendar_selection(update, context)
    if selected:
        context.user_data[CALENDAR] = date.strftime("%d/%m/%Y")
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="Вы выбрали %s" % (date.strftime("%d/%m/%Y")))
    update.callback_query.message.reply_text(
        text='Введите тариф (грн/т).'
    )
    return PAYMENT


@debug_requests
def payment_handler(update: Update, context: CallbackContext):
    price = validate_float(update.message.text)
    while price is None:
        update.message.reply_text(
            text='Некорректный тариф! Пожалуйста повторите попытку.',
        )
        return PAYMENT
    context.user_data[PRICE] = price
    logger.info('user_data: %s', context.user_data)

    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=value, callback_data=key)
                                    for key, value in PAYMENT_MAP.items()],
        ],
    )

    update.message.reply_text(
        text='Выберите тип оплаты.',
        reply_markup=inline_buttons,
    )

    return CONFIRMATION


@debug_requests
def confirmation_handler(update: Update, context: CallbackContext):

    context.user_data[PAYMENT] = PAYMENT_MAP[int(update.callback_query.data)]
    current_user = update.callback_query.message.chat.username
    startpoint = context.user_data[STARTPOINT]
    endpoint = context.user_data[ENDPOINT]
    weight = context.user_data[WEIGHT]
    cargo_type = context.user_data[CARGO]
    start_date = context.user_data[CALENDAR]
    price = context.user_data[PRICE]
    payment_type = context.user_data[PAYMENT]
    weight_limitations = context.user_data[WEIGHT_LIMITATIONS]
    mileage = context.user_data[MILEAGE]
    logger.info('user_data: %s', context.user_data)

    now = datetime.now()

    register_order(username=current_user,
                    startpoint=startpoint,
                    endpoint=endpoint,
                    weight=weight,
                    cargo_type=cargo_type,
                    start_date=start_date,
                    price=price,
                    payment_type=payment_type,
                    carrier_username='',
                    status='Ожидает исполнителя',
                    weight_limitations=weight_limitations,
                    mileage=mileage,
                    reg_date=now.strftime("%m/%d/%Y, %H:%M:%S"))

    order_id = post_sql_query(f'SELECT order_id FROM ORDERS WHERE username ='\
                                f' "{current_user}"')[-1][0]
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Перейти в меню', callback_data='menu')],
            [InlineKeyboardButton(text='Отменить заявку!',
                                callback_data=f'confirm-{order_id}')],
        ],
    )
    update.callback_query.message.reply_text(
        text=f'Ваша заявка успешно оформлена.'\
                f'№{order_id}\nПункт погрузки: {startpoint}\n'\
                f'Пункт выгрузки: {endpoint}\n'\
                f'Расстояние: {mileage}км\n'\
                f'Вес и тип: {weight}т {cargo_type}\n'\
                f'Тариф: {price} грн/т, {payment_type}\nДата отгрузки: '\
                f'{start_date}\nОграничения: {weight_limitations}',
        reply_markup=inline_buttons,
    )
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Принять заказ',
                                callback_data=f'order-{order_id}')],
            [InlineKeyboardButton(text='Информация о заказчике',
                                callback_data=f'customer-{order_id}')],
        ],
    )
    try:
        carriers_list = post_sql_query(f'SELECT chat_id FROM USERS WHERE role ='\
                                    f' "1"')[0]
        for carrier in carriers_list:
            context.bot.send_message(chat_id=carrier,
                            text=f'Новая заявка!\nПункт погрузки: {startpoint}\n'\
                            f'Пункт выгрузки: {endpoint}\n'\
                            f'Расстояние: {mileage}км\n'\
                            f'Вес и тип: {weight}т {cargo_type}\n'\
                            f'Тариф: {price} грн/т, {payment_type}\nДата отгрузки: '\
                            f'{start_date}\nОграничения: {weight_limitations}',
                            reply_markup=inline_buttons,)
    except IndexError:
        pass
    inline_buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Посмотреть детали',
                                url=f'tg://resolve?domain={TG_APP_NAME}')],
        ],
    )
    context.bot.send_message(chat_id=ADMIN,
                            text=f'Новая заявка! От @{current_user}\n'\
                            f'Пункт погрузки: {startpoint}\n'\
                            f'Пункт выгрузки: {endpoint}\n'\
                            f'Расстояние: {mileage}км\n'\
                            f'Вес и тип: {weight}т {cargo_type}\n'\
                            f'Тариф: {price} грн/т, {payment_type}\nДата отгрузки: '\
                            f'{start_date}\nОграничения: {weight_limitations}')
    context.bot.send_message(chat_id=GROUP,
                            text=f'Новая заявка!\n'\
                            f'Пункт погрузки: {startpoint}\n'\
                            f'Пункт выгрузки: {endpoint}\n'\
                            f'Расстояние: {mileage}км\n'\
                            f'Вес и тип: {weight}т {cargo_type}\n'\
                            f'Тариф: {price} грн/т, {payment_type}\nДата отгрузки: '\
                            f'{start_date}\nОграничения: {weight_limitations}',
                            reply_markup=inline_buttons,)
    return ConversationHandler.END


@debug_requests
def order_acception_handler(update: Update, context: CallbackContext):
    current_user = update.callback_query.message.chat.username
    order_id = update.callback_query.data.split('-')[1]
    current_order = post_sql_query(f'SELECT * FROM ORDERS WHERE order_id ='\
                                f' "{order_id}";')[0]
    customer_details = post_sql_query(f'SELECT * FROM USERS WHERE username ='\
                                f' "{current_order[1]}";')[0]
    carrier_details = post_sql_query(f'SELECT * FROM USERS WHERE username ='\
                                f' "{current_user}";')[0]
    now = datetime.now()
    diff = (datetime.strptime(now.strftime("%m/%d/%Y, %H:%M:%S"),
                                "%m/%d/%Y, %H:%M:%S") -
            datetime.strptime(current_order[-1],"%m/%d/%Y, %H:%M:%S")).days
    if diff >= 3:
        update.callback_query.message.reply_text(
            text='Заказ уже неавктивен.\nПерейти в меню - /menu'
        )
        post_sql_query(f'UPDATE ORDERS SET status = "Выполнен" '\
                        f'WHERE order_id = "{order_id}";')
        return ConversationHandler.END
    if current_order[10] == 'Взят в работу':
        update.callback_query.message.reply_text(
            text='Заказ уже взят в работу.\nПерейти в меню - /menu'
        )
        return ConversationHandler.END
    if current_order[10] == 'Выполнен':
        update.callback_query.message.reply_text(
            text='Заказ отменен.\nПерейти в меню - /menu'
        )
        return ConversationHandler.END
    if update.callback_query.data[:5] == 'order':
        post_sql_query(f'UPDATE ORDERS SET status = "Взят в работу", '\
                        f'carrier_username = "{current_user}" WHERE order_id ='\
                        f' "{current_order[0]}";')
        update.callback_query.message.reply_text(
            text=f'Вы подтвердили транспортировку по заявке №{current_order[0]}\n'\
                    f'Заказчик: @{current_order[1]}'
        )
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Выполнено!',
                                    callback_data=f'done-{order_id}')],
            ],
        )
        update.callback_query.message.reply_text(
            text='Когда заявка будет выполнена, нажмите '\
                    '"Выполнено!" чтобы закрыть ее. ',
            reply_markup=inline_buttons,
        )
        context.bot.send_message(chat_id=customer_details[-1],
                        text=f'Заявка №{current_order[0]} была принята '\
                                f'пользователем @{current_user}.')

    else:
        if int(customer_details[2]) == 2:
            update.callback_query.message.reply_text(
                text=f'Отправлено диспетчером!\n'\
                    f'Имя: {customer_details[1]}\n'\
                    f'Номер телефона: {customer_details[6]}\n'\
                    f'Telegram: @{customer_details[0]}'
            )
        else:
            update.callback_query.message.reply_text(
                text=f'Название компании: {customer_details[4]}\n'\
                    f'Имя: {customer_details[1]}\n'\
                    f'Номер телефона: {customer_details[6]}\n'\
                    f'Telegram: @{customer_details[0]}\n'
                    f'ИНН: {customer_details[5]}\n'\
                    f'Тип компании: {OWNERSHIP_MAP[int(customer_details[3])]}\n'\
            )


@debug_requests
def done_orders_handler(update: Update, context: CallbackContext):
    current_user = update.callback_query.message.chat.username
    order_id = update.callback_query.data.split('-')[1]
    current_order = post_sql_query(f'SELECT * FROM ORDERS WHERE order_id ='\
                                f' "{order_id}";')[0]
    customer_details = post_sql_query(f'SELECT * FROM USERS WHERE username ='\
                                f' "{current_order[1]}";')[0]
    if current_order[10] == 'Выполнен':
        update.callback_query.message.reply_text(
            text='Заказ отменен.\nПерейти в меню - /menu'
        )
        return ConversationHandler.END
    else:
        update.callback_query.message.reply_text(
            text=f'Заявка отмечена как выполненная. Ожидайте подтверждения от '\
                f'@{customer_details[0]}\nПерейти в меню - /menu')
        inline_buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Подтвердить!',
                                    callback_data=f'confirm-{order_id}')],
            ],
        )
        context.bot.send_message(chat_id=customer_details[-1],
                        text=f'Заявка №{order_id} отмечена выполненной '\
                                f'пользователем @{current_user}. '\
                                f'Нажмите "Подтвердить!" для закрытия заявки.\n'\
                                f'Перейти в меню - /menu',
                        reply_markup=inline_buttons,)


@debug_requests
def confirmed_orders_handler(update: Update, context: CallbackContext):
    current_user = update.callback_query.message.chat.username
    order_id = update.callback_query.data.split('-')[1]
    current_order = post_sql_query(f'SELECT * FROM ORDERS WHERE order_id ='\
                                f' "{order_id}";')[0]
    post_sql_query(f'UPDATE ORDERS SET status = "Выполнен" '\
                    f'WHERE order_id = "{order_id}";')
    if current_user != current_order[1]:
        carrier_details = post_sql_query(f'SELECT * FROM USERS WHERE username ='\
                                    f' "{current_order[9]}";')[0]
        context.bot.send_message(chat_id=carrier_details[-1],
                text=f'Заявка №{order_id} закрыта пользователем @{current_user}')
    update.callback_query.message.reply_text(
        text='Заявка закрыта.'
    )
