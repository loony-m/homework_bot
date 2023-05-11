# Telegram бот

## Описание
Telegram-бот, проверка статуса домашней работы в сервисе Яндекс.Домашка

Стек: работа с внешним REST API, python-telegram-bot, логирование, exceptions

## Как запустить проект

1. Kлонируем репозиторий
```
git clone 
```

2. Установим и активируем виртуальное окружение
```
python3 -m venv venv
```
```
. venv/bin/activate
```

3. Установим зависимости
```
pip install -r requirements.txt
```

4. Запустим бот для демонстрации 
```
python homework.py
```

## Дополнительная информация

Пример .env
```
TELEGRAM_TOKEN={ваш токен бота}
PRACTICUM_TOKEN={токен для Яндекс.Домашка}
TELEGRAM_CHAT_ID={id вашего чата с ботом}
```
