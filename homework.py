import logging
import os
import time
import requests
import telegram

from datetime import datetime, timedelta
from dotenv import load_dotenv
from exceptions import (CheckAvailiableConstant,
                        EmptyHomework,
                        ResponseNot200Status,
                        ServiceError)

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, [%(levelname)s], %(message)s'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PERIOD_DAY = 30

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    fields = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }

    for name, value in fields.items():
        if value is None:
            message = ('Отсутствует обязательная переменная окружения: ',
                       name)
            logging.critical(message)
            raise CheckAvailiableConstant(message)


def send_message(bot, message):
    """Отправим сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Удачная отправка сообщения в Telegram')
    except Exception:
        logging.error('Сбой при отправке сообщения в Telegram')


def get_api_answer(timestamp):
    """Отправляем запрос к эндпоинту."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception:
        raise ServiceError('Сервис недоступен')

    if response.status_code != 200:
        raise ResponseNot200Status('Код ответа API домашки отличный от 200')

    response = response.json()

    return response


def check_response(response):
    """Проверяем наличие ключей и проектов."""
    if not isinstance(response, dict):
        message = 'Тип данных ответа должен быть словарь'
        logging.error(message)
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'В ответе отсутствует ключ homeworks'
        logging.error(message)
        raise KeyError(message)

    if not isinstance(response['homeworks'], list):
        message = 'Тип данных homeworks должен быть список'
        logging.error(message)
        raise TypeError(message)

    if not response['homeworks']:
        message = 'За текущий период отсутствуют проекты'
        logging.error(message)
        raise EmptyHomework(message)


def parse_status(homework):
    """Формируем сообщение для телеграмм."""
    work_status = homework['status']

    try:
        homework_name = homework['homework_name']
    except KeyError:
        raise KeyError('Отсутствует ключ homework_name')

    try:
        verdict = HOMEWORK_VERDICTS[work_status]
    except KeyError:
        raise KeyError(f'Неизвестный статус - {work_status}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    from_date = int((datetime.now() - timedelta(days=PERIOD_DAY)).timestamp())
    response_cache = {
        'homeworks': '',
        'current_date': 0,
    }

    while True:
        try:
            # Если уже есть дата последнего запроса.
            from_date_from_cache = response_cache.get('current_date')
            if int(from_date_from_cache) > 0:
                from_date = from_date_from_cache

            can_send = False

            # Отправляем запрос, проверяет ответ.
            response = get_api_answer(from_date)
            check_response(response)

            # Проверяем изменился ли статус.
            homeworks_from_cache = response_cache.get('homeworks')

            if len(homeworks_from_cache) > 0:
                status_from_cache = response_cache.get('homeworks')['status']
                status_from_response = response.get('homeworks')[0]['status']

                if status_from_cache != status_from_response:
                    can_send = True
                    message = parse_status(response_cache.get('homeworks'))
            else:
                can_send = True
                message = parse_status(response.get('homeworks')[0])

            if can_send:
                send_message(bot, message)

            # Запоминаем ответ.
            response_cache['current_date'] = response.get('current_date')
            response_cache['homeworks'] = response.get('homeworks')[0]

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.debug(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
