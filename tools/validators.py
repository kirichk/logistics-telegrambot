from typing import Optional
import functools
import random
import time
import os

import sentry_sdk


USER_MAP = {
    'role-1': 'Перевозчик',
    'role-2': 'Диспетчер',
    'role-3': 'Отправитель',
}

OWNERSHIP_MAP = {
    'owner-1': 'Юр. Лицо',
    'owner-2': 'Физ. Лицо',
    'owner-3': 'ФОП',
}

PAYMENT_MAP = {
    'payment-1': 'Наличный',
    'payment-2': 'Безналичный',
    'payment-3': '3-я группа без НДС'
}


def gender_hru(gender: int) -> Optional[str]:
    return GENDER_MAP.get(gender)


def validate_id(text: str) -> Optional[int]:
    try:
        id = int(text)
    except (TypeError, ValueError):
        return None
    return id


def validate_float(text: str) -> Optional[float]:
    try:
        price = float((text.replace(',', '.')).replace(' ',''))
    except (TypeError, ValueError):
        return None
    return price


def validate_chosed_weight(text: str, num: float) -> Optional[float]:
    try:
        weight = float((text.replace(',', '.')).replace(' ',''))
        if weight <= num:
            return weight
        else:
            return None
    except (TypeError, ValueError):
        return None


def logger_factory(logger):
    """ Импорт функции происходит раньше чем загрузка конфига логирования.
        Поэтому нужно явно указать в какой логгер мы хотим записывать.
    """
    def debug_requests(f):

        @functools.wraps(f)
        def inner(*args, **kwargs):

            try:
                logger.debug('Обращение в функцию `{}`'.format(f.__name__))
                return f(*args, **kwargs)
            except Exception as e:
                logger.exception('Ошибка в функции `{}`'.format(f.__name__))
                sentry_sdk.capture_exception(error=e)
                raise

        return inner

    return debug_requests
