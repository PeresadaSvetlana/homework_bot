import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='program.log',
    filemode='w'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.info(
            f'Сообщение отправлено: {message}')
    except Exception as error:
        logger.error(
            f'Сообщение не отправлено: {error}')


def get_api_answer(current_timestamp):
    """Выполняет запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        logger.error(f'Ошибка при запросе к API: {error}')
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            error_message = 'Статус страницы не равен 200'
            logger.error(error_message)
            raise Exception(error_message)
        return homework_statuses.json()


def check_response(response):
    """Проверяет полученный ответ на корректность."""
    homeworks_response = response['homeworks']
    logger.info('Список домашних работ получен')
    if not homeworks_response:
        message = logger.error('Отсутствует статус homeworks')
        raise Exception(message)
    if not isinstance(homeworks_response, list):
        message_error = logger.error('Невернй тип входящих данных')
        raise Exception(message_error)
    return homeworks_response


def parse_status(homework):
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    if homework_status not in HOMEWORK_STATUSES.keys():
        logger.error('Такого статуса не существует')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных."""
    if (
        PRACTICUM_TOKEN
        and TELEGRAM_TOKEN
        and TELEGRAM_CHAT_ID is not None
    ):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        exit()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework is not None:
                message = parse_status(homework)
                if homework is not None:
                    message = parse_status(bot, homework[0])
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            time.sleep(RETRY_TIME)
        else:
            logger.error('Сбой, ошибка не найдена')


if __name__ == '__main__':
    main()
